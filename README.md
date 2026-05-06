# x-change v0 — Principled reward core

Canonical **policy**: [`docs/policy-core-v0.md`](docs/policy-core-v0.md) — `PrincipledServiceContract`, **`RewardModel`** (center), **EvidenceLedger** (Glass), **StripePaymentConfirmation**, **StudentOutcome**.

## What this does (v0)

1. **`POST /v0/rewards/draft`** (auth) — create a `drafted` reward on the **reward ledger**.
2. **`POST /v0/ingest/glass-session`** (auth) — writes **evidence** (`glass_session_event`, optional `failure_snapshot`) and **proposes** reward transitions (`contract_satisfied`, `ready_for_payment`, `student_ack`, `request_review`).
3. **`POST /v0/ingest/glass-bridge`** (auth) — maps caller-enriched Glass bridge telemetry into the existing Glass session ingest flow without inferring policy state. Also accepts optional USEB `grid_substantiation` evidence.
4. **`POST /v0/rewards/<reward_id>/acknowledge`** (auth) — dedicated student acknowledgement endpoint (replaces inline `student_ack` flag).
5. **`POST /v0/stripe/webhook`** — verifies `Stripe-Signature`, records **`payment_confirmations`** (idempotent on `stripe_event_id`), advances **payment** state when metadata matches an existing reward + student.
6. **`GET /v0/state/reward/<reward_id>`** (auth) — RewardModel-oriented view: ledger state, evidence tail, payment rows, legacy mirror row.
7. **`GET /v0/outcomes/summary`** (auth) — aggregate reward counts by state, total rewards, and distinct student count; optional `student_id` filter.
8. **`GET /v0/support-signals`** (auth) — list support signals with optional `kind` and `resolved` filters.
9. **`POST /v0/support-signals/<id>/resolve`** (auth) — mark a support signal as resolved with resolution note.

**Stripe `payment_intent.succeeded`**: requires `metadata.reward_id` and `metadata.student_id`. **Missing metadata → `support_signals`** + HTTP **200** (fail closed without dropping the event on Stripe retries). Payment confirmed ≠ student acknowledged.

Operator endpoints require `Authorization: Bearer <XCHANGE_INGEST_TOKEN>` or `X-Ingest-Token: <token>` and share an in-process rate limit. The Stripe webhook is signed separately and is not subject to the operator bucket.

## Acceptance / foundation tests

- Reward transitions: drafted → earned → payment_pending → payment_confirmed → student_acknowledged.
- Stripe idempotency on `stripe_event_id`.
- Support signals for missing reward / student mismatch.
- Glass bridge telemetry preserved as evidence without automatic policy inference.
- USEB GRID substantiation preserved as evidence without automatic policy inference.
- Operator read surfaces require ingest-token auth.

Run:

```bash
export PYTHONPATH="$PWD/src"
uv run python -m unittest discover -s tests -v
```

## Run locally

x-change has a `pyproject.toml` and `uv.lock` for reproducible local execution. It remains zero-runtime-dependency Python and has no build step.

```bash
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
export XCHANGE_INGEST_TOKEN="dev-secret"   # required for operator endpoints
export STRIPE_WEBHOOK_SECRET="whsec_..."  # required for Stripe webhook signature verification
export XCHANGE_STRIPE_TOLERANCE_SECONDS="300" # optional

export PYTHONPATH="$PWD/src"
uv run python -m xchange
```

Server defaults: `0.0.0.0:8788`
Rate limit defaults: `XCHANGE_RATE_LIMIT_REQUESTS=60`, `XCHANGE_RATE_LIMIT_WINDOW_SECONDS=60`.

## Ingest hints (JSON)

| Field | Role |
| --- | --- |
| `reward_id` | Associate evidence + transitions with a ledger row. |
| `contract_satisfied` | `drafted` → `earned` |
| `ready_for_payment` | `earned` → `payment_pending` |
| `student_ack` | **DEPRECATED.** Use `POST /v0/rewards/<reward_id>/acknowledge` instead. After `payment_confirmed`, → `student_acknowledged` |
| `request_review` | → `review_requested` |
| `failure` | Optional failure snapshot (evidence + legacy `failures` row). |

## Circuit Close — Proof of Concept (v1)

**Thesis:** A spatial development environment (Glass) generates session evidence that a principled reward service (x-change) processes into auditable, policy-valid state transitions. The builder and the student are the same person. The evidence trail is inspectable by a third party.

**Gate definitions:**

| Gate | Criterion | Status |
|------|-----------|--------|
| 1 — Live Wire | Glass bridge payload ingested into `evidence_ledger` without staleness bypass | Pass |
| 2 — State Advance | Deliberate attestation transitions reward `drafted` -> `earned` with traceable reason | Pass |
| 3 — Visible Surface | Shareable proof artifact verifiable by a non-operator | Pass |

**First real run (2026-05-06):**

- Session: `circuit-close-20260506T0559-383e53fa`
- Bridge freshness: 23 seconds at ingest (no override)
- Transition: `contract_satisfied: drafted -> earned` at `2026-05-06T05:59:53Z`
- Evidence: 2 rows (pre-attestation + attestation), both linked to `reward-circuit-close-001`

**Proof artifacts:** [`proofs/circuit-close-proof.md`](proofs/circuit-close-proof.md) (human narrative) | [`proofs/circuit-close-proof.json`](proofs/circuit-close-proof.json) (machine-verifiable)

**Reproduce in <10 minutes:** see [`docs/circuit-close-runbook.md`](docs/circuit-close-runbook.md)

## Token boundary

x-change **`RewardToken`** is the integer `reward_token_amount` on the ledger — **not** signal/EQ tokens from other Cascade packages; see policy doc **Token reference boundary**.

## USEB

Unified Session Evidence Bundle combines a Glass bridge snapshot with optional GRID substantiation and submits both to `POST /v0/ingest/glass-bridge`. GRID data is stored under `_grid_substantiation` as evidence only; it never drives reward state. See [`docs/useb-api-contract.md`](docs/useb-api-contract.md), [`docs/useb-runbook.md`](docs/useb-runbook.md), and the short prompt-oriented [`docs/useb-agent-brief.md`](docs/useb-agent-brief.md).
