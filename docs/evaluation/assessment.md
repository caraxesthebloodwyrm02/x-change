# Executive assessment — x-change vs Anthropic FSI (post-integration evaluation)

**Date:** 2026-05-07
**Status:** Evaluation pack **executed**; tests **305 OK** (`PYTHONPATH=src uv run python -m unittest discover -s tests -q`).

This document is the **synthesis** of the dual audits, complement matrix, and combo trial. Source detail lives in the linked files below.

---

## 1. Verdict (one line)

**Conclusion A:** Keep Anthropic financial-services plugins as **reference / narrative patterns** only; **do not** treat them as integration dependencies for x-change core. Prefer **internal scaffolding** (docs + optional MCP read layer) over marketplace coupling.

---

## 2. Evidence summary

| Dimension | Finding |
|-----------|---------|
| **x-change** | Small, coherent stack: stdlib HTTP, SQLite, policy choke in `domain.py`, Glass evidence-only boundary, Stripe fail-closed signals. See [x-change-audit.md](x-change-audit.md). |
| **Installed FSI** | `gl-reconciler` + `month-end-closer` enabled; both assume **`mcp__internal-gl__*`** (and subledger for GL) — **not present** in this repo. `financial-analysis` **fails to load** (`hooks.json` is `[]`). See [fsi-marketplace-audit.md](fsi-marketplace-audit.md), [fsi-asset-index.json](fsi-asset-index.json). |
| **Complement** | Strong **process** overlap (exception queue → human sign-off); weak **tool** overlap (no MCP to ledger; modeling/MCP vendors misfit). See [complement-matrix.md](complement-matrix.md). |
| **Trial** | Combo + goal scored; **mean rubric = 2.5** (&lt; 3 → Conclusion A). See [combo-trial-record.md](combo-trial-record.md). |

---

## 3. Rubric outcome (session-scale)

| Axis | Score | Headline |
|------|------:|----------|
| Emergence | 2 | Reinforces known gaps, little novelty |
| Code quality | 2 | No mergeable output from plugins |
| Usefulness | 3 | Runbook / digest **shape** is reusable as internal docs |
| Discovery | 3 | MCP read-server priority; `financial-analysis` hook defect |

**Mean:** **2.5** — below the plan’s “≥ 3 to double down on marketplace leverage” bar.

---

## 4. Recommended immediate path

1. **P1 (scaffold):** Add or extend internal Markdown runbooks for `support_signals` + monthly outcomes/payment digest — **no** FSI runtime.
2. **P2 (when ready):** MCP read tools over existing HTTP/SQLite surfaces — **then** optional re-score (combo-trial **P6**).

Defer **P3** (patch `financial-analysis` hooks) unless you explicitly want IB/ER slash commands; core product alignment remains low even if fixed.

---

## 5. Artifact index

| File | Role |
|------|------|
| [README.md](README.md) | Pack index |
| [x-change-audit.md](x-change-audit.md) | Codebase / architecture audit |
| [fsi-marketplace-audit.md](fsi-marketplace-audit.md) | Installed plugin audit |
| [fsi-asset-index.json](fsi-asset-index.json) | File inventory |
| [complement-matrix.md](complement-matrix.md) | Gap ↔ asset matrix |
| [combo-trial-record.md](combo-trial-record.md) | Trial, scores, PATHS P1–P6 |
| **This file** | Executive assessment |

---

## 6. Cross-links

- [glass-xchange-fsi-release-audit.md](../glass-xchange-fsi-release-audit.md) — Glass + FSI structural audit
- [anthropic-financial-services-integration.md](../anthropic-financial-services-integration.md) — Marketplace install notes
- [finance-agents-modernization.md](../finance-agents-modernization.md) — MCP roadmap
