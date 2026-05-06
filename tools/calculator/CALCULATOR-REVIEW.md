# x-change Reward & Token Calculator — Review Report

**File:** `tools/calculator/xchange_reward_token_calculator.xlsx`  
**Build script:** `tools/calculator/build_calculator.py`  
**Generated:** 2026-05-07  
**Policy source:** `docs/policy-core-v0.md`  
**Code source:** `src/xchange/domain.py`

---

## Build Verification

| Check | Result |
|-------|--------|
| Python build errors | 0 |
| Hardcoded Excel error strings (`#VALUE!`, `#REF!`, etc.) | 0 |
| Bad formula cells (empty `=`) | 0 |
| **Total formula cells** | **240** |
| **Total yellow input cells** | **170** |

---

## Sheet Inventory

| Sheet | Purpose | Formulas | Input Cells |
|-------|---------|----------|-------------|
| `Cover` | Navigation and metadata | 0 | 0 |
| `Assumptions` | All configurable parameters | 2 | 36 |
| `Rarity_Calc` | Single-token rarity calculator | 12 | 5 |
| `Tier_Ref` | InsightTier reference (cross-sheet links) | 20 | 0 |
| `Lifecycle` | State machine and valid transitions | 0 | 0 |
| `Token_Log` | 15-token portfolio with formula-driven rarity | 44 | 105 |
| `Exchange_Eval` | 3-layer exchange constraint evaluator | 113 | 24 |
| `Summary` | Portfolio dashboard | 49 | 0 |

---

## Requirements Coverage

### Rarity Scoring (`domain.py:compute_rarity_score`)

| Requirement | Status | Location |
|------------|--------|----------|
| Formula: `0.4×(1−trend_position) + 0.4×inferential_richness + 0.2×tier_weight` | PASS | `Rarity_Calc!B20`, `Token_Log!G4:G18` |
| Weights configurable (not hardcoded) | PASS | `Assumptions!B3:B5` |
| Weight sum check (`must = 100%`) | PASS | `Assumptions!B6` with `✓ OK` / `✗ ERROR` indicator |
| Score clamped to `[0.0, 1.0]` | PASS | `MAX(0, MIN(1, …))` in all rarity formulas |
| Score rounded to 4 decimal places | PASS | `fmt="0.0000"` on all rarity output cells |

### InsightTier Classification

| Requirement | Status | Location |
|------------|--------|----------|
| All 5 tiers present: surface/pattern/structural/causal/theoretical | PASS | `Assumptions!A10:A14`, `Tier_Ref!A3:A7` |
| Backward-compatible integer amounts (1–5) | PASS | `Assumptions!C10:C14` |
| Tier rarity weights (0.00, 0.25, 0.50, 0.75, 1.00) | PASS | `Assumptions!B10:B14` |
| Tier amounts formula-driven (VLOOKUP, not hardcoded) | PASS | `Rarity_Calc!B16`, `Token_Log!H4:H18` |
| Data validation dropdown (tier selection) | PASS | `Rarity_Calc!B6`, `Token_Log!C4:C18` |

### Reward State Machine (`domain.py:RewardState`)

| Requirement | Status | Location |
|------------|--------|----------|
| All 6 states documented | PASS | `Lifecycle!A5:A10` |
| Valid transition matrix | PASS | `Lifecycle!A15:E22` |
| Evidence types (6 types) | PASS | `Lifecycle!A27:C32` |
| Stripe replay idempotency noted | PASS | `Lifecycle!A21:E22` |
| `review_requested` as lateral transition | PASS | `Lifecycle!A20` |

### Token Log Portfolio

| Requirement | Status | Location |
|------------|--------|----------|
| 15 sample tokens | PASS | `Token_Log!A4:I18` |
| Rarity score formula-driven per token | PASS | `Token_Log!G4:G18` |
| Amount formula-driven per token | PASS | `Token_Log!H4:H18` |
| Portfolio statistics (count, avg, min, max, tier breakdown, rarity bands) | PASS | `Token_Log!A23:C36` |

### Exchange Constraint Evaluation (`domain.py:evaluate_exchange_request`)

| Requirement | Status | Location |
|------------|--------|----------|
| Layer 1: Safety/Security hard gate (blocked key COUNTIF) | PASS | `Exchange_Eval!B26:B35` |
| Layer 2: Ethics/Irreversibility scope narrowing | PASS | `Exchange_Eval!D42:D51` |
| Layer 3: Economic stability (scope count cap + token_amount cap) | PASS | `Exchange_Eval!C62:D71` |
| Blocked keys configurable in Assumptions | PASS | `Assumptions!A25:A32` |
| Irreversible keys configurable in Assumptions | PASS | `Assumptions!A36:A43` |
| Max token amount configurable | PASS | `Assumptions!B19` |
| Max scope items configurable | PASS | `Assumptions!B20` |
| Final result (overall approved, items by layer) | PASS | `Exchange_Eval!A76:B81` |

### Portfolio Summary Dashboard

| Requirement | Status | Location |
|------------|--------|----------|
| Tokens by tier (count, %, avg rarity, avg/total amount) | PASS | `Summary!A17:F22` |
| Rarity band distribution (Very Rare/Rare/Uncommon/Common) | PASS | `Summary!A26:E29` |
| Portfolio-level stats (total, avg, median, stdev, min, max rarity) | PASS | `Summary!A6:B12` |
| No manual inputs (100% formula-driven) | PASS | 0 yellow input cells on sheet |

### Color Coding Convention

| Convention | Status |
|-----------|--------|
| Blue text = hardcoded inputs | PASS (`ARGB: FF0000FF`) |
| Black text = formula outputs | PASS (`ARGB: FF000000`) |
| Green text = cross-sheet link formulas | PASS (`ARGB: FF008000`) |
| Yellow background = key assumption cells | PASS (`ARGB: FFFFFF00`) |
| Arial font throughout | PASS |

---

## Known Limitations

1. **No LibreOffice recalculation** — formula values are stored as formula strings only; Excel/LibreOffice must open the file to compute live results. This is the expected behavior for openpyxl-generated workbooks.
2. **Exchange_Eval Layer 3 scope ranking** — the `OVER_LIMIT` logic uses `SUMPRODUCT` rank estimation rather than a strict ordered rank, which may not exactly replicate `enumerate()`-based ordering from `domain.py`. Acceptable for a calculator model.
3. ~~**`data/` directory created but empty**~~ — **RESOLVED.** See `data/` directory and `scripts/export_calculator_data.py`.

---

## Data Directory (`data/`)

Three CSV files are maintained in `data/`. They serve dual purpose: (a) format fixtures that match the calculator sheet column order, (b) outputs of the live export script.

| File | Purpose | Sheet mapping |
|---|---|---|
| `data/token_log_sample.csv` | Token issuance records | → `Token_Log` columns A–I |
| `data/reward_ledger_summary.csv` | Per-reward state + token summary | → `Summary` dashboard context |
| `data/evidence_ledger_sample.csv` | Evidence rows with optional reward association | Reference only |

**Refresh from live database:**

```bash
# Default: reads $XCHANGE_DB_PATH or ./xchange.sqlite, writes to ./data/
uv run python3 scripts/export_calculator_data.py

# Explicit paths
uv run python3 scripts/export_calculator_data.py \
  --db /path/to/xchange.sqlite \
  --out /path/to/data/
```

The script exits non-zero with a clear message if the database is not found.
Column ordering in the CSVs matches the `Token_Log` sheet headers exactly so
rows can be pasted directly into column A of the sheet.

---

## File Paths

```
x-change/
  tools/
    calculator/
      build_calculator.py          ← regenerate with: uv run --with openpyxl python3 build_calculator.py
      xchange_reward_token_calculator.xlsx
      CALCULATOR-REVIEW.md         ← this file
  scripts/
    export_calculator_data.py      ← export live SQLite → data/ CSVs
  data/
    token_log_sample.csv           ← 15-token fixture (Token_Log column order)
    reward_ledger_summary.csv      ← reward state summary fixture
    evidence_ledger_sample.csv     ← evidence rows fixture
```
