# x-change — Pre-Build Code Review
**Date:** 2026-05-06
**Branch:** no git history (standalone repo)
**Reviewer:** /s&pp systematic sweep
**Scope:** Full proximity scan of `src/xchange/` (6 modules, 1804 LOC), `tests/` (9 test files, 53 tests), and `docs/` (4 policy/contract docs). Goal: verify all existing assumptions before writing the epistemic-token extension.

---

## Phase 1 — Code Quality

**Baseline: 53/53 tests green.** This is the invariant; every change must preserve it.

### Findings

| Severity | File | Line | Issue |
|----------|------|------|-------|
| Low | `storage.py` | 816 | `reward_token_amount` surfaced in `get_reward_state()` response as a raw integer — callers will be surprised when this field is later replaced with a JSON classification |
| Low | `main.py` | 332–344 | `_handle_reward_draft` accepts `reward_token_amount: int` from the HTTP body; any redesign must update this coerce-to-int path |
| Low | `storage.py` | 182–196 | `_migrate_legacy_rewards` hardcodes `reward_token_amount=1`; migration logic must be extended when columns change |
| Info | `stripe_sig.py` | 60–74 | Accepts `v0` signature as fallback to `v1`; Stripe deprecated `v0` in 2018. Safe for now but worth flagging for hardening. |
| Info | `domain.py` | 79–80 | `_boolish` is a private alias for `ingest_bool` with no added value — minor dead code, not blocking |
| Info | `main.py` | 200 | `from urllib.parse import parse_qs` imported inside method body rather than at module top |

### What's clean (and must stay that way)

- `domain.py` has zero imports from `storage.py` or `main.py` — pure function isolation is intact.
- All state writes to `reward_ledger.state` go through `_apply_transition` — `test_only_policy_advances_state` confirms this at the regex level.
- Stripe idempotency via UNIQUE on `stripe_event_id` is schema-enforced and tested.
- Fail-closed on missing `XCHANGE_INGEST_TOKEN` is confirmed by `test_fail_closed_on_missing_ingest_token`.
- `glass_adapter.py` passes all bridge fields verbatim without inferring policy booleans — the no-auto-inference rule holds.

---

## Phase 2 — Simplification & Consolidation

The codebase is small and well-scoped. No consolidation needed. Two observations worth naming:

**Consolidate:** `storage.py` has two nearly identical "write and commit, return summary" patterns (`ingest_glass_session` and `process_stripe_payment_intent_succeeded`). Both are complex enough that extracting a shared helper isn't worth it at current scale — but if exchange request handling adds a third, extract `_write_and_commit(conn, ops)` at that point.

**Extract (deferred):** `_migrate_legacy_rewards` in `storage.py:163–197` is a one-time migration that runs on every `init_db` call. It skips early if `reward_ledger` is non-empty. This is correct but fragile — if the migration logic needs to extend (it will, for epistemic columns), the skip condition needs to be revisited. Plan: version the migration with an explicit `schema_migrations` table rather than relying on row-count heuristic.

---

## Phase 3 — Optimization

Not applicable at this scale. SQLite + stdlib HTTP. The 60fps render loop concern in the Glass context does not exist here.

One latency note worth having: `open_db` creates and closes a SQLite connection on every HTTP request. WAL mode is set (good), but per-request connection cost is ~0.5–1 ms on tmpfs. Acceptable at v0 volume; flag for connection pooling if request rate exceeds ~100 RPS.

---

## Phase 4 — Structural Domain Review

### Current Domains

| Domain | Status | Files | Notes |
|--------|--------|-------|-------|
| Reward lifecycle | Complete | `domain.py`, `storage.py` | 6-state machine, pure policy layer, tested |
| Glass evidence ingest | Complete | `glass_adapter.py`, `storage.py:ingest_glass_session` | No-inference rule enforced |
| Stripe payment confirmation | Complete | `stripe_sig.py`, `storage.py:process_stripe_payment_intent_succeeded` | Idempotent, support signals on mismatch |
| Support signals | Complete | `storage.py:insert/list/resolve_support_signal`, `main.py` | First-class ops surface |
| Student acknowledgement | Complete | `storage.py:acknowledge_reward`, `main.py` | Ack separated from payment confirmation |
| Token governance | Stub | `domain.py:RewardToken` | Currently `amount: int` — the primary build target |
| Exchange constraint evaluation | Missing | — | The new system: ExchangeRequest → LayeredConstraints → approved scope |
| Token issuance endpoint | Missing | — | No HTTP surface for token classification yet |
| Forecasting / rarity engine | Missing | — | Trend-position and rarity computation |

### Missing / Underdeveloped Domains

**Exchange constraint evaluation**
What it is: The mechanism by which a token holder submits a request, and x-change evaluates that request through a layered constraint stack (safety/security → ethics/irreversibility → economic stability), narrowing the approved scope at each layer.
Current gap: No `ExchangeRequest`, `ConstraintConfig`, or `ExchangeResult` types exist. No constraint evaluation function exists. No HTTP endpoints.
Unlock: The primary value proposition of x-change as a policy-constrained exchange system, not just a reward delivery service.
Fit: New pure functions in `domain.py`, new storage functions + tables in `storage.py`, new POST endpoint in `main.py`.
Effort: Medium — domain logic is the hard part; storage and HTTP layers are mechanical.

**Epistemic token classification**
What it is: `RewardToken` redesigned to carry `insight_tier`, `base_bank_depth`, `inferential_richness`, `trend_position`, `rarity_score`, `issued_at`, `issuance_trigger`. Rarity is stamped once and immutable at issuance.
Current gap: `RewardToken` is `amount: int`. No classification schema, no issuance trigger, no rarity computation.
Unlock: Tokens become auditable epistemic credentials rather than plain counters.
Fit: Pure dataclass extension in `domain.py`. Schema migration in `storage.py` (new JSON column or explicit classification columns on `reward_ledger`).
Effort: Small-Medium — the types are clear; the scoring functions for `inferential_richness` and rarity need definition.

**Token issuance trigger**
What it is: The moment of issuance — triggered by human recognition during a session (not at session start/end). Needs an explicit API call, not inferred from threshold state.
Current gap: Issuance is implicit in reward lifecycle (drafted → earned). No explicit cognitive-trigger event.
Unlock: Issuance becomes auditable with a timestamp and trigger provenance.
Fit: New endpoint `POST /v0/tokens/issue` or extension of the draft endpoint with classification fields.
Effort: Small — primarily HTTP + storage plumbing once domain types exist.

**Schema versioning**
What it is: An explicit `schema_migrations` table tracking which migrations have run.
Current gap: `_migrate_legacy_rewards` uses a row-count heuristic to skip. Adding epistemic columns will require a second migration pass that the current skip logic won't handle correctly.
Unlock: Safe additive schema migration without data loss or re-running legacy migration logic.
Fit: 5-line table + version check in `init_db`.
Effort: Small — do this before writing any new column.

---

## Phase 5 — Security Scan

Network access is not available in this environment. Completing all other phases; flagging the gap.

**What was checked in-code:**

| Surface | File | Finding | Severity |
|---------|------|---------|----------|
| Ingest token check | `main.py:64–75` | Fail-closed when `XCHANGE_INGEST_TOKEN` unset — correct | Info |
| Stripe signature | `stripe_sig.py:32–75` | HMAC-SHA256 with timestamp tolerance — correct. Accepts `v0` fallback (deprecated by Stripe). | Low |
| Rate limiting | `main.py:95–133` | In-process per-operator bucket. No persistence across restarts — a restart resets the bucket, enabling burst attacks immediately after restart. | Medium |
| SQL injection | `storage.py` throughout | All queries use parameterized `?` placeholders — correct | Info |
| Secret in output | `main.py`, `storage.py` | No secrets printed or returned in responses | Info |
| JSON body size | `main.py:55–61` | Reads `Content-Length` bytes; no max body size cap. A request with `Content-Length: 100000000` would allocate 100 MB. | Medium |

**Livemode gap** (from `docs/stripe-boundary.md`): x-change does not check `event.livemode` against an expected environment flag. A test-mode Stripe event sent to a production instance would be processed as real. Fix: check `event.get("livemode")` against `os.environ.get("XCHANGE_LIVE_MODE", "false")`.

**No Critical findings.** The two Medium findings (rate limit reset on restart, unbounded body size) are documented gaps, not blockers for v1 build.

---

## Summary

- The existing v0 is structurally sound. 53 tests, all green. Policy isolation is real — `domain.py` has no I/O imports.
- `RewardToken` is a stub (`amount: int`). The primary build task is redesigning it with epistemic classification fields.
- Exchange constraint evaluation does not exist yet. This is the largest missing domain — it is also the core value proposition.
- Schema migration needs versioning before any new columns are added. The current row-count heuristic for skipping legacy migration will not handle a second migration pass.
- Three storage surfaces will need updates when the token type changes: `reward_ledger` schema, `create_reward_draft()`, `get_reward_state()` response, and `_migrate_legacy_rewards`.

## What to Do Next

1. **Add `schema_migrations` table in `storage.py:init_db`** — 5 lines, gates all subsequent schema work safely. Without this, the epistemic column migration will re-run or collide with legacy migration on existing DBs.

2. **Redesign `RewardToken` in `domain.py`** — Replace `amount: int` with `insight_tier`, `base_bank_depth`, `inferential_richness`, `trend_position`, `rarity_score`, `issuance_trigger`, `issued_at`. Define tier vocabulary as a `StrEnum` (`InsightTier`). Keep `amount` as a derived integer for backward compatibility in the HTTP response layer only.

3. **Add `ExchangeRequest`, `ConstraintConfig`, `ExchangeResult`, `ConstraintLayer` types to `domain.py`** — pure dataclasses, no I/O. Add `evaluate_exchange_request(request, config)` pure function that applies all three constraint layers and returns an `ExchangeResult`.

4. **Migrate `reward_ledger` schema in `storage.py`** — Add `reward_token_json TEXT` column (nullable). Keep `reward_token_amount` for the migration period; mark as deprecated in comments. Update `create_reward_draft`, `get_reward_state`, `_migrate_legacy_rewards` to handle both.

5. **Add `exchange_requests` table** — columns: `id`, `reward_id`, `student_id`, `requested_scope_json`, `constraint_result_json`, `approved`, `created_at`. Append-only audit trail.

6. **Add `POST /v0/tokens/issue` and `POST /v0/exchange/request` to `main.py`** — after domain and storage are stable.

7. **Write domain unit tests first** — `test_domain.py` already has the pattern. Add tests for: token classification rarity computation, each constraint layer passing/narrowing, full constraint stack evaluation.
