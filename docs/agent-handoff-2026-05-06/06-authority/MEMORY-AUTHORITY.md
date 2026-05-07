# Memory Authority

## Objective

Make persistent context carryover real by defining memory sources, stale-context rules, session handoff expectations, and a working reference implementation.

## Canonical Sources

| Source | Status | Purpose |
|---|---|---|
| `/home/irfankabir/.codex/memories` | active | Codex memory, rollout summaries, prior decisions. |
| `/home/irfankabir/.claude/knowledge` | active candidate | Knowledge scripts, decisions, state files. |
| `/mnt/arch_data/home/caraxes/.claude/knowledge` | preserved candidate | Mirrored or historical knowledge assets. |
| `/home/irfankabir/.claude/memory` | active candidate | Human-readable memory notes and operational references. |
| `/home/irfankabir/PROJECT_REGISTRY.yaml` | workspace authority | Project provenance and registry source. |
| `x-change/session_memory` (SQLite) | active — reference impl | Project-scoped session handoff table; ingest/retrieve with freshness metadata. |

## Known Gaps

- No operational `.rag_db` was found at the expected locations during the audit.
- Some scheduler or knowledge-loop paths may still reference stale `/home/caraxes` paths.
- Multiple memory systems exist without a single retrieval contract.

## Staleness Policy

Context is classified by age and source freshness:

| Band | Threshold | Action |
|---|---|---|
| **Fresh** | < 24 h since creation | Trust directly; cite source path. |
| **Lingering** | 24 h – 7 d | Trust but re-verify source path exists before acting. |
| **Stale** | > 7 d | Flag as stale; do not act without explicit re-validation of the source. |
| **Unverifiable** | Source path missing | Mark stale immediately; treat as historical reference only. |

Staleness is checked at retrieval time via `stale_checked_at`. Memory entries with `is_stale=1` are excluded from retrieval by default (`include_stale=False`).

## Ingestion Policy

**Store:**
- Non-secret cross-session facts: project paths, active branches, open decisions, blocker states, contract versions, environment variable names (not values).
- Batch execution state: which batch ran, what passed/failed, next recommended batch.
- Session handoff records: changed files, validation results, blockers, stale assumptions.

**Do NOT store:**
- Secret values, credentials, tokens, API keys, OAuth state.
- Raw event payloads (use `evidence_ledger` for those).
- Transient runtime state (process IDs, port numbers, current temperature readings).
- Large blobs (> 4 KB per entry) — store a pointer to the source file instead.

## Session Protocol

| Phase | Required Behavior |
|---|---|
| Start | Read handoff entrypoint, workspace rules, selected batch, and relevant memory sources. |
| During work | Verify memory-derived paths before acting. Mark stale facts when live state differs. |
| End | Record changed files, validation, blockers, next batch, and stale assumptions. |

## Retrieval Validation

A memory implementation passes when **all five** conditions hold:

1. Ingest a new non-secret note with `memory_key`, `memory_value`, `source_path`, and `scope`.
2. Retrieve that note by `memory_key` and `scope`.
3. Every retrieved row includes `source_path` and `created_at` (freshness metadata).
4. Stale entries (source path missing or > 7 d) are excluded from retrieval by default.
5. `mark_stale_memory()` flags entries and updates `stale_checked_at`.

## Reference Implementation

`src/xchange/storage.py` provides a `session_memory` SQLite table with four functions:

- `store_session_memory()` — INSERT with `memory_key`, `memory_value`, `source_path`, `scope`, `session_id`
- `retrieve_session_memory()` — SELECT with optional filters for `memory_key`, `scope`; skips stale rows by default
- `mark_stale_memory()` — UPDATE `is_stale=1`, `stale_checked_at` on a single row by `memory_id` or `memory_key`
- `get_memory_freshness_report()` — count of fresh vs. stale entries by scope

Validation script: `scripts/validate_memory_authority.py` — end-to-end proof of all five retrieval conditions.

## Next Implementation Action

The reference implementation satisfies the completion gate. Future work: federate x-change `session_memory` with global `personal-rag` via `query_federated`, so cross-project context carryover doesn't require a separate ChromaDB deployment per project.
