# USEB Proof Summary

Unified Session Evidence Bundle v1 adds one auditable evidence package for session close:

- `_glass_bridge`: Glass session reality.
- `_grid_substantiation`: GRID readiness reality.
- Explicit policy booleans: the only inputs that can propose reward transitions.

## Proof Claims

- Bridge-only ingest remains valid.
- Malformed GRID substantiation returns `400`.
- Oversized GRID substantiation returns `400`.
- GRID `FAST_CLEAR` by itself leaves a drafted reward in `drafted`.
- Stale Glass bridge snapshots are rejected by the collector unless `--allow-stale` is explicit.

## Operator Receipt Shape

```json
{
  "ok": true,
  "session_id": "useb-demo-session",
  "evidence_recorded": true,
  "transition": null,
  "bundle_hash": "sha256:..."
}
```

See `docs/useb-runbook.md` for reproduction steps.
