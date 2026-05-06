# USEB — agent brief (constitutional)

Use this as a short system-prompt block; full detail lives in linked docs.

## Names

- HTTP JSON body: **`grid_substantiation`**
- Persisted on evidence row: **`_grid_substantiation`** (normalized whitelist)
- Glass snapshot in payload: **`_glass_bridge`**

## Endpoint

`POST /v0/ingest/glass-bridge`

Auth: `Authorization: Bearer <XCHANGE_INGEST_TOKEN>` or `X-Ingest-Token: <token>`.

## Non-goals (do not infer)

- Glass `agent_state`, `threshold_state`, `progress`, or `signals` do **not** imply `contract_satisfied`, payment, or acknowledgement.
- `_grid_substantiation` (PATH score, verdict tier, dimensions, fingerprints) does **not** imply any reward transition; `FAST_CLEAR` and `URGENT` are evidence only until the caller sets explicit top-level booleans.

## Before editing `domain.py`

`next_state_after_glass_evidence` **must** ignore `_glass_bridge` and `_grid_substantiation`; only explicit ingest booleans (`contract_satisfied`, `ready_for_payment`, `request_review`, `student_ack`) drive proposals. Re-read the docstring there before changing transition logic.

## Evidence semantics

Successful posts **append** ledger rows. No dedupe on `bundle_hash`.

## Pointers

- Contract (request/response, errors): [`docs/useb-api-contract.md`](useb-api-contract.md)
- Operator scripts and local flow: [`docs/useb-runbook.md`](useb-runbook.md)
- Policy table: [`docs/policy-core-v0.md`](policy-core-v0.md)
