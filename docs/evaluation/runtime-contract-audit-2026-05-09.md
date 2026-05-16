# x-change Runtime-vs-Docs Contract Audit (2026-05-09)

## Scope
- Runtime source audited: `/home/irfankabir/finance/x-change/src/xchange/main.py`
- Docs audited:
  - `/home/irfankabir/finance/x-change/README.md`
  - `/home/irfankabir/finance/x-change/AGENTS.md`
  - `/home/irfankabir/finance/x-change/CLAUDE.md`
  - `/home/irfankabir/finance/x-change/docs/evaluation/x-change-audit.md`

## Runtime Surface (observed)
- GET routes: 7
- POST routes: 8
- PATCH routes: 1
- Total handler-level routes: 16

## Findings Ledger

| ID | Severity | Finding | Evidence | Owner | Closure Action |
|---|---|---|---|---|---|
| XC-001 | P1 | `README.md` endpoint list is partial relative to runtime handlers. | Runtime includes `/v0/viewer`, `/v0/exchange/*`, `/v0/scope/*`, `/v0/evidence/<id>` while README lists only primary operational subset. | x-change docs owner | Add a "Full API Surface" section in `README.md` or clearly label current list as "primary flow only". |
| XC-002 | P2 | Endpoint coverage is consistent across `AGENTS.md` and `docs/evaluation/x-change-audit.md`, but split-source docs increase drift risk. | `AGENTS.md` and `x-change-audit.md` both reflect full surface; README does not. | x-change maintainers | Set one canonical API table source and derive other docs from it. |
| XC-003 | P2 | Historical concern about undocumented outbound `anthropic` behavior is not present in runtime source. | No `anthropic` usage found in `/src`; references exist in docs only as marketplace/integration guidance. | x-change maintainers | Close previous runtime-risk flag; keep integration docs but tag as non-runtime dependency. |

## Decision Summary
- Runtime contract is healthy.
- Primary drift is documentation placement/clarity, not handler behavior.
- Highest-value fix is README clarification plus single-source API table policy.
