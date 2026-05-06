# Memory Authority

## Objective

Make persistent context carryover real by defining memory sources, stale-context rules, and session handoff expectations.

## Canonical Sources

| Source | Status | Purpose |
|---|---|---|
| `/home/irfankabir/.codex/memories` | active | Codex memory, rollout summaries, prior decisions. |
| `/home/irfankabir/.claude/knowledge` | active candidate | Knowledge scripts, decisions, state files. |
| `/mnt/arch_data/home/caraxes/.claude/knowledge` | preserved candidate | Mirrored or historical knowledge assets. |
| `/home/irfankabir/.claude/memory` | active candidate | Human-readable memory notes and operational references. |
| `/home/irfankabir/PROJECT_REGISTRY.yaml` | workspace authority | Project provenance and registry source. |

## Known Gaps

- No operational `.rag_db` was found at the expected locations during the audit.
- Some scheduler or knowledge-loop paths may still reference stale `/home/caraxes` paths.
- Multiple memory systems exist without a single retrieval contract.

## Session Protocol

| Phase | Required Behavior |
|---|---|
| Start | Read handoff entrypoint, workspace rules, selected batch, and relevant memory sources. |
| During work | Verify memory-derived paths before acting. Mark stale facts when live state differs. |
| End | Record changed files, validation, blockers, next batch, and stale assumptions. |

## Retrieval Validation

A memory implementation passes when:

- it can ingest a new non-secret handoff note
- it can retrieve that note by project and task query
- every retrieval includes source path and freshness
- stale path references are flagged instead of silently trusted

## Next Implementation Action

Create a machine-readable `memory-authority.yaml` from this record, then build a read-only hydration check before any vector-store rebuild.

