# x-change — architecture and codebase audit

**Audit date:** 2026-05-07
**Scope:** Repository `/home/irfankabir/x-change` only (runtime: stdlib + SQLite, zero PyPI deps).
**Canonical ops:** [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md).

---

## 1. Context — what the app is

x-change is a **principled reward-delivery core**: service contract → **evidence** (Glass / optional failures / USEB substantiation) → **reward ledger state** → **Stripe `payment_intent.succeeded`** (HMAC-verified webhook) → **student acknowledgement** as a separate step. **Support signals** capture Stripe metadata gaps and mismatches without silent drops. Policy is explicit: **payment confirms funds movement, not educational outcome** ([`docs/policy-core-v0.md`](../policy-core-v0.md)).

**Non-goals (architectural):** not GRID’s subscription Stripe surface ([`docs/stripe-boundary.md`](../stripe-boundary.md)); not a general-purpose HTTP framework app.

---

## 2. Structural map

| Layer | Module | Responsibility |
|-------|--------|------------------|
| Entry | [`src/xchange/__main__.py`](../../src/xchange/__main__.py) | Reads `XCHANGE_HOST` / `XCHANGE_PORT`, calls `run_server()`. |
| HTTP | [`src/xchange/main.py`](../../src/xchange/main.py) | `BaseHTTPRequestHandler` routing, auth (`Bearer` / `X-Ingest-Token` + optional `XCHANGE_INGEST_TOKEN_PREV`), rate limit, body size caps, JSON/HTML responses, readonly viewer. |
| Policy | [`src/xchange/domain.py`](../../src/xchange/domain.py) | `RewardState`, `EvidenceType`, transitions (`next_state_after_glass_evidence`, `next_state_after_stripe_payment`), token/exchange/scope types — **no I/O**. |
| Persistence | [`src/xchange/storage.py`](../../src/xchange/storage.py) | SQLite schema (legacy + core tables), ingest, Stripe processing, support signals, evidence patch, exchange, scope resolution helpers. |
| Stripe crypto | [`src/xchange/stripe_sig.py`](../../src/xchange/stripe_sig.py) | HMAC-SHA256 verification, tolerance — no Stripe SDK. |
| Glass | [`src/xchange/glass_adapter.py`](../../src/xchange/glass_adapter.py) | `map_glass_bridge_to_ingest` — bridge blob + caller enrichment. |
| USEB / GRID | [`src/xchange/grid_substantiation.py`](../../src/xchange/grid_substantiation.py), [`src/xchange/useb.py`](../../src/xchange/useb.py) | Normalize optional substantiation evidence. |
| UX text | [`src/xchange/nudge.py`](../../src/xchange/nudge.py) | Deterministic nudge strings from failure commands. |

---

## 3. HTTP surface (v0)

| Method | Path | Auth | Notes |
|--------|------|------|------|
| GET | `/v0/viewer` | ingest | Read-only HTML collaborator view. |
| GET | `/v0/state/reward/<reward_id>` | ingest | RewardModel-oriented JSON. |
| GET | `/v0/outcomes/summary` | ingest | Aggregates by state. |
| GET | `/v0/support-signals` | ingest | Filters `kind`, `resolved`. |
| GET | `/v0/exchange/requests` | ingest | List exchange requests. |
| GET | `/v0/scope/token/<reward_id>` | ingest | Token scope resolution. |
| GET | `/v0/scope/tool` | ingest | `provenance` query param. |
| POST | `/v0/ingest/glass-session` | ingest | Session + optional failure. |
| POST | `/v0/ingest/glass-bridge` | ingest | Bridge dict + enrichment. |
| POST | `/v0/stripe/webhook` | Stripe-Signature | Single event type path. |
| POST | `/v0/rewards/draft` | ingest | Create drafted reward. |
| POST | `/v0/rewards/<id>/acknowledge` | ingest | Student ack. |
| POST | `/v0/support-signals/<id>/resolve` | ingest | Resolve signal. |
| POST | `/v0/tokens/issue` | ingest | Issue RewardToken metadata. |
| POST | `/v0/exchange/request` | ingest | Exchange evaluation + persist. |
| PATCH | `/v0/evidence/<id>` | ingest | Link evidence to reward. |

---

## 4. Mechanical influences on architecture

1. **stdlib `HTTPServer` + single handler class** — No ASGI middleware stack; cross-cutting concerns (auth, rate limit, max body) are **inline** in `AppHandler` and helpers (`_require_ingest_token`, `_rate_limit_settings`, `_max_body_bytes`). This favors **explicit** branches over plugin hooks.

2. **SQLite + WAL** (`storage.py` pragma) — Single-file durability; all consistency rules are **application-enforced** (e.g. unique `stripe_event_id`, idempotent applies).

3. **Policy choke point** — `domain.next_state_*` + `ingest_bool` semantics: raw HTTP and storage **never** advance state without passing domain rules. Ingest handlers call `storage.apply_evidence_to_reward` / Stripe path uses `next_state_after_stripe_payment`.

4. **Fail-closed configuration** — Missing `XCHANGE_INGEST_TOKEN` or `STRIPE_WEBHOOK_SECRET` rejects relevant routes ([AGENTS.md](../../AGENTS.md)); shapes operator vs Stripe trust boundaries.

5. **Glass contract** — Bridge fields are **never** interpreted as policy booleans ([`docs/glass-contract-v0.md`](../glass-contract-v0.md)); prevents “ambient UI state” from becoming ledger writes.

6. **Stripe retry safety** — Many anomaly paths return **HTTP 200** to Stripe while recording `support_signals` ([`docs/stripe-boundary.md`](../stripe-boundary.md)); avoids retry storms.

---

## 5. Vertical slices (code review)

### Slice A — Glass bridge → evidence → optional transition

1. `AppHandler._handle_ingest_glass_bridge` parses JSON, requires `bridge` dict.
2. `map_glass_bridge_to_ingest` copies `session_id`, embeds full bridge under `_glass_bridge`, merges caller flags and optional `grid_substantiation`.
3. `ingest_glass_session` → `append_evidence` + `apply_evidence_to_reward` using `next_state_after_glass_evidence`.

**Invariant:** `_glass_bridge` keys do not auto-map to `contract_satisfied` / `ready_for_payment`.

### Slice B — Stripe webhook → payment row → state

1. `_handle_stripe_webhook` verifies signature (`stripe_sig.verify_stripe_signature`), parses event.
2. `process_stripe_payment_intent_succeeded` records `payment_confirmations`, may insert `support_signals`, applies `next_state_after_stripe_payment` when metadata matches.

**Invariant:** missing metadata → signal, not silent skip.

---

## 6. Data planes (tables)

| Table | Role |
|-------|------|
| `reward_ledger` | Canonical reward lifecycle + token JSON / outcome fields. |
| `evidence_ledger` | Append-friendly evidence with `provenance`, optional `reward_id`. |
| `payment_confirmations` | Stripe events, status, raw JSON. |
| `support_signals` | Exception queue (`kind`, `payload_json`, `resolved_at`). |
| `exchange_requests` | Token exchange evaluations. |
| `service_contracts` | PSC seed. |
| Legacy `sessions`, `failures`, `rewards`, `nudges` | Mirror / nudge compatibility. |

---

## 7. Test coverage map (tests vs surface)

| Test module | Primary coverage |
|-------------|------------------|
| `test_domain.py` | Policy transitions. |
| `test_stripe_signature.py`, `test_webhook_dedup.py` | Stripe HMAC + idempotency. |
| `test_support_signals_api.py` | List/resolve signals. |
| `test_ack_api.py` | Acknowledgement route. |
| `test_glass_adapter.py` | Bridge mapping. |
| `test_grid_substantiation.py`, `test_useb.py` | USEB / GRID payloads. |
| `test_token_exchange_api.py`, `test_token_rotation.py`, `test_scope.py` | Tokens / exchange / scope APIs. |
| `test_readonly_viewer.py` | Viewer sanitization. |
| `test_evidence_patch.py` | PATCH evidence. |
| `test_outcome_summary.py` | Outcomes summary. |
| `test_http_boundaries.py`, `test_http_gap.py`, `test_main_utils.py` | Size limits, helpers. |
| `test_storage_coverage.py`, `test_storage_extra.py`, `test_reward_foundation.py` | Storage edge cases. |
| `test_entrypoint.py` | CLI entry. |
| `test_nudge.py` | Nudge generation. |
| `test_validation_gate.py` | Validation gate behavior. |

**Gaps to carry to complement matrix:** no automated test for **full** multi-step “Glass bridge + Stripe + ack” E2E in one file (many pieces exist separately); no MCP server (documented future in [`docs/finance-agents-modernization.md`](../finance-agents-modernization.md)).

---

## 8. Summary strengths / risks

**Strengths:** Clear separation of evidence vs policy vs payment; explicit support path; small blast radius; strong test spread for a small codebase.

**Risks:** In-process rate limit map (multi-worker deployment would need external limiter); livemode hardening noted in stripe-boundary; operator routes depend on shared ingest secret hygiene.

---

## See also

- [`fsi-marketplace-audit.md`](fsi-marketplace-audit.md) — Installed Claude plugins inventory.
- [`complement-matrix.md`](complement-matrix.md) — Gap ↔ asset mapping.
