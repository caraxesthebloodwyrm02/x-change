# Circuit Close — Proof Artifact

Generated: 2026-05-06T06:49:24.971419+00:00

## Trust Signal

**Lifecycle stage:** `EARNED` — Evidence satisfies the service contract; awaiting payment.
**Last transition:** contract_satisfied: drafted -> earned
**Transition time:** 2026-05-06T05:59:53.998903+00:00
**Evidence on record:** 2 items

## Reward Details

| Field | Value |
|-------|-------|
| Reward ID | `reward-circuit-close-001` |
| Recipient | `prince` |
| Service contract | `psc-circuit-close-001` |
| Token amount | 1 |
| Delivery outcome | No outcome determined yet. |
| Last updated | 2026-05-06T05:59:53.998908+00:00 |

## Transition History

- **2026-05-06T05:59:53.998903+00:00** — contract_satisfied: drafted -> earned

## Evidence Trail

| # | Kind | Source | Session | Recorded at | Attestation | Bridge captured at |
|---|------|--------|---------|-------------|-------------|-------------------|
| 1 | glass session event | glass ingest | `circuit-close-20260506T0559-383e53fa` | 2026-05-06T05:59:53.935333+00:00 | evidence only | 2026-05-06T05:59:30.960338+00:00 |
| 2 | glass session event | glass ingest | `circuit-close-20260506T0559-383e53fa` | 2026-05-06T05:59:53.997929+00:00 | `ATTESTED` | 2026-05-06T05:59:30.960338+00:00 |

## Work Signals

Captured from the Glass bridge at ingest time.

- Evidence #1: git diff lines: 350, iteration count: 12, session age minutes: 45
- Evidence #2: git diff lines: 350, iteration count: 12, session age minutes: 45

## Reward Distribution

Total rewards: 1

- `EARNED`: 1

## Verification Checklist

- [x] Live evidence (non-demo session)
- [x] No staleness bypass (default 6h freshness gate)
- [x] Policy transition occurred
- Transition reason: contract_satisfied: drafted -> earned

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
