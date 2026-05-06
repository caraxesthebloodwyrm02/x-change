# USEB Local Runbook

## What USEB Is

Unified Session Evidence Bundle is a session-close evidence package. It records Glass session state and GRID readiness state together so x-change can audit the context around a reward decision.

## What USEB Is Not

- USEB does not authorize payout.
- USEB does not infer contract completion.
- USEB does not infer student acknowledgement.
- USEB does not replace policy attestation.

## Operator Ingest Checklist

Before executing `useb_bundle.py --submit`, an operator **must** verify:

1. [ ] **Bridge Freshness**: Confirm `~/.caraxes/field-bridge.json` is recent. Run with `--max-bridge-age-seconds 300` to enforce freshness.
2. [ ] **Explicit Booleans**: Ensure `--contract-satisfied` or `--ready-for-payment` are explicitly passed **only** if the reward lifecycle policy warrants it. (Never assume these from bridge state).
3. [ ] **GRID Substantiation**: Attach `--grid-lumos-path` or `--seeds-snapshot-path` as `_grid_substantiation` for evidence-only archival. (This does *not* auto-advance state).

## Prerequisites

- x-change checkout at `/home/irfankabir/x-change`
- `uv` available
- Fresh Glass bridge JSON at `~/.caraxes/field-bridge.json` or a path passed with `--bridge-path`
- GRID Lumos JSON or Seeds snapshot JSON
- `XCHANGE_INGEST_TOKEN` set in the shell running the submitter

## Start x-change

```bash
cd /home/irfankabir/x-change
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
export XCHANGE_INGEST_TOKEN="dev-secret"
export STRIPE_WEBHOOK_SECRET="whsec_test"
export PYTHONPATH="$PWD/src"
uv run python -m xchange
```

## Build Bundle Only

```bash
cd /home/irfankabir/x-change
PYTHONPATH="$PWD/src" uv run python scripts/useb_bundle.py \
  --student-id stu-1 \
  --reward-id rwd-1 \
  --grid-lumos-path /path/to/lumos-result.json
```

If no Lumos output exists, pass `--seeds-snapshot-path /path/to/snapshot.json`. If omitted, the script tries the latest `~/.seeds-server/snapshots/snapshot-*.json`.

## Submit Bundle

```bash
cd /home/irfankabir/x-change
XCHANGE_INGEST_TOKEN="dev-secret" PYTHONPATH="$PWD/src" uv run python scripts/useb_bundle.py \
  --student-id stu-1 \
  --reward-id rwd-1 \
  --submit \
  --receipt
```

Expected receipt:

```json
{
  "bundle_hash": "sha256:...",
  "evidence_recorded": true,
  "ok": true,
  "session_id": "glass-session-1",
  "transition": null
}
```

## Expected Failure Path

Stale bridge snapshots fail closed:

```bash
PYTHONPATH="$PWD/src" uv run python scripts/useb_bundle.py \
  --student-id stu-1 \
  --max-bridge-age-seconds 300
```

Expected stderr:

```text
Bridge stale: age 1480s > max 300s. Refuse submission unless --allow-stale is set.
```

Use `--allow-stale` only for deliberate inspection or replay.

## Policy Check

After submission, query reward state:

```bash
curl -s \
  -H "Authorization: Bearer dev-secret" \
  http://127.0.0.1:8788/v0/state/reward/rwd-1
```

Evidence payload should include `_glass_bridge` and `_grid_substantiation`. Reward state changes only when explicit booleans such as `--contract-satisfied` or `--ready-for-payment` are passed and existing domain rules allow the transition.
