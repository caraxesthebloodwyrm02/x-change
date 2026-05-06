# Complement matrix — x-change vs installed FSI assets

**Date:** 2026-05-07
**Inputs:** [`x-change-audit.md`](x-change-audit.md), [`fsi-marketplace-audit.md`](fsi-marketplace-audit.md).

**Legend — complement type**

- **Fill** — Asset improves a documented x-change gap with low metaphorical stretch.
- **Adjacent** — Useful only after glue (MCP, export pipeline, or explicit operator procedure).
- **Misfit** — Different problem domain or conflicts with constraints (zero deps, policy choke).
- **Activation cost:** Low / Medium / High.

---

## Matrix

| x-change surface / gap | FSI asset(s) | Type | Activation | Notes |
|--------------------------|--------------|------|------------|-------|
| Exception queue (`support_signals`) + human `resolve` | **gl-reconciler** agent, `break-trace`, `gl-recon` skills | Adjacent | **High** (agent expects `mcp__internal-gl__*`, `mcp__subledger__*`) | **Workflow homology** (break list → trace → sign-off) is strong; **data** is not GL/subledger. |
| Period summary for operator (“close pack” narrative) | **month-end-closer** agent, `variance-commentary`, `roll-forward` | Adjacent | **High** (same MCP gap) | Could inspire **Markdown** monthly report from `GET /v0/outcomes/summary` + payment export — not accrual schedules. |
| Read-only governance / no silent posting | Both agents’ **guardrail** sections in `agents/*.md` | Fill | **Low** | **Process documentation** alignment only; no code. |
| Market / Excel modeling | **financial-analysis** commands + skills (`dcf-model`, `comps-analysis`, …) | Misfit | N/A | x-change is not a valuation or spreadsheet product; **plugin also fails to load**. |
| Vendor market data | `.mcp.json` (Daloopa, FactSet, LSEG, …) | Misfit | N/A | No intersection with SQLite reward ledgers. |
| Excel audit of *exported* reward/payment CSV | `audit-xls` (bundled in all three plugins) | Adjacent | **Medium** | Requires **export step** from SQLite or HTTP; skill targets financial models, not x-change schema — usable with discipline. |
| Headless workbook artifact | `xlsx-author` skills | Adjacent | **Medium** | Same as above; optional reporting layer outside core server. |
| MCP as integration layer ([`finance-agents-modernization.md`](../finance-agents-modernization.md)) | FSI agents’ MCP tool prefixes | Adjacent | **High** until x-change exposes MCP | Confirms **same integration primitive** (MCP) as FSI; x-change has HTTP only today. |
| Glass evidence-only bridge | (none in FSI bundle) | Misfit | N/A | FSI does not address spatial session telemetry; x-change + Glass already defined in [`glass-contract-v0.md`](../glass-contract-v0.md). |
| Stripe HMAC + idempotency | (none in FSI bundle) | Misfit | N/A | Correctly out of scope for marketplace verticals. |
| Policy tests + domain purity | `skill-creator` (financial-analysis disk) | Adjacent | **Low** | Generic skill authoring; **financial-analysis not loaded**. |
| Epistemic tokens / exchange / scope APIs | (none) | Misfit | N/A | No FSI asset maps to `RewardToken` / `GET /v0/scope/*`. |

---

## Narrow scopes that complement (honest shortlist)

1. **Exception narrative template** — Reuse **section headings** from gl-reconciler (break list → root cause → recommended resolution **for human approval**) when writing runbooks for `support_signals` kinds in `docs/`. **Fill** at doc level only.

2. **Monthly operator digest** — Use month-end-closer’s **“close package”** idea as a **checklist shape** for: outcomes summary + open signals + count of `payment_confirmations` by status (from SQL or future read API). **Adjacent**; data from x-change.

3. **skill-creator** — If financial-analysis is repaired, **skill-creator** may help author **x-change-native** `.claude/skills` for triage; not a runtime dependency of the server.

---

## Anti-patterns (do not force)

- Mapping `reward_ledger.state` to “GL accounts” or `payment_confirmations` to “subledger” **without** a documented metaphor — creates wrong mental model for support staff.
- Enabling vendor MCP URLs “because they ship with the plugin” — no reward data there.
- Inferring `contract_satisfied` from Glass `threshold_state` — **violates** [`glass-contract-v0.md`](../glass-contract-v0.md); no FSI asset overrides that.

---

## See also

- [`combo-trial-record.md`](combo-trial-record.md) — Scored trial and PATHS.
