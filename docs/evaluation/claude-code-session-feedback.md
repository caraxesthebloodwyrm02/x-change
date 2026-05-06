# Feedback for Claude Code (session-derived, verified)

**Context:** x-change repo — Anthropic **financial-services** marketplace (`claude-for-financial-services`), post-integration evaluation, local SQLite recon, and `scripts/stripe_ledger_verify.py` runs.
**Audience:** Product / plugins / marketplace teams (copy sections as needed).

---

## 1. `financial-analysis` — `hooks.json` is `[]` (confirmed)

```bash
cat ~/.claude/plugins/cache/claude-for-financial-services/financial-analysis/0.1.0/hooks/hooks.json
# []
```

The loader reports **expected object, received array**. The CLI plugin cache faithfully clones what was published — the **gate has to be upstream** (publish-time defect).

**Publish pipeline (upstream):** Assert `hooks.json` is a JSON **object** or absent, e.g.:

```bash
python -c "import json, pathlib; p = pathlib.Path('hooks/hooks.json'); \
  assert not p.exists() or isinstance(json.loads(p.read_text()), dict)"
```

If “no hooks” is intentional, ship **`{}`** or **omit** the file.

**CLI error UX (runtime):** When hook load fails on shape, add a one-line hint, e.g.
`hooks.json must be a JSON object, not an array` — see hooks documentation (e.g. [Hooks](https://code.claude.com/docs/en/hooks)) — so the operator avoids a filesystem dig.

---

## 2. GitHub slug vs marketplace display name (confirmed)

| Concept | Value |
|---------|--------|
| Marketplace id | `claude-for-financial-services` |
| Real GitHub repo | `anthropics/financial-services` |
| Broken inference | `claude plugin marketplace add anthropics/claude-for-financial-services` → **404** |

Natural inference from the marketplace id does not match a real repo; **doc and CLI disagree silently**.

**README (upstream):** Two-line install block, e.g.:

```bash
claude plugin marketplace add anthropics/financial-services
```

**CLI:** On `git clone` 404 for `github.com/<org>/<repo>.git`, pattern-match known marketplaces and emit:
`try: anthropics/financial-services`.

---

## 3. Agent templates assume `mcp__internal-gl__*` (confirmed in both agents)

**`gl-reconciler.md` (frontmatter):**

`tools: Read, Grep, Glob, mcp__internal-gl__*, mcp__subledger__*`

**`month-end-closer.md`:**

`tools: Read, Grep, Glob, mcp__internal-gl__*`

Neither MCP prefix resolves on a default install. Definitions are structurally sound for fund accounting, but **inert** without a user MCP server — sessions **degrade to narrative-only**, as observed.

**Plugin README (upstream):**

- Add **“Bring your own ledger”** with a minimal MCP contract, for example two tools:
  - `mcp__internal-gl__read_balances(entity, trade_date, asset_classes)` → `[{account, balance_ccy, balance_base}]`
  - `mcp__subledger__read_holdings(entity, trade_date, asset_classes)` → `[{security_id, quantity, local_amount, base_amount}]`

**Optional preflight:** At session start, if an enabled agent declares `mcp__*` wildcards and **none** resolve in the current MCP config, emit one line, e.g.
`agent gl-reconciler references mcp__internal-gl__* — no matching server found`.

**Worked example:** The x-change session shows the same **recon pattern** works when “subledger” is SQLite + `payment_confirmations` / `evidence_ledger` and verification is a small Python script (`scripts/stripe_ledger_verify.py`). A **~20-line** ledger-agnostic example in FSI docs would lower activation cost.

---

## 4. `scripts/stripe_ledger_verify.py` — green (confirmed)

```
stripe_ledger_verify db=/home/irfankabir/x-change/xchange.sqlite rows=1
  applied+consistent: 1
  issues: none
```

Clean output, zero-config with `uv run`. Discoverability: a **one-line** in project `CLAUDE.md` / Makefile `verify` target (optional) — see [CLAUDE.md](../../CLAUDE.md) Run section.

---

## 5. Cursor terminal `last_command` newline merge (not Claude Code)

`terminals/*.txt` sometimes collapses newlines in `last_command` while the transcript body is correct — **copy-paste fidelity** issue. **Fix locus:** Cursor terminal metadata writer, not Anthropic.

---

## Summary (prioritized, with verification status)

| Priority | Item | Verified | Fix locus |
|----------|------|----------|-----------|
| **P0** | `hooks.json` is `[]`, loader rejects | Confirmed — file contents are `[]` | Publish pipeline + CLI error string |
| **P1** | `marketplace add anthropics/claude-for-financial-services` 404s | Confirmed — real repo is `anthropics/financial-services` | README install block + CLI 404 hint |
| **P2** | `mcp__internal-gl__*` / `mcp__subledger__*` unresolvable | Confirmed in both agent YAMLs | Plugin README (BYO-ledger) + optional preflight |
| **P3** | Ledger-agnostic recon example | Session proves viability (SQLite + script) | FSI docs (worked example) |
| **P4** | Cursor `last_command` newline merge | Cursor-side capture | Cursor |

The first three are **concrete, file-specific**, each addressable with small upstream edits. Item 4 already **works** in-repo — remaining gap is **documentation**, not engineering.

---

## One-line paste (generic feedback form)

> `financial-analysis` fails to load: `hooks/hooks.json` is `[]` but the loader expects a JSON object — validate at publish time and improve the error string. `marketplace add` should document `anthropics/financial-services`. GL agents assume `mcp__internal-gl__*` / `mcp__subledger__*` — add a minimal BYO-ledger MCP contract and optional preflight when prefixes are unresolved.
