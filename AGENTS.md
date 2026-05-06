# AGENTS.md — x-change

## Run / Test

```bash
# Server (listens on 0.0.0.0:8788 by default)
PYTHONPATH="$PWD/src" uv run python -m xchange

# All tests
PYTHONPATH="$PWD/src" uv run python -m unittest discover -s tests -v

# Single test file
PYTHONPATH="$PWD/src" uv run python -m unittest tests.test_stripe_signature -v
```

`PYTHONPATH="$PWD/src"` is required — there is no `pip install` step; the package is run from source.

## Environment Variables

| Variable | Required | Default |
|----------|-----------|---------|
| `XCHANGE_DB_PATH` | No | `xchange.sqlite` |
| `XCHANGE_INGEST_TOKEN` | Yes (for ingest) | — |
| `STRIPE_WEBHOOK_SECRET` | Yes (for webhooks) | — |
| `XCHANGE_HOST` | No | `0.0.0.0` |
| `XCHANGE_PORT` | No | `8788` |
| `XCHANGE_STRIPE_TOLERANCE_SECONDS` | No | `300` |
| `XCHANGE_RATE_LIMIT_REQUESTS` | No | `60` |
| `XCHANGE_RATE_LIMIT_WINDOW_SECONDS` | No | `60` |
| `XCHANGE_MAX_BODY_BYTES` | No | `65536` |
| `XCHANGE_GRID_SUB_MAX_BYTES` | No | `65536` |

Missing `XCHANGE_INGEST_TOKEN` or `STRIPE_WEBHOOK_SECRET` causes requests to be rejected (fail-closed).

## Architecture

```
src/xchange/
  __main__.py   — entrypoint: reads env, calls run_server()
  main.py       — HTTP handler (stdlib BaseHTTPRequestHandler), routing, auth, rate limiting
  domain.py     — pure policy: RewardState lifecycle, transition functions (no I/O)
  storage.py    — SQLite schema + all DB operations
  glass_adapter.py — maps Glass bridge telemetry to ingest payload
  stripe_sig.py — HMAC-SHA256 Stripe signature verification (no Stripe SDK)
  nudge.py      — deterministic nudge text generation
```

**Request flow:** HTTP → `AppHandler` (main.py) → auth/rate-limit → storage read/write → optional domain transition → response

**Reward lifecycle:** `drafted` → `earned` → `payment_pending` → `payment_confirmed` → `student_acknowledged` (or `review_requested` at any point). Only `domain.py` rules advance state — raw evidence and Stripe JSON propose transitions, they don't bypass validation.

## Key Facts

- Pure Python, stdlib `http.server`, zero external dependencies (verify via `uv.lock`)
- `uv` manages the environment; `pyproject.toml` + `uv.lock` are intentional for reproducible local execution
- SQLite via `sqlite3` stdlib module; schema auto-created on first `open_db()` call
- `RewardToken` is x-change governance only — not related to signal-rate tokens elsewhere
- Stripe payment confirms funds movement, not educational outcome; student acknowledgement is a separate step
- Missing Stripe metadata emits support signals, never silently discards
- No linter or typechecker configured yet; `pyproject.toml` uses `setuptools`
- No build step; `python -m xchange` starts the server directly

## API Endpoints (v0)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/v0/ingest/glass-session` | Bearer/X-Ingest-Token | Store session + optional failure snapshot |
| POST | `/v0/ingest/glass-bridge` | Bearer/X-Ingest-Token | Map Glass bridge telemetry to ingest |
| POST | `/v0/stripe/webhook` | Stripe-Signature header | Process payment webhooks |
| POST | `/v0/tokens/issue` | Bearer/X-Ingest-Token | Issue epistemic token on a reward |
| POST | `/v0/exchange/request` | Bearer/X-Ingest-Token | Evaluate + store token exchange request |
| GET | `/v0/exchange/requests` | Bearer/X-Ingest-Token | List exchange requests (filters: student_id, reward_id, approved, limit) |
| POST | `/v0/rewards/draft` | Bearer/X-Ingest-Token | Create reward draft |
| GET | `/v0/state/reward/<reward_id>` | Bearer/X-Ingest-Token | Query reward state |
| POST | `/v0/rewards/<id>/acknowledge` | Bearer/X-Ingest-Token | Student acknowledgement |
| GET | `/v0/outcomes/summary` | Bearer/X-Ingest-Token | Aggregate reward counts by state |
| GET | `/v0/support-signals` | Bearer/X-Ingest-Token | List support signals |
| POST | `/v0/support-signals/<id>/resolve` | Bearer/X-Ingest-Token | Resolve support signal |
| GET | `/v0/scope/token/<reward_id>` | Bearer/X-Ingest-Token | Resolve token scope for a reward |
| GET | `/v0/scope/tool?provenance=<prov>` | Bearer/X-Ingest-Token | Resolve tool scope for a provenance |
| PATCH | `/v0/evidence/<id>` | Bearer/X-Ingest-Token | Retroactively link evidence to reward |

## See Also

- `CLAUDE.md` — full project instructions, architecture notes, and session guidelines
- `docs/policy-core-v0.md` — reward lifecycle policy rules
- `docs/glass-contract-v0.md` — Glass integration contract
- `docs/stripe-boundary.md` — Stripe integration boundary
- `docs/token-scope.md` — RewardToken scope characteristics and properties
- `docs/tool-scope.md` — Tool scope evidence model and validation
- `docs/scope-integration.md` — Token + Tool + Evidence integration model
