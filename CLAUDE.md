# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is x-change

A reward-delivery service that accepts session telemetry (Glass sessions with failure snapshots), processes Stripe `payment_intent.succeeded` webhooks, and generates nudge records for students. Pure Python, stdlib `http.server`, SQLite storage, zero external dependencies.

## Run / Test / Lint

```bash
# Run the server
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
export XCHANGE_INGEST_TOKEN="dev-secret"
export STRIPE_WEBHOOK_SECRET="whsec_..."
PYTHONPATH="$PWD/src" python3 -m xchange
# Listens on 0.0.0.0:8788 by default (override: XCHANGE_HOST, XCHANGE_PORT)

# Run tests
PYTHONPATH="$PWD/src" python3 -m pytest tests/ -v

# Run a single test
PYTHONPATH="$PWD/src" python3 -m pytest tests/test_stripe_signature.py -v
```

No build step. No linter configured yet. No `pyproject.toml` — PYTHONPATH must include `src/`.

## Architecture

```
src/xchange/
  __main__.py   — entrypoint: reads env, calls run_server()
  main.py       — HTTP handler (stdlib BaseHTTPRequestHandler), routes, request parsing
  domain.py     — pure policy: RewardState lifecycle enum, transition functions (no I/O)
  storage.py    — SQLite schema + all DB operations (sessions, failures, rewards, nudges)
  stripe_sig.py — HMAC-SHA256 Stripe webhook signature verification (no Stripe SDK)
  nudge.py      — deterministic nudge text generation from failure commands
```

**Request flow:** HTTP request → `AppHandler` (main.py) → auth check → storage write → optional domain transition → response.

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
| POST | `/v0/stripe/webhook` | Stripe-Signature header | Process payment webhooks |
| GET | `/v0/state/reward/<reward_id>` | None | Query reward delivery state |

## SQLite Tables

`sessions`, `failures`, `rewards`, `nudges` — schema defined in `storage.py:SCHEMA_SQL`. Auto-created on first connection via `open_db()`.

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
