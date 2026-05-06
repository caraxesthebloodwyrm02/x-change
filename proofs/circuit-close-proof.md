# Circuit Close — Gate 2 Proof Artifact

Generated: 2026-05-06T05:59:54.048847+00:00

## Reward State

| Field | Value |
|-------|-------|
| reward_id | `reward-circuit-close-001` |
| student_id | `prince` |
| contract_id | `psc-circuit-close-001` |
| state | **earned** |
| reward_token_amount | 1 |
| outcome_state | unknown |
| updated_at | 2026-05-06T05:59:53.998908+00:00 |

## Transition Log

- **2026-05-06T05:59:53.998903+00:00**: contract_satisfied: drafted -> earned

## Evidence Trail

| # | Type | Provenance | Session | Ingested | Attested | Bridge Timestamp |
|---|------|-----------|---------|----------|----------|-----------------|
| 1 | glass_session_event | glass_ingest | `circuit-close-20260506T0559-383e53fa` | 2026-05-06T05:59:53.935333+00:00 | no | 2026-05-06T05:59:30.960338+00:00 |
| 2 | glass_session_event | glass_ingest | `circuit-close-20260506T0559-383e53fa` | 2026-05-06T05:59:53.997929+00:00 | yes | 2026-05-06T05:59:30.960338+00:00 |

## Bridge Signals (from evidence)

- Evidence #1: {"git_diff_lines": 350, "iteration_count": 12, "session_age_minutes": 45}
- Evidence #2: {"git_diff_lines": 350, "iteration_count": 12, "session_age_minutes": 45}

## Outcomes Summary

- Total rewards: 1
- earned: 1

## Verification Checklist

- [x] Live evidence (non-demo session)
- [x] No staleness bypass
- [x] Policy transition occurred (drafted -> earned)
- Transition reason: contract_satisfied: drafted -> earned

---
*This artifact was generated from x-change API endpoints. Credentials redacted.*
