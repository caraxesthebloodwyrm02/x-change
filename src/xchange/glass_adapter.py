from __future__ import annotations

from typing import Any

from xchange.grid_substantiation import normalize_grid_substantiation_evidence


class PluginManifestError(Exception):
    """Raised when a plugin manifest fails structural validation."""

    def __init__(self, reason: str, field: str | None = None) -> None:
        self.reason = reason
        self.field = field
        super().__init__(reason)


def validate_plugin_manifest(manifest: dict[str, Any]) -> None:
    """Validate a plugin.json manifest before accepting it as evidence.

    Pattern derived from claude-plugins-official #1751:
    missing 'skills' path in plugin.json causes silent discovery failures.
    We fail closed here — malformed manifests are rejected with structured
    detail so the caller knows why their evidence was not accepted.
    """
    if not isinstance(manifest, dict):
        raise PluginManifestError("manifest must be an object", field=None)

    if "name" not in manifest or not isinstance(manifest["name"], str):
        raise PluginManifestError("missing required field: name", field="name")

    # claude-plugins-official #1751: plugin.json must declare "skills" path
    skills = manifest.get("skills")
    if skills is None:
        raise PluginManifestError(
            "missing required field: skills (plugin.json must declare a skills path)",
            field="skills",
        )
    if not isinstance(skills, (str, list)):
        raise PluginManifestError(
            "skills must be a string path or list of paths", field="skills"
        )

    # Optional: validate version string if present
    version = manifest.get("version")
    if version is not None and not isinstance(version, str):
        raise PluginManifestError("version must be a string", field="version")


def map_glass_bridge_to_ingest(
    bridge: dict[str, Any],
    *,
    student_id: str,
    reward_id: str | None = None,
    contract_satisfied: bool = False,
    ready_for_payment: bool = False,
    student_ack: bool = False,
    request_review: bool = False,
    failure: dict[str, Any] | None = None,
    grid_substantiation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    session_id = bridge.get("session_id")
    if not session_id:
        raise ValueError("bridge must contain session_id")
    if not student_id or not isinstance(student_id, str):
        raise ValueError("student_id must be a non-empty string")
    if reward_id is not None and (not reward_id or not isinstance(reward_id, str)):
        raise ValueError("reward_id must be a non-empty string when provided")

    result: dict[str, Any] = {
        "session_id": str(session_id),
        "student_id": student_id,
        "_glass_bridge": bridge,
    }
    if reward_id:
        result["reward_id"] = reward_id
    if contract_satisfied:
        result["contract_satisfied"] = True
    if ready_for_payment:
        result["ready_for_payment"] = True
    if student_ack:
        result["student_ack"] = True
    if request_review:
        result["request_review"] = True
    if failure is not None:
        result["failure"] = failure
    if grid_substantiation is not None:
        result["_grid_substantiation"] = normalize_grid_substantiation_evidence(
            grid_substantiation
        )
    return result
