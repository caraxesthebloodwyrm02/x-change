# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is x-change

A reward-delivery service that accepts session telemetry (Glass sessions with failure snapshots), processes Stripe `payment_intent.succeeded` webhooks, and generates nudge records for students. Pure Python, stdlib `http.server`, SQLite storage; **no PyPI deps on the HTTP server**. Optional read-only MCP over SQLite uses uv dependency group `mcp` (`docs/mcp-server.md`).

## Run / Test / Lint

```bash
# Run the server
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
export XCHANGE_INGEST_TOKEN="dev-secret"
export STRIPE_WEBHOOK_SECRET="whsec_..."
PYTHONPATH="$PWD/src" uv run python -m xchange
# Listens on 0.0.0.0:8788 by default (override: XCHANGE_HOST, XCHANGE_PORT)

# Run tests
PYTHONPATH="$PWD/src" uv run python -m unittest discover -s tests -v

# MCP stdio server (read-only ledger tools; installs dependency group `mcp`)
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
PYTHONPATH="$PWD/src" uv run --group mcp python -m xchange.xchange_mcp

# Run a single test
PYTHONPATH="$PWD/src" uv run python -m unittest tests.test_stripe_signature -v

# Read-only Stripe ↔ ledger drift check (SQLite only; no Stripe API)
XCHANGE_DB_PATH="$PWD/xchange.sqlite" uv run python scripts/stripe_ledger_verify.py --student <student_id>
```

No build step. No linter configured yet. `pyproject.toml` + `uv.lock` are intentional for reproducible local execution; PYTHONPATH must include `src/` for direct module runs.

## Architecture

```
src/xchange/
  __main__.py   — entrypoint: reads env, calls run_server()
  main.py       — HTTP handler (stdlib BaseHTTPRequestHandler), routes, request parsing
  domain.py     — pure policy: RewardState lifecycle enum, transition functions (no I/O)
  storage.py    — SQLite schema + all DB operations (legacy tables plus reward/evidence/payment/support ledgers)
  glass_adapter.py — Glass bridge to ingest-payload mapper; preserves telemetry as evidence only
  stripe_sig.py — HMAC-SHA256 Stripe webhook signature verification (no Stripe SDK)
  nudge.py      — deterministic nudge text generation from failure commands
```

**Request flow:** HTTP request → `AppHandler` (main.py) → auth check/operator rate limit (Stripe uses signature instead) → storage write/read → optional domain transition → response.

**Key design rules from `docs/policy-core-v0.md`:**
- Only the policy layer (`domain.py` rules) advances reward state — raw evidence and Stripe JSON propose transitions, they don't bypass validation.
- `RewardToken` is x-change's own governance unit, not related to signal-rate tokens elsewhere in the ecosystem.
- Stripe payment confirms funds movement, not educational outcome. Student acknowledgement is separate.
- Missing Stripe metadata or mismatches must emit support signals, never silently discard.
- Fail closed: missing `XCHANGE_INGEST_TOKEN` or `STRIPE_WEBHOOK_SECRET` rejects requests.
- **No `anthropic` SDK dependency.** References to `anthropic` in `docs/` are marketplace integration guidance only (XC-003, `docs/evaluation/runtime-contract-audit-2026-05-09.md`). The runtime has zero outbound calls to Anthropic APIs.

## API Endpoints (v0)

_Last audited 2026-05-11 against `main.py`. "Operator auth" = Bearer token or X-Ingest-Token header._

### Ingest (write, ingest token)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v0/ingest/glass-session` | Ingest token | Store Glass session + optional failure snapshot |
| POST | `/v0/ingest/glass-bridge` | Ingest token | Map Glass bridge telemetry into evidence ingest |

### Stripe (write, Stripe-Signature)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v0/stripe/webhook` | Stripe-Signature | Process `payment_intent.succeeded` webhook |

### Reward lifecycle (write, operator auth)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v0/rewards/draft` | Operator auth | Create a drafted reward record |
| POST | `/v0/rewards/<id>/acknowledge` | Operator auth | Advance reward to `student_acknowledged` |
| POST | `/v0/tokens/issue` | Operator auth | Issue a governance token |
| POST | `/v0/exchange/request` | Operator auth | Submit a token exchange request |
| PATCH | `/v0/evidence/<id>` | Operator auth | Retroactively link evidence to a reward |

### Read / query (operator auth)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/v0/viewer` | Operator auth | HTML dashboard: reward state + exchange requests |
| GET | `/v0/state/reward/<reward_id>` | Operator auth | Query single reward delivery state |
| GET | `/v0/outcomes/summary` | Operator auth | Aggregate reward counts by state; `?student_id=` filter |
| GET | `/v0/support-signals` | Operator auth | List support signals |
| GET | `/v0/exchange/requests` | Operator auth | List exchange requests; `?reward_id=` / `?state=` filters |
| GET | `/v0/scope/token/<id>` | Operator auth | Get governance scope for a token |
| GET | `/v0/scope/tool` | Operator auth | Get governance scope for a tool |

### Support signal resolution (operator auth)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v0/support-signals/<id>/resolve` | Operator auth | Resolve a support signal |

### MCP read-only tools (`xchange_mcp.py`, stdio)

_Requires `uv run --group mcp python -m xchange.xchange_mcp`. All tools read SQLite only — no writes._

| Tool | Purpose |
|------|---------|
| `xchange_list_support_signals` | Paginated support signals; `kind`, `resolved`, `limit`, `offset` |
| `xchange_get_outcome_summary` | Aggregate reward counts by state; optional `student_id` |
| `xchange_get_reward_state` | Single reward state by `reward_id` |
| `xchange_list_exchange_requests` | Paginated exchange requests |
| `xchange_list_payment_confirmations` | Paginated payment confirmation records |

## SQLite Tables

Legacy mirror tables: `sessions`, `failures`, `rewards`, `nudges`. Core policy tables: `service_contracts`, `reward_ledger`, `evidence_ledger`, `payment_confirmations`, `support_signals`. Schema is defined in `storage.py` and auto-created on first connection via `open_db()`.

## Reward Lifecycle States

`drafted` → `earned` → `payment_pending` → `payment_confirmed` → `student_acknowledged` (or `review_requested` at any point). Transitions defined in `domain.py:next_state_after_glass_evidence` and `next_state_after_stripe_payment`.

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `XCHANGE_DB_PATH` | No | `xchange.sqlite` |
| `XCHANGE_INGEST_TOKEN` | Yes (for ingest) | — |
| `STRIPE_WEBHOOK_SECRET` | Yes (for webhooks) | — |
| `XCHANGE_HOST` | No | `0.0.0.0` |
| `XCHANGE_PORT` | No | `8788` |
| `XCHANGE_STRIPE_TOLERANCE_SECONDS` | No | `300` |
| `XCHANGE_RATE_LIMIT_REQUESTS` | No | `60` |
| `XCHANGE_RATE_LIMIT_WINDOW_SECONDS` | No | `60` |
