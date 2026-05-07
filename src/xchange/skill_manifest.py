"""Skill manifest domain mapper for x-change v0.

Parses `coordinator.domains` frontmatter from skill YAML/MD files and maps
 declarative skill domains to x-change InsightTier and ToolScope.

Pure logic — no file I/O. Callers read files and pass content as strings.
Pattern derived from skills #1091: coordinator.domains frontmatter for
spec-coordinator tag-routing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

try:
    from domain import InsightTier, ToolScope, EvidenceType, ToolProvenance
except ImportError:
    from xchange.domain import InsightTier, ToolScope, EvidenceType, ToolProvenance


# Domain → InsightTier mapping (heuristic, extensible)
_DOMAIN_TIER_MAP: dict[str, InsightTier] = {
    "math": InsightTier.STRUCTURAL,
    "coding": InsightTier.CAUSAL,
    "reasoning": InsightTier.THEORETICAL,
    "analysis": InsightTier.PATTERN,
    "review": InsightTier.PATTERN,
    "document": InsightTier.SURFACE,
    "knowledge": InsightTier.SURFACE,
    "search": InsightTier.SURFACE,
    "orchestration": InsightTier.STRUCTURAL,
    "security": InsightTier.CAUSAL,
    "finance": InsightTier.STRUCTURAL,
    "agent": InsightTier.STRUCTURAL,
}

# Domain → ToolProvenance mapping (heuristic, extensible)
_DOMAIN_PROVENANCE_MAP: dict[str, str] = {
    "math": ToolProvenance.CALCULATOR,
    "coding": ToolProvenance.AGENT_INTERP,
    "reasoning": ToolProvenance.GRID_SUBSTANTIATION,
    "analysis": ToolProvenance.AGENT_INTERP,
    "review": ToolProvenance.AGENT_INTERP,
    "document": ToolProvenance.GLASS_INGEST,
    "knowledge": ToolProvenance.GLASS_INGEST,
    "search": ToolProvenance.GLASS_INGEST,
    "orchestration": ToolProvenance.GRID_SUBSTANTIATION,
    "security": ToolProvenance.FAIL_SNAPSHOT,
    "finance": ToolProvenance.CALCULATOR,
    "agent": ToolProvenance.AGENT_INTERP,
}


@dataclass(frozen=True)
class SkillDomain:
    """A single domain tag from a skill manifest."""

    name: str
    confidence: float  # 0.0–1.0, derived from position/order in manifest


@dataclass(frozen=True)
class MappedSkill:
    """Result of mapping a skill manifest to x-change policy objects."""

    skill_name: str
    domains: tuple[SkillDomain, ...]
    insight_tier: InsightTier
    tool_scope: ToolScope | None
    rationale: str


def _parse_yaml_dict(text: str) -> dict[str, Any]:
    """Minimal YAML dict parser for frontmatter — no external deps.

    Handles the coordinator.domains pattern specifically:
      coordinator:
        domains:
          - math
          - reasoning
    """
    lines = text.splitlines()
    result: dict[str, Any] = {}
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line or line.strip().startswith("#"):
            i += 1
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)

        if ":" in stripped and not stripped.startswith("- "):
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()

            if value:
                # Simple key: value
                result[key] = value
                i += 1
                continue

            # key: (no value) → look ahead for nested structure
            nested: dict[str, Any] = {}
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                next_stripped = next_line.lstrip()
                if not next_stripped or next_stripped.startswith("#"):
                    j += 1
                    continue
                next_indent = len(next_line) - len(next_stripped)
                if next_indent <= indent:
                    break

                if next_stripped.startswith("- "):
                    # list items under this key
                    if key not in result:
                        result[key] = []
                    if not isinstance(result[key], list):
                        result[key] = []
                    result[key].append(next_stripped[2:].strip())
                elif ":" in next_stripped and not next_stripped.startswith("- "):
                    # nested dict key
                    sub_key, _, sub_value = next_stripped.partition(":")
                    sub_key = sub_key.strip()
                    sub_value = sub_value.strip()
                    if sub_value:
                        nested[sub_key] = sub_value
                    else:
                        # Look ahead for list under sub_key
                        sub_list: list[str] = []
                        k = j + 1
                        while k < len(lines):
                            sub_next = lines[k]
                            sub_next_stripped = sub_next.lstrip()
                            if not sub_next_stripped or sub_next_stripped.startswith("#"):
                                k += 1
                                continue
                            sub_next_indent = len(sub_next) - len(sub_next_stripped)
                            if sub_next_indent <= next_indent:
                                break
                            if sub_next_stripped.startswith("- "):
                                sub_list.append(sub_next_stripped[2:].strip())
                            k += 1
                        nested[sub_key] = sub_list
                        j = k - 1
                j += 1

            if nested:
                result[key] = nested
            i = j
            continue

        i += 1

    return result


def _extract_frontmatter(text: str) -> dict[str, Any]:
    """Extract YAML frontmatter from a SKILL.md or skill YAML string.

    Supports both `---` delimited YAML frontmatter and inline
    `coordinator.domains:` declarations. Pure stdlib — no PyYAML.
    """
    # Try standard YAML frontmatter
    match = re.search(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if match:
        try:
            return _parse_yaml_dict(match.group(1)) or {}
        except Exception:
            return {}

    # Fallback: look for coordinator.domains inline (line-by-line for robustness)
    for i, line in enumerate(text.splitlines()):
        if line.strip().startswith("coordinator.domains:"):
            tags: list[str] = []
            for next_line in text.splitlines()[i + 1 :]:
                stripped = next_line.strip()
                if not stripped:
                    continue
                if stripped.startswith("- "):
                    tags.append(stripped[2:].strip())
                else:
                    break
            if tags:
                return {"coordinator": {"domains": tags}}
            break

    return {}


def _domains_from_frontmatter(frontmatter: dict[str, Any]) -> list[SkillDomain]:
    """Parse domain tags from extracted frontmatter dict."""
    coordinator = frontmatter.get("coordinator", {})
    if isinstance(coordinator, dict):
        raw = coordinator.get("domains", [])
    else:
        raw = []

    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, (list, tuple)):
        return []

    total = len(raw)
    domains: list[SkillDomain] = []
    for idx, tag in enumerate(raw):
        if not isinstance(tag, str):
            continue
        # Confidence decays linearly with position: first = 1.0, last = 0.5
        confidence = 1.0 - (idx / max(total, 1)) * 0.5
        domains.append(SkillDomain(name=tag.strip().lower(), confidence=round(confidence, 4)))
    return domains


def _map_domains_to_tier(domains: list[SkillDomain]) -> InsightTier:
    """Select the highest-cognitive-demand tier from mapped domains."""
    tier_order = [
        InsightTier.SURFACE,
        InsightTier.PATTERN,
        InsightTier.STRUCTURAL,
        InsightTier.CAUSAL,
        InsightTier.THEORETICAL,
    ]
    best_tier = InsightTier.SURFACE
    best_score = -1.0
    for d in domains:
        tier = _DOMAIN_TIER_MAP.get(d.name, InsightTier.SURFACE)
        score = tier_order.index(tier) + d.confidence
        if score > best_score:
            best_score = score
            best_tier = tier
    return best_tier


def _map_domains_to_tool_scope(
    domains: list[SkillDomain], skill_name: str
) -> ToolScope | None:
    """Build a ToolScope from the highest-confidence domain."""
    if not domains:
        return None
    # Pick highest-confidence domain
    best = max(domains, key=lambda d: d.confidence)
    provenance = _DOMAIN_PROVENANCE_MAP.get(best.name, ToolProvenance.AGENT_INTERP)
    # Evidence type inferred from provenance
    if provenance == ToolProvenance.GLASS_INGEST:
        evidence_type = EvidenceType.GLASS_SESSION_EVENT
    elif provenance in (ToolProvenance.FAIL_SNAPSHOT,):
        evidence_type = EvidenceType.FAILURE_SNAPSHOT
    elif provenance == ToolProvenance.STUDENT_ACK:
        evidence_type = EvidenceType.STUDENT_CONFIRMATION
    else:
        evidence_type = EvidenceType.AGENT_INTERPRETATION

    return ToolScope(
        provenance=provenance,
        evidence_type=evidence_type,
        source_system="grid" if provenance == ToolProvenance.GRID_SUBSTANTIATION else "glass",
        produces_transitions=True,
        payload_keys=("skill_name", "domain", "confidence"),
    )


def map_skill_manifest(
    skill_name: str,
    manifest_text: str,
) -> MappedSkill:
    """Map a skill manifest (SKILL.md or plugin.json skills entry) to x-change policy objects.

    Args:
        skill_name: Canonical skill identifier (e.g. "glass-eval", "skill-creator").
        manifest_text: Raw text of the skill manifest (YAML frontmatter or JSON).

    Returns:
        MappedSkill with inferred InsightTier and ToolScope.
    """
    frontmatter = _extract_frontmatter(manifest_text)
    domains = _domains_from_frontmatter(frontmatter)
    insight_tier = _map_domains_to_tier(domains)
    tool_scope = _map_domains_to_tool_scope(domains, skill_name)

    if domains:
        domain_names = ", ".join(d.name for d in domains)
        rationale = (
            f"Mapped {skill_name} from coordinator.domains [{domain_names}] → "
            f"insight_tier={insight_tier.value}, provenance={tool_scope.provenance if tool_scope else 'none'}"
        )
    else:
        rationale = f"No coordinator.domains found for {skill_name}; defaulted to insight_tier={insight_tier.value}"

    return MappedSkill(
        skill_name=skill_name,
        domains=tuple(domains),
        insight_tier=insight_tier,
        tool_scope=tool_scope,
        rationale=rationale,
    )
