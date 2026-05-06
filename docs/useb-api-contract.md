# Unified Session Evidence Bundle API Contract

## Purpose

USEB submits one auditable package at session close:

1. Glass bridge snapshot: session reality.
2. GRID substantiation snapshot: system-readiness reality.
3. Explicit x-change policy booleans: the only fields that can propose reward state transitions.

## Endpoint

`POST /v0/ingest/glass-bridge`

Auth: `Authorization: Bearer <XCHANGE_INGEST_TOKEN>` or `X-Ingest-Token: <token>`.

## Request

```json
{
  "student_id": "stu-1",
  "reward_id": "rwd-1",
  "contract_satisfied": false,
  "ready_for_payment": false,
  "request_review": false,
  "bridge": {
    "timestamp": "2026-05-06T18:00:00+00:00",
    "session_id": "glass-session-1",
    "agent_state": "idle",
    "threshold_state": "ground",
    "progress": 0,
    "blocks": [],
    "conversation": [],
    "voices": [],
    "signals": {
      "git_diff_lines": 0,
      "iteration_count": 1,
      "session_age_minutes": 10
    }
  },
  "grid_substantiation": {
    "version": "v1",
    "captured_at": "2026-05-06T18:00:00+00:00",
    "workspace_roots": ["/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main"],
    "summary": {
      "composite_score": 62.3,
      "verdict_tier": "WATCH",
      "dimensions": {
        "health": 94,
        "trust": 95,
        "drift": 90,
        "fail": 100,
        "momentum": 80
      }
    },
    "repo_fingerprints": [
      {
        "name": "GRID",
        "health_score": 100,
        "branch": "main",
        "last_commit": "20 hours ago",
        "stack": "Python",
        "uncommitted": 0
      }
    ],
    "source": "grid-lumos-orchestrator"
  }
}
```

## Wire vs persisted names

| Location | Field name |
|----------|------------|
| JSON request body | `grid_substantiation` |
| Evidence payload in `evidence_ledger.payload_json` | `_grid_substantiation` (normalized) |

## Invariants

- `student_id` is required.
- `bridge.session_id` is required.
- `grid_substantiation` is optional for backward compatibility.
- If present, `grid_substantiation.version` must be `v1`.
- If present, `grid_substantiation` must include `captured_at`, `source`, `summary.composite_score`, and `summary.verdict_tier`.
- GRID substantiation is whitelisted before persistence. Unknown noisy fields are dropped.
- Serialized GRID substantiation is bounded by `XCHANGE_GRID_SUB_MAX_BYTES` (default 65536).

## `student_ack` (legacy)

For new integrations, prefer `POST /v0/rewards/<reward_id>/acknowledge` instead of sending `student_ack` on ingest. The bridge/session ingest paths may still accept `student_ack` for backward compatibility, but it is deprecated on those routes.

## Evidence semantics

Each successful `POST` **appends** a new evidence row (`glass_session_event`). There is **no** idempotent dedupe: resubmitting the same body (or the same computed `bundle_hash`) creates **another** ledger entry. Operators who need replay protection must enforce it upstream.

## Response

Glass-bridge handler responses extend the base ingest summary with `session_id` and `bundle_hash` (`sha256:` + hex of a stable JSON serialization of receipt fields).

Typical evidence-only submission (no state change):

```json
{
  "ok": true,
  "evidence_recorded": true,
  "session_id": "glass-session-1",
  "bundle_hash": "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
}
```

When explicit policy booleans are accepted by domain rules (e.g. `contract_satisfied` with a `drafted` reward), `transition` is included. GRID and Glass telemetry never create that transition alone.

Example with transition:

```json
{
  "ok": true,
  "evidence_recorded": true,
  "session_id": "glass-session-1",
  "bundle_hash": "sha256:aabbccdd11223344556677889900aabbccdd1122334455667788990011223344",
  "transition": {
    "new_state": "earned",
    "new_outcome": "unknown",
    "notes": ["contract_satisfied: drafted -> earned"]
  }
}
```

`transition.new_state` and `new_outcome` use the RewardModel enums exposed by the server implementation.

## Failure Examples

Malformed GRID evidence:

```json
{
  "error": "grid_substantiation.summary.composite_score must be in [0, 100]"
}
```

Oversized GRID evidence:

```json
{
  "error": "grid_substantiation exceeds size limit: 1520 bytes (max 1024)"
}
```
