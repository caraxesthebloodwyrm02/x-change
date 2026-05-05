# x-change policy core v0

**Scope:** Single-student principled service loop — contract → evidence → reward state → Stripe payment confirmation → student outcome. Team payouts, geo withdrawal, and marketplace logic are **out of scope** until this foundation is stable.

**Authoritative architecture:** `PrincipledServiceContract` constrains interpretation; **`RewardModel` is canonical** for financing/reward state; **Glass** supplies **EvidenceLedger** inputs only; **Stripe** supplies **payment confirmation** only (not student acknowledgement).

---

## PrincipledServiceContract (PSC)

Before any reward is interpreted, a service promise must exist that is intelligible to a student and support staff.

A PSC records:

| Field | Meaning |
| --- | --- |
| What may be rewarded | Observable progress or behaviors (v0: declared in contract JSON). |
| Required evidence | Minimum evidence types / signals (v0: glass session + optional failure snapshot). |
| Post-success expectation | What the student should receive after satisfying the contract (v0: narrative in `promise_json`). |
| Stripe linkage | Successful `payment_intent.succeeded` with `metadata.reward_id` + `metadata.student_id` confirms **payment**, not satisfaction. |
| Support path | Mismatch or missing linkage produces **support signals** (fail closed); no silent drops. |
| Fulfillment confirmation | **Student acknowledgement** is separate from Stripe confirmation. |

**Default contract id (v0):** `psc-v0-default` — seeded in storage on first init.

---

## RewardModel

The RewardModel answers: *what* reward, *for whom*, *why*, *with what evidence*, *what delivery proof*, *what acknowledgement state*, and *current lifecycle state*.

### RewardToken (x-change)

`RewardToken` is the **x-change governance unit** for a reward row: an integer `reward_token_amount` on the ledger (v0 scalar). It is **not** imported from signal-rate-limit “tokens” elsewhere in the ecosystem.

### Lifecycle states (v0)

| State | Meaning |
| --- | --- |
| `drafted` | Service may have a reward intention; not yet earned. |
| `earned` | Evidence satisfies the PSC. |
| `payment_pending` | Awaiting Stripe payment confirmation for this reward. |
| `payment_confirmed` | Stripe reports `payment_intent.succeeded` with matching metadata. |
| `student_acknowledged` | Student-facing acknowledgement recorded. |
| `review_requested` | Student or agent flagged mismatch / escalation. |

**Rule:** Only the **policy layer** (application code applying `domain` rules) advances state. Raw evidence rows and raw Stripe JSON **propose** transitions; they do not bypass validation.

### StripePaymentConfirmation

- Primary event type handled: `payment_intent.succeeded`.
- **Idempotency:** `stripe_event_id` is unique; duplicates are acknowledged without double-applying.
- **Link keys:** `metadata.reward_id`, `metadata.student_id`.
- **Missing metadata:** record `support_signals.kind = stripe_missing_metadata`, return HTTP 200 to Stripe (avoid broken retries), **do not** mutate reward state.
- **Mismatch** (unknown reward, wrong student): record support signal, do not apply payment to ledger state.

### EvidenceLedger (v0 types)

| Type | Typical source |
| --- | --- |
| `glass_session_event` | `POST /v0/ingest/glass-session` |
| `failure_snapshot` | Optional `failure` object on same ingest |
| `return_attempt` | Future: explicit retry markers |
| `success_after_support` | Declared progress in ingest payload |
| `agent_interpretation` | Future: agent-attributed summaries |
| `student_confirmation` | Ingest payload acknowledging outcome |

Provenance string examples: `glass_ingest`, `stripe_webhook`, `api_ack`.

### StudentOutcome (v0)

Tracked alongside reward state:

| Outcome field | Meaning |
| --- | --- |
| `outcome_state` | `unknown` → `delivered_pending_ack` → `acknowledged` / `review_open` |
| Notes | Optional JSON notes on last milestone |

Stripe payment confirms **funds movement**, not educational outcome. Student acknowledgement is explicit.

---

## Plain-language service promise (v0 default)

> If your session evidence shows you met the contract (`contract_satisfied`), x-change records **earned**. When the service marks **ready** for disbursement (`ready_for_payment`), the reward moves to **payment_pending**. When Stripe confirms payment to the linked reward and student ids, the row becomes **payment_confirmed**. You may then **acknowledge** receipt or **request review** if something does not match what was promised.

---

## Token reference boundary (ecosystem scaffolds)

Prior “token” work in Cascade is **reference_only** for x-change unless explicitly promoted here.

| Reference | Disposition | Notes |
| --- | --- | --- |
| `Components/shared-types/src/signal-model.ts` | **reject** (canonical) | EQ / signal weights — not financial reward governance. |
| `Components/shared-types/tests/signal-model.test.ts` | **reject** | Test machinery for signal tokens. |
| `canopy/token-type-calculator/` | **defer** | Useful vocabulary for classification; **do not** conflate with `RewardToken`. |

**Default stance:** define `RewardToken` and states from **this** policy, not from signal-type calculators.

---

## Architecture validation gate (pre-broadening checklist)

Apply before adding teams, withdrawals, or dashboards:

1. **Reward transitions** — every transition maps to a named rule in `domain.py`; no ad hoc state writes outside storage helpers.
2. **Stripe idempotency** — `payment_confirmations.stripe_event_id` UNIQUE enforced; replays are safe.
3. **Provenance** — every evidence and payment row stores `provenance` / payload for audit.
4. **Support path** — missing metadata and mismatches emit `support_signals`; never silent discard.
5. **Ack vs pay** — `payment_confirmed` cannot imply `student_acknowledged` without `student_confirmation` evidence or ack API.
6. **Fail closed on ingest** — missing `XCHANGE_INGEST_TOKEN` configuration rejects ingestion (existing behavior).

---

## Deferred (explicitly not v0)

- Team leader approvals, transcript validation, geo-specific withdrawal, multi-currency, marketplace payouts, revenue dashboards.
