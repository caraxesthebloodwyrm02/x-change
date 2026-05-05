# Stripe integration boundary: x-change vs GRID

This document defines which system handles which Stripe events, how metadata namespaces are separated, and what guardrails are needed if both systems share a Stripe account.

---

## Routing table

| Event type | Handled by | Endpoint | Action |
|------------|-----------|----------|--------|
| `payment_intent.succeeded` (with `metadata.reward_id` + `metadata.student_id`) | **x-change** | `POST /v0/stripe/webhook` | Reward state → `payment_confirmed` |
| `payment_intent.succeeded` (without x-change metadata) | **x-change** (support signal) | `POST /v0/stripe/webhook` | Logs `stripe_missing_metadata`, returns 200 |
| `checkout.session.completed` | **GRID** | `POST /api/v1/payment/webhook` | Subscription activation |
| `payment_intent.payment_failed` / `canceled` | **GRID** | `POST /api/v1/payment/webhook` | Transaction failure handling |
| `customer.subscription.*` | **GRID** | `POST /api/v1/payment/webhook` | Subscription lifecycle |
| `invoice.paid` / `payment_failed` | **GRID** | `POST /api/v1/payment/webhook` | Usage billing |
| All other event types | Neither | — | Ignored |

x-change ignores all event types except `payment_intent.succeeded`.

---

## Metadata namespace

**x-change reserves** these keys on `PaymentIntent.metadata`:
- `reward_id` — links payment to a reward ledger row
- `student_id` — links payment to the student who earned the reward

**GRID uses** Stripe Customer IDs, Subscription IDs, and usage record quantities. GRID does not use `reward_id` or `student_id` in PaymentIntent metadata.

**Rule:** Any PaymentIntent created for x-change reward delivery MUST include both `metadata.reward_id` and `metadata.student_id`. Absence triggers a `stripe_missing_metadata` support signal (fail closed, HTTP 200 to prevent Stripe retry storms).

---

## Endpoint routing recommendation

Configure **separate webhook endpoints** in the Stripe dashboard:

| System | Webhook URL | Events to subscribe |
|--------|-------------|---------------------|
| x-change | `https://<xchange-host>/v0/stripe/webhook` | `payment_intent.succeeded` only |
| GRID | `https://<grid-host>/api/v1/payment/webhook` | `payment_intent.*`, `checkout.session.completed`, `customer.subscription.*`, `invoice.*` |

Each endpoint gets its own **endpoint-specific signing secret** from Stripe. Do not share a single `whsec_` across both systems.

If both systems must share a single Stripe account, this separation at the webhook level is mandatory. Code-level event routing (a single proxy that fans out) is not recommended — it adds a failure point and complicates signature verification.

---

## SDK vs raw HMAC rationale

| System | Approach | Why |
|--------|----------|-----|
| **GRID** | Official `stripe` Python SDK via `StripeGateway` | GRID handles complex subscription lifecycle, usage metering, customer management. SDK type safety and multi-provider abstraction (bKash legacy) justify the dependency. |
| **x-change** | Raw HMAC-SHA256 in `stripe_sig.py` | x-change has a zero-external-deps constraint. It handles exactly one event type (`payment_intent.succeeded`). Custom HMAC is ~75 lines, explicit, and sufficient. |

Both approaches validate `Stripe-Signature` headers. Both check timestamp tolerance (configurable). The SDK approach is opaque but maintained by Stripe; the raw approach is explicit but requires manual maintenance if Stripe changes their signing scheme.

---

## Failure mode matrix (x-change)

| Scenario | Behavior | HTTP status | Code reference |
|----------|----------|-------------|----------------|
| Missing `reward_id` or `student_id` in metadata | Accept, create `stripe_missing_metadata` signal | 200 | `main.py` `_handle_stripe_webhook` |
| `reward_id` not found in ledger | Accept, create `stripe_reward_missing` signal | 200 | `storage.py` `process_stripe_payment_intent_succeeded` |
| `student_id` doesn't match reward's student | Accept, create `stripe_student_mismatch` signal | 200 | `storage.py` `process_stripe_payment_intent_succeeded` |
| Duplicate `stripe_event_id` | Idempotent return, no state change | 200 | `storage.py` UNIQUE on `payment_confirmations.stripe_event_id` |
| Invalid `Stripe-Signature` | Reject | 401 | `main.py` `_handle_stripe_webhook` |

All failure modes return 200 except invalid signature. This is intentional: returning non-200 to Stripe causes retries, which would repeatedly create support signals for the same unresolvable issue.

---

## Hardening notes (future work)

These gaps are documented for future hardening, not current blockers:

1. **Livemode validation.** GRID checks `event["livemode"]` against expected environment. x-change does not. A Stripe test-mode event sent to a production x-change instance would be processed as real, potentially corrupting reward state. Fix: check `event.livemode` against an `XCHANGE_LIVE_MODE` env var.

2. **Webhook-level deduplication.** GRID tracks webhook events by `gateway_event_id` and marks them PROCESSED/IGNORED. x-change deduplicates only at the payment confirmation level (`stripe_event_id` UNIQUE on `payment_confirmations`). If a webhook arrives for a reward that isn't in `payment_pending` state, the event is processed (creating a support signal) every time Stripe retries. Fix: add a `webhook_events` table to track all received event IDs regardless of processing outcome.

3. **Metadata `system` tag.** If both systems share a Stripe account, adding `metadata.system = "xchange"` or `"grid"` to all PaymentIntents would allow either webhook handler to quickly ignore events meant for the other system, before any database work.
