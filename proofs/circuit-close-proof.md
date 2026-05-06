# Circuit Close — Proof Artifact

Generated: 2026-05-07T00:00:00+00:00 (final — scope layer active)

## Trust Signal

**Lifecycle stage:** `ACKNOWLEDGED` — Student confirmed receipt of reward.
**Last transition:** student acknowledged
**Transition time:** 2026-05-06T21:24:23.701974+00:00
**Evidence on record:** 4 items

## Reward Details

| Field | Value |
|-------|-------|
| Reward ID | `reward-circuit-close-001` |
| Recipient | `prince` |
| Service contract | `psc-circuit-close-001` |
| Token amount | 3 |
| Token insight tier | `structural` |
| Token rarity band | `rare` |
| Issuance trigger | `contract_close` |
| Token issued at | 2026-05-06T21:30:03Z |
| Delivery outcome | acknowledged |
| Last updated | 2026-05-06T21:24:23.701984+00:00 |

## Transition History

- **2026-05-06T05:59:53.998903+00:00** — contract_satisfied: drafted -> earned
- **2026-05-06T21:24:04.545575+00:00** — ready_for_payment: earned -> payment_pending
- **2026-05-06T21:24:15.474283+00:00** — payment confirmed via Stripe
- **2026-05-06T21:24:23.701974+00:00** — student acknowledged

## Evidence Trail

| # | Kind | Source | Session | Recorded at | Attestation | Bridge captured at |
|---|------|--------|---------|-------------|-------------|-------------------|
| 1 | glass session event | glass ingest | `circuit-close-20260506T0559-383e53fa` | 2026-05-06T05:59:53.935333+00:00 | evidence only | 2026-05-06T05:59:30.960338+00:00 |
| 2 | glass session event | glass ingest | `circuit-close-20260506T0559-383e53fa` | 2026-05-06T05:59:53.997929+00:00 | `ATTESTED` | 2026-05-06T05:59:30.960338+00:00 |
| 3 | glass session event | glass ingest | `premium-close-20260506T2123-b625e108` | 2026-05-06T21:24:04.543546+00:00 | evidence only | 2026-05-06T21:23:38.494793+00:00 |
| 4 | student confirmation | ack api | `None` | 2026-05-06T21:24:23.688086+00:00 | evidence only | None |

## Work Signals

Captured from the Glass bridge at ingest time.

- Evidence #1: git diff lines: 350, iteration count: 12, session age minutes: 45
- Evidence #2: git diff lines: 350, iteration count: 12, session age minutes: 45
- Evidence #3: git diff lines: 420, iteration count: 18, session age minutes: 62

## Reward Distribution

Total rewards: 1

- `ACKNOWLEDGED`: 1

## Token Scope

| Field | Value |
|-------|-------|
| Insight tier | `structural` |
| Rarity band | `rare` |
| Issuance trigger | `contract_close` |
| Evidence provenance | `glass_ingest` |
| Evidence type | `glass_session_event` |
| Source system | Glass |
| Produces transitions | yes |

## Verification Checklist

- [x] Live evidence (non-demo session)
- [x] No staleness bypass (default 6h freshness gate)
- [x] Policy transition occurred — full 4-step lifecycle: `drafted → earned → payment_pending → payment_confirmed → student_acknowledged`
- [x] Token issued: 3 units, structural tier, rare rarity band
- [x] Scope resolved: glass_ingest provenance, organic emergence confirmed

## Lifecycle Reference

| Stage | Meaning |
|-------|---------|
| `DRAFTED` | Reward created; evidence collection open, not yet earned. |
| `EARNED` | Evidence satisfies the service contract; awaiting payment. |
| `PAYMENT PENDING` | Marked ready for payment; awaiting Stripe confirmation. |
| `PAYMENT CONFIRMED` | Stripe reports successful payment; awaiting student acknowledgement. |
| `ACKNOWLEDGED` | Student confirmed receipt of reward. |
| `REVIEW REQUESTED` | Flagged for manual review (mismatch or escalation). |

---
*Generated from x-change API endpoints. Credentials and code content redacted.*
