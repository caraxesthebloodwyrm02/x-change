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

## API Endpoints (v0)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v0/ingest/glass-session` | Bearer token or X-Ingest-Token | Store session + optional failure snapshot |
| POST | `/v0/ingest/glass-bridge` | Bearer token or X-Ingest-Token | Map caller-enriched Glass bridge telemetry into ingest |
| POST | `/v0/stripe/webhook` | Stripe-Signature header | Process payment webhooks |
| GET | `/v0/state/reward/<reward_id>` | Bearer token or X-Ingest-Token | Query reward delivery state |
| GET | `/v0/outcomes/summary` | Bearer token or X-Ingest-Token | Aggregate reward counts by state; optional `student_id` |
| GET | `/v0/support-signals` | Bearer token or X-Ingest-Token | List support signals |
| POST | `/v0/support-signals/<id>/resolve` | Bearer token or X-Ingest-Token | Resolve support signal |

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
