# Circuit Close Runbook

Reproduce the Glass -> x-change evidence -> reward transition pipeline in under 10 minutes.

## Prerequisites

- Python 3.13+, `uv` installed
- x-change repo cloned (`/home/irfankabir/x-change` or equivalent)
- Scripts: `~/scripts/xchange-ingest-bridge.py`, `~/scripts/xchange-seed-circuit-close.py`, `~/scripts/xchange-circuit-close-proof.py`

## Steps

### 1. Start x-change

```bash
cd /path/to/x-change
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
export XCHANGE_INGEST_TOKEN="dev-secret"
export STRIPE_WEBHOOK_SECRET="whsec_test"
export PYTHONPATH="$PWD/src"
uv run python -m xchange
```

Verify: `curl -s http://localhost:8788/v0/outcomes/summary` returns JSON.

### 2. Seed PSC and reward

```bash
XCHANGE_DB_PATH=/path/to/xchange.sqlite python3 ~/scripts/xchange-seed-circuit-close.py
```

Creates `psc-circuit-close-001` (service contract) and `reward-circuit-close-001` (drafted state).

### 3. Produce a fresh Glass bridge snapshot

Either start a real Glass session, or write a fresh bridge file at `~/.caraxes/field-bridge.json` with a current timestamp and non-demo `session_id`. The bridge must contain at minimum: `timestamp`, `session_id`, `agent_state`, `signals`.

### 4. Ingest evidence (pre-attestation)

```bash
XCHANGE_INGEST_TOKEN=dev-secret python3 ~/scripts/xchange-ingest-bridge.py \
  --reward-id reward-circuit-close-001
```

Verify: response contains `"evidence_recorded": true`. Reward stays in `drafted` state.

Optional dry-run first: add `--dry-run` to inspect the payload without POSTing.

### 5. Attest (Gate 2 closure)

```bash
XCHANGE_INGEST_TOKEN=dev-secret python3 ~/scripts/xchange-ingest-bridge.py \
  --reward-id reward-circuit-close-001 --contract-satisfied
```

Verify: response contains `"transition": {"new_state": "earned", ...}` with note `contract_satisfied: drafted -> earned`.

### 6. Generate proof artifact

```bash
mkdir -p proofs
XCHANGE_INGEST_TOKEN=dev-secret python3 ~/scripts/xchange-circuit-close-proof.py \
  --output-dir proofs
```

Produces `circuit-close-proof.md` and `circuit-close-proof.json`. The script reports `PASS`, `PARTIAL`, or `NOT YET`.

### 7. Verify

Open `proofs/circuit-close-proof.md`. Checklist should show:

- [x] Live evidence (non-demo session)
- [x] No staleness bypass
- [x] Policy transition occurred (drafted -> earned)
- Transition reason: `contract_satisfied: drafted -> earned`

## Script reference

| Script | Purpose | Key flags |
|--------|---------|-----------|
| `xchange-ingest-bridge.py` | Read bridge, POST to x-change | `--reward-id`, `--contract-satisfied`, `--dry-run`, `--student-id` |
| `xchange-seed-circuit-close.py` | Create PSC + draft reward row | Env: `XCHANGE_DB_PATH` |
| `xchange-circuit-close-proof.py` | Generate proof from API state | `--output-dir`, `--reward-id` |

## Environment variables

| Variable | Default | Used by |
|----------|---------|---------|
| `XCHANGE_INGEST_TOKEN` | (required) | ingest + proof scripts |
| `XCHANGE_URL` | `http://localhost:8788` | ingest + proof scripts |
| `XCHANGE_DB_PATH` | `xchange.sqlite` | seed script, server |
| `BRIDGE_PATH` | `~/.caraxes/field-bridge.json` | ingest script |
| `BRIDGE_MAX_AGE_HOURS` | `6` | ingest script (staleness gate) |
