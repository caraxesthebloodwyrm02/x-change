# Combo trial record — FSI agents vs x-change read surfaces

**Date:** 2026-05-07
**Procedure:** Plan §D–E — one selective combo, one concise goal, rubric 1–5, verdict + PATHS.

---

## 1. Selected combo

| Item | Rationale |
|------|-----------|
| **gl-reconciler@claude-for-financial-services** | Strongest **workflow** homology to `support_signals` (exception → trace → sign-off). |
| **month-end-closer@claude-for-financial-services** | Adds **period packaging** language; shares `audit-xls` / `xlsx-author` with gl-reconciler (overlap acceptable for single trial). |

**Excluded:** `financial-analysis` — **not loaded** in Claude Code (`hooks.json` invalid); including it would not reflect operator reality.

---

## 2. One-sentence goal

> Produce a **controller-style exception pack** for **open** `support_signals` plus a **30-day payment confirmation summary**, using **only** read-only x-change surfaces (HTTP GETs or SQLite read) and repo policy docs — **no** ledger writes, **no** Stripe posts, **no** inferring Glass policy from bridge telemetry.

---

## 3. Preconditions and local smoke

| Check | Result |
|-------|--------|
| Fresh DB open + outcome summary | `PYTHONPATH=src uv run python` with `open_db('/tmp/xe_eval.sqlite')` → `{'total_rewards': 0, 'by_state': {}, 'student_count': 0}` |
| Env for full HTTP trial | Not required for empty DB; production-like trial would use `XCHANGE_INGEST_TOKEN` + `curl` to `/v0/outcomes/summary` and `/v0/support-signals` |

**Note on Claude transcript:** This trial did **not** capture a live Claude Code session log (non-interactive evaluation). The **sample output** below is a **synthesis** structured to match the **declared deliverables** in `agents/gl-reconciler.md` and `agents/month-end-closer.md` applied to x-change semantics — used to score **usefulness of the pattern**, not to claim vendor agent verbatim output.

---

## 4. Sample synthesized output (goal-shaped)

### A. Exception pack — open `support_signals`

*No open signals in smoke DB — template shows expected shape when data exists.*

1. **Break list (signals)**
   - Table: `id`, `kind`, `created_at`, `payload_json` keys (e.g. `stripe_missing_metadata`, `stripe_student_mismatch`).
2. **Root-cause trace (per kind)**
   - Reference [`docs/stripe-boundary.md`](../stripe-boundary.md) failure mode matrix; map `kind` → recommended human checks (Dashboard metadata, `reward_id` existence).
3. **Recommended resolution (draft — human executes)**
   - For each row: suggested `POST /v0/support-signals/<id>/resolve` body **after** operator verification — aligns with agents’ “no posting” guardrail adapted to x-change’s resolve endpoint as **human-gated** write.

### B. Payment confirmation summary (30-day window)

*Empty DB → structure only.*

- Query `payment_confirmations` filtered by `created_at` (operator SQL or future read tool).
- Group by `status` (`received`, `applied`, `duplicate_ignored`, `not_applied_mismatch` per domain).
- Tie to `reward_ledger` via `reward_id` for narrative “funds applied vs pending review.”

### C. “Close checklist” echo (from month-end-closer)

- Accrual / JE **not applicable**.
- **Roll-forward analogue:** prior period `payment_confirmed` count → current (placeholder).
- **Variance commentary analogue:** delta in `support_signals` opened vs resolved week-over-week (placeholder).

---

## 5. Rubric scores (1–5)

| Axis | Score | Justification |
|------|------:|---------------|
| **Emergence** | 2 | Confirms known gap (MCP / export) rather than revealing a novel integration; matrix largely pre-determined. |
| **Code quality** | 2 | No mergeable code from plugins; sample is prose/checklist only. |
| **Usefulness** | 3 | Usable **runbook skeleton** for support triage and monthly digest **if** operator maintains it; does not automate x-change. |
| **Discovery** | 3 | Sharpens **MCP read-server** priority and documents `hooks.json` blocker for financial-analysis. |

**Mean:** (2 + 2 + 3 + 3) / 4 = **2.5**

**Safety:** No unsafe writes proposed in sample; aligns with policy.

---

## 6. Verdict (plan threshold)

Plan rule: **Mean < 3** → **Conclusion A — Reference-only / scaffold internally.**

**Verdict:** **Conclusion A.** Treat installed FSI ops agents as **narrative and checklist references**; do **not** depend on marketplace assets for x-change core behavior. **financial-analysis** remains **blocked** until `hooks.json` is fixed upstream or patched locally (optional Path 3 below).

---

## 7. PATHS (sharp branches)

| ID | Path |
|----|------|
| P1 | **Scaffold internal ops pack** — `docs/` Markdown templates for signal triage + monthly digest fed only by x-change exports; **no** FSI runtime dependency. |
| P2 | **MCP read server** — Expose `list_support_signals`, `get_outcome_summary`, `query_payment_confirmations` as tools; optionally **rename** mentally to “internal-ledger” for agent prompts **without** cloning GL semantics in schema. |
| P3 | **Patch financial-analysis** — Replace `hooks/hooks.json` `[]` with valid `{}` per Claude Code schema, then **re-run** complement matrix for `skill-creator` / commands (still mostly misfit for core product). |
| P4 | **Glass + exception narrative** — Attach `_glass_bridge` excerpts to human-written triage notes only; never auto-resolve from telemetry. |
| P5 | **Deprioritize FSI** — Invest test time in complement-matrix gaps (e.g. E2E multi-step test) per [`x-change-audit.md`](x-change-audit.md) §7. |
| P6 | **Combo retry after P2** — Re-score emergence/usefulness once MCP tools exist; expect mean ≥ 3 if agents can pull real balances. |

---

## 8. Artifacts index

| File | Role |
|------|------|
| [`x-change-audit.md`](x-change-audit.md) | System audit |
| [`fsi-marketplace-audit.md`](fsi-marketplace-audit.md) | Plugin audit |
| [`fsi-asset-index.json`](fsi-asset-index.json) | File inventory |
| [`complement-matrix.md`](complement-matrix.md) | Gap ↔ asset |
| This file | Trial + scores + PATHS |

---

## 9. Follow-up implemented (Stripe ↔ ledger drift check)

Read-only script (no Stripe API): [`../../scripts/stripe_ledger_verify.py`](../../scripts/stripe_ledger_verify.py)

```bash
XCHANGE_DB_PATH="$PWD/xchange.sqlite" uv run python scripts/stripe_ledger_verify.py --student prince
# optional window (ISO prefixes on payment_confirmations.created_at):
uv run python scripts/stripe_ledger_verify.py "$PWD/xchange.sqlite" --since 2026-05-06 --until 2026-05-07
```

Flags **metadata** in `raw_event_json` vs DB columns and checks `status=applied` rows sit on a post-payment ledger state.
