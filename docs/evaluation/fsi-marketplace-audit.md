# Anthropic Financial Services — installed marketplace audit (this host)

**Audit date:** 2026-05-07
**Marketplace:** `claude-for-financial-services` (source repo `anthropics/financial-services`)
**Install registry:** `~/.claude/plugins/installed_plugins.json` (version 2).

---

## 1. Installed plugins (FSI)

| Plugin | Version | Install path | CLI status (2026-05-07) |
|--------|---------|--------------|-------------------------|
| `financial-analysis@claude-for-financial-services` | 0.1.0 | `.../financial-analysis/0.1.0` | **Failed to load** — `hooks/hooks.json` is JSON array `[]`; Claude Code expects a **hook config object**. Commands/skills exist on disk but plugin does not activate. |
| `gl-reconciler@claude-for-financial-services` | 0.1.0 | `.../gl-reconciler/0.1.0` | **Enabled** |
| `month-end-closer@claude-for-financial-services` | 0.1.0 | `.../month-end-closer/0.1.0` | **Enabled** |

*(Non-FSI plugins present: `rust-analyzer-lsp`, `frontend-design`; out of scope for this audit.)*

---

## 2. financial-analysis (disk inventory)

**Manifest:** `.claude-plugin/plugin.json` — name `financial-analysis`, description: core modeling (DCF, comps, LBO, 3-statement, competitive analysis, deck QC).

### Commands (`commands/*.md`)

| File | Likely slash surface |
|------|----------------------|
| `comps.md`, `dcf.md`, `lbo.md`, `3-statement-model.md`, `debug-model.md`, `competitive-analysis.md`, `ppt-template.md` | IB/ER modeling entry points |

### Skills (`skills/*/SKILL.md`)

Includes: `comps-analysis`, `dcf-model` (+ `scripts/validate_dcf.py`, `requirements.txt`), `lbo-model`, `3-statement-model` (+ references), `competitive-analysis`, `audit-xls`, `clean-data-xls`, `deck-refresh`, `ib-check-deck` (+ `extract_numbers.py`), `pptx-author`, `xlsx-author`, `ppt-template-creator`, `skill-creator` (+ init/package/validate scripts).

### MCP bundle (`.mcp.json`)

Eleven HTTP MCP server stubs: `daloopa`, `morningstar`, `sp-global`, `factset`, `moodys`, `mtnewswire`, `aiera`, `lseg`, `pitchbook`, `chronograph`, `egnyte` — **vendor market / document** connectors, not ledger systems.

### Hooks

`hooks/hooks.json` contains `[]` → **invalid for current Claude Code plugin loader** (reported as `expected object, received array`).

---

## 3. gl-reconciler

**Agent:** `agents/gl-reconciler.md`
- **Role:** GL ↔ subledger reconciliation for a trade date; break list, root-cause trace, exception report for sign-off.
- **Declared tools:** `Read`, `Grep`, `Glob`, `mcp__internal-gl__*`, `mcp__subledger__*`.
- **Guardrails:** Custodian/counterparty statements untrusted; reader workers without MCP; **no ledger posting**; orchestrator never writes; resolver may format only.

**Skills:** `gl-recon`, `break-trace`, `audit-xls`, `xlsx-author` (each `SKILL.md` under `skills/<name>/`).

**Implication for x-change:** No `internal-gl` or `subledger` MCP exists in this workspace; agent **happy path** assumes external systems not present in the x-change repo.

---

## 4. month-end-closer

**Agent:** `agents/month-end-closer.md`
- **Role:** Month-end close checklist — accrual schedule, roll-forwards, variance commentary, close package for controller.
- **Declared tools:** `Read`, `Grep`, `Glob`, `mcp__internal-gl__*`.
- **Guardrails:** Untrusted vendor PDFs; reader isolation; **no GL posting**; JEs staged for approval.

**Skills:** `accrual-schedule`, `roll-forward`, `variance-commentary`, `audit-xls`, `xlsx-author`.

**Overlap with gl-reconciler:** Shared `audit-xls`, `xlsx-author` skill directories (bundled per plugin).

---

## 5. Asset counts (file-level)

| Plugin | Approx. tracked files | Notes |
|--------|----------------------|--------|
| financial-analysis | 40 | Full list in [`fsi-asset-index.json`](fsi-asset-index.json) |
| gl-reconciler | 6 | agent + 4 skills + plugin.json |
| month-end-closer | 8 | agent + 5 skills + plugin.json |

---

## 6. Summary

- **Operational agents** (gl-reconciler, month-end-closer) are **process-strong**, **MCP-dependent** on fictional (for this host) `internal-gl` / `subledger` tool prefixes.
- **financial-analysis** is **asset-rich** for capital-markets workflows but **broken at load** due to `hooks.json`.
- **None** of the bundled MCP URLs point at x-change, SQLite, or Glass.

---

## See also

- [`fsi-asset-index.json`](fsi-asset-index.json) — machine-readable paths.
- [`complement-matrix.md`](complement-matrix.md) — Cross-audit complements.
