# Glass integration contract v0

**Contract version:** `glass-contract-v0`
**Tied to:** `policy-core-v0`
**Status:** Interface specification. No live integration exists yet.

---

## Purpose

Formalizes the data boundary between Glass (the Canvas2D spatial environment) and x-change (the reward delivery service). Glass sessions are the named evidence source for x-change's `EvidenceLedger`, but the two systems have disjoint schemas today. This contract defines what Glass must provide — and what x-change will never infer.

---

## Glass bridge schema (source)

The Glass bridge file (`~/.caraxes/field-bridge.json`) is written by `glass-server` and contains workspace/agent state:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session identifier (e.g., `demo-20260504T0216-48e398de`) |
| `agent_state` | enum | `idle`, `thinking`, `writing`, `reviewing`, `elevated` |
| `threshold_state` | enum | `ground`, `evaluating`, `floor_rising`, `voices_appearing`, `voice_1_active`, `voice_2_active`, `voice_3_active`, `elevated`, `returning`, `denied` |
| `progress` | float | Ceremony progress 0.0–1.0 |
| `blocks` | array | Code/note/output/asset blocks with position and origin |
| `conversation` | array | `{role, text, timestamp}` entries |
| `voices` | array | Active voice state |
| `signals` | object | `{git_diff_lines, iteration_count, session_age_minutes}` |
| `timestamp` | string | ISO-8601 last-write timestamp |

**Not present in Glass:** `student_id`, `reward_id`, `contract_satisfied`, `ready_for_payment`, `student_ack`, `request_review`.

---

## x-change ingest schema (target)

`POST /v0/ingest/glass-session` expects:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `session_id` | Yes | string | From Glass bridge |
| `student_id` | Yes | string | **Caller-supplied** — not in Glass |
| `reward_id` | No | string | **Caller-supplied** — associates evidence with a ledger row |
| `contract_satisfied` | No | bool | **Caller-supplied** — triggers `drafted` → `earned` |
| `ready_for_payment` | No | bool | **Caller-supplied** — triggers `earned` → `payment_pending` |
| `student_ack` | No | bool | **Deprecated** — use `POST /v0/rewards/<id>/acknowledge` |
| `request_review` | No | bool | **Caller-supplied** — triggers → `review_requested` |
| `failure` | No | object | Optional failure snapshot |

---

## Adapter contract

The adapter (`POST /v0/ingest/glass-bridge`) accepts a Glass bridge payload plus caller-supplied enrichment fields, and maps them to the ingest schema.

### Enrichment fields (required from caller)

| Field | Required | Source | Notes |
|-------|----------|--------|-------|
| `student_id` | Yes | Caller | Glass has no student concept |
| `reward_id` | No | Caller | Links evidence to a reward ledger row |
| `contract_satisfied` | No | Caller | Explicit boolean; never inferred from Glass state |
| `ready_for_payment` | No | Caller | Explicit boolean; never inferred from Glass state |
| `student_ack` | No | Caller | Deprecated; use acknowledge endpoint |
| `request_review` | No | Caller | Explicit boolean; never inferred from Glass state |
| `failure` | No | Caller | Optional failure snapshot object |

### Bridge fields (passed through as evidence)

All Glass bridge fields are stored verbatim in the `evidence_ledger` under the `_glass_bridge` key of the payload. They are recorded for provenance and audit. None of them drive state transitions.

### Design rule: no auto-inference

The adapter MUST NOT infer policy booleans from Glass state. For example:
- `threshold_state=elevated` does NOT imply `contract_satisfied=true`
- `progress=1.0` does NOT imply `ready_for_payment=true`
- `agent_state=reviewing` does NOT imply `request_review=true`

Per `policy-core-v0`: only the policy layer (`domain.py`) advances reward state, and it acts on explicit boolean flags from the caller — never on ambient session telemetry.

---

## Out of scope

- **Automatic threshold-to-policy mapping.** Deferred until the relationship between Glass ceremony outcomes and educational contract satisfaction is formally defined.
- **Glass-side changes.** This contract does not require modifications to `glass-server` or the bridge file format.
- **Bidirectional communication.** x-change does not write back to Glass. The flow is one-directional: Glass → adapter → x-change.
