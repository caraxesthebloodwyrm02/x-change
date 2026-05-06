# Integration Spike: Glass Session → x-change Evidence

**Status:** Interface specification — spike complete. Typed payload trace, failure paths, operator dev loop, and Phase 4 tickets live in this doc; passive Glass tooling (no automated signal population yet) is explicit in §3.  
**Tied to:** `glass-contract-v0.md`, `policy-core-v0.md`  
**Spike date:** 2026-05-06

---

## What this document covers

1. Typed example payload — Glass `BridgeState` → x-change ingest JSON, field-by-field policy mapping
2. Failure paths — wrong token, missing `reward_id`, Stripe metadata mismatch
3. Signal challenge — what actually populates Glass `signals` today
4. Operator dev loop — copy-paste sequence to exercise the full pipe locally
5. Token rotation procedure

---

## 1. Trace: BridgeState → ingest payload

### Source: Glass bridge file (`~/.caraxes/field-bridge.json`)

Typed per `bridge/schema.ts:BridgeState`:

```json
{
  "timestamp": "2026-05-06T01:30:00.000Z",
  "session_id": "demo-20260506T0130-48e398de",
  "agent_state": "reviewing",
  "threshold_state": "ground",
  "progress": 0.0,
  "blocks": [],
  "conversation": [
    { "role": "agent", "text": "Tests green. 3 files changed.", "timestamp": "2026-05-06T01:29:55.000Z" }
  ],
  "voices": [],
  "signals": {
    "git_diff_lines": 42,
    "iteration_count": 7,
    "session_age_minutes": 18
  }
}
```

### Policy mapping (per `policy-core-v0.md`)

| Bridge field | Role in x-change | Policy disposition |
|---|---|---|
| `session_id` | Identifies the evidence row in `evidence_ledger.session_id` | Passed through. Required. |
| `agent_state` | Spatial telemetry stored verbatim in `_glass_bridge` | **Evidence only.** `reviewing` does NOT imply `request_review=true`. |
| `threshold_state` | Ceremony state stored verbatim in `_glass_bridge` | **Evidence only.** `elevated` does NOT imply `contract_satisfied=true`. |
| `progress` | Stored verbatim | **Evidence only.** `1.0` does NOT imply `ready_for_payment=true`. |
| `blocks`, `conversation`, `voices` | Stored verbatim | Evidence only — spatial artifacts, not policy inputs. |
| `signals.git_diff_lines` | Work intensity proxy, stored verbatim | Evidence only — not a reward metric. |
| `signals.iteration_count` | Tool call count proxy, stored verbatim | Evidence only. |
| `signals.session_age_minutes` | Session duration, stored verbatim | Evidence only. |

**No Glass field drives a reward transition.** All transition booleans (`contract_satisfied`, `ready_for_payment`, `request_review`) are **caller-supplied** enrichment, not inferred.

### Enriched ingest payload sent to `POST /v0/ingest/glass-bridge`

```json
{
  "student_id": "stu-abc123",
  "reward_id": "rwd-xyz789",
  "contract_satisfied": true,
  "bridge": {
    "timestamp": "2026-05-06T01:30:00.000Z",
    "session_id": "demo-20260506T0130-48e398de",
    "agent_state": "reviewing",
    "threshold_state": "ground",
    "progress": 0.0,
    "blocks": [],
    "conversation": [
      { "role": "agent", "text": "Tests green. 3 files changed.", "timestamp": "2026-05-06T01:29:55.000Z" }
    ],
    "voices": [],
    "signals": {
      "git_diff_lines": 42,
      "iteration_count": 7,
      "session_age_minutes": 18
    }
  }
}
```

The adapter (`glass_adapter.py:map_glass_bridge_to_ingest`) maps this to:

```json
{
  "session_id": "demo-20260506T0130-48e398de",
  "student_id": "stu-abc123",
  "reward_id": "rwd-xyz789",
  "contract_satisfied": true,
  "_glass_bridge": { "<full bridge state above>" }
}
```

This is then passed to `storage.py:ingest_glass_session`, which:
1. Writes a row to `sessions` (legacy mirror)
2. Appends a `glass_session_event` row to `evidence_ledger` with `provenance="glass_ingest"`
3. Calls `domain.py:next_state_after_glass_evidence` — if `contract_satisfied=true` and reward is `drafted`, transitions to `earned`
4. Returns `{ "ok": true, "evidence_recorded": true, "transition": { "new_state": "earned", ... } }`

### What x-change is allowed to infer

x-change MUST NOT infer any of these from Glass fields:
- Contract satisfaction from `threshold_state` or `progress`
- Payment readiness from any Glass field
- Student acknowledgement from any Glass field
- Review escalation from `agent_state`

These are **operator decisions** expressed as explicit booleans in the request body.

---

## 2. Failure paths

### Wrong token → 401

```bash
curl -X POST http://localhost:8788/v0/ingest/glass-session \
  -H "Authorization: Bearer wrong-token" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"s1","student_id":"stu1"}'
# → 401 {"error":"unauthorized"}
```

Both `/v0/ingest/glass-session` and `/v0/ingest/glass-bridge` check `_require_operator_access` before reading the body (`main.py:348`, `main.py:377`). No body is parsed on auth failure.

Missing `XCHANGE_INGEST_TOKEN` env var also returns 401 — the token check requires the env var to be set and matching (`main.py:64–75`).

### Missing `reward_id` — evidence-only path (not an error)

`reward_id` is optional on both endpoints. Omitting it records evidence without linking it to a reward row:

```json
{ "session_id": "s1", "student_id": "stu1" }
```

Result: `evidence_ledger` row written with `reward_id=NULL`. No reward state transition attempted. Returns `{ "ok": true, "evidence_recorded": true }` (no `transition` key).

This is correct behavior — operators may want to record session telemetry before they know which reward to associate. Wire up `reward_id` in a subsequent call or use `GET /v0/state/reward/<id>` to link later.

### Stripe metadata mismatch → support signal + HTTP 200

Stripe sends `payment_intent.succeeded` with missing or mismatched `metadata.reward_id` or `metadata.student_id`:

```json
{
  "id": "evt_missing_meta",
  "type": "payment_intent.succeeded",
  "data": { "object": { "id": "pi_abc", "metadata": {} } }
}
```

x-change:
- Emits a `support_signals` row with `kind="stripe_missing_metadata"` (or `"stripe_student_mismatch"`)
- Returns HTTP **200** to Stripe to prevent retry loops
- Does NOT mutate reward state

This is documented in `policy-core-v0.md:StripePaymentConfirmation` and tested in `test_validation_gate.py:test_support_path_on_missing_metadata`.

---

## 3. Signal challenge: what populates Glass signals today

**Current state (Glass PHASE3.md, W2):** Nothing populates `signals` from real data automatically.

The bridge schema defines three signal keys:
- `git_diff_lines` — intended: `git diff --stat` line count at each turn boundary
- `iteration_count` — intended: incremented per tool call or turn
- `session_age_minutes` — intended: elapsed time since `glass_session_start`

The `ModulationEngine` reads `thresholdState` and `progress` to produce ADSR → LFO → bus values. Signal heat feeds field intensity modulation (`signal-heat.ts`). The infrastructure is complete; the population step is not automated.

**Why automation is not yet wired:** Phase 3 shipped the infrastructure with a deliberate "passive" decision (PHASE3.md W1): agent calls tools when prompted, rather than hooks writing bridge state automatically. The risk of active automation is writing stale state when the agent is not actually using Glass. This is not a gap — it is an intentional boundary: operator or agent explicitly calls `glass_emit_turn({signals: {...}})` to update signals.

**Smallest truthful increment (Phase 4 candidate):** A `PostToolUse` hook that reads `git diff --stat` and calls `glass_emit_turn` with the updated `git_diff_lines` count. Acceptance test: `git_diff_lines` in the bridge file increases after a file edit tool call, and `ModulationEngine` produces a higher `ambientIntensity` bus value. **Not implemented in this spike.** Implementing it without the hook product surface (Claude Code `PostToolUse` hook writing to an MCP tool) would require the operator script to call `glass_emit_turn` manually, which is documented in the dev loop below.

---

## 4. Operator dev loop

Copy-paste sequence for local end-to-end testing. Replace placeholder values; **never commit secrets**.

```bash
# ── Terminal 1: start x-change ──────────────────────────────────────────────
cd /home/irfankabir/x-change
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
export XCHANGE_INGEST_TOKEN="dev-secret"            # NEVER COMMIT
export STRIPE_WEBHOOK_SECRET="whsec_devtest"        # NEVER COMMIT
export PYTHONPATH="$PWD/src"
uv run python -m xchange
# Listening on 0.0.0.0:8788

# ── Terminal 2: run dev loop ─────────────────────────────────────────────────

# 1. Draft a reward
curl -s -X POST http://localhost:8788/v0/rewards/draft \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d '{"reward_id":"rwd-dev-001","student_id":"stu-dev-001"}' | jq .

# 2. Simulate Glass session-init (what glass-server writes to the bridge)
#    This represents a real Glass bridge file snapshot.
BRIDGE_PAYLOAD='{
  "student_id": "stu-dev-001",
  "reward_id": "rwd-dev-001",
  "contract_satisfied": true,
  "bridge": {
    "session_id": "demo-20260506T0130-48e398de",
    "agent_state": "reviewing",
    "threshold_state": "ground",
    "progress": 0.0,
    "blocks": [],
    "conversation": [],
    "voices": [],
    "signals": { "git_diff_lines": 42, "iteration_count": 7, "session_age_minutes": 18 },
    "timestamp": "2026-05-06T01:30:00.000Z"
  }
}'

curl -s -X POST http://localhost:8788/v0/ingest/glass-bridge \
  -H "Authorization: Bearer dev-secret" \
  -H "Content-Type: application/json" \
  -d "$BRIDGE_PAYLOAD" | jq .
# Expected: {"ok":true,"evidence_recorded":true,"transition":{"new_state":"earned",...}}

# 3. Verify reward state
curl -s http://localhost:8788/v0/state/reward/rwd-dev-001 \
  -H "Authorization: Bearer dev-secret" | jq .state

# 4. Failure path: wrong token → 401
curl -s -X POST http://localhost:8788/v0/ingest/glass-bridge \
  -H "Authorization: Bearer wrong" \
  -H "Content-Type: application/json" \
  -d "$BRIDGE_PAYLOAD" | jq .error
# Expected: "unauthorized"

# 5. Run full test suite to confirm
cd /home/irfankabir/x-change
PYTHONPATH="$PWD/src" uv run python -m unittest discover -s tests -v
```

The script above is also available at `x-change/scripts/glass-session-init.sh`.

---

## 5. Token rotation

`XCHANGE_INGEST_TOKEN` is a single env var shared across all operator endpoints. There is no graceful in-process rotation in v0 — rotation requires:

1. Set new token value in the deployment environment (or `.env` file — **not committed**).
2. Restart the x-change server (`uv run python -m xchange`).
3. Update callers (Glass-side scripts, CI) to use the new token.
4. Invalidation is immediate on restart — old token is rejected before the first request.

**Phase 2 improvement candidate:** token-pairs with a grace window (old + new both valid during overlap). Not implemented. Workaround for zero-downtime rotation: use a reverse proxy (nginx/caddy) to proxy `/v0/ingest/*` and swap the upstream env after a rolling restart.

The Stripe webhook secret (`STRIPE_WEBHOOK_SECRET`) is rotated independently through the Stripe dashboard. The signature check is HMAC-SHA256 (`stripe_sig.py`); the old secret must remain valid until Stripe confirms the new key is active.

---

## 6. What shipped vs. deferred

| Item | Status |
|---|---|
| Field-by-field payload trace with policy mapping | Shipped (this doc) |
| Failure path: wrong token → 401 | Shipped (test in `test_http_boundaries.py`) |
| Failure path: missing `reward_id` documented as evidence-only | Shipped (this doc) |
| Failure path: Stripe mismatch → support signal | Existing test `test_validation_gate.py:test_support_path_on_missing_metadata` |
| Signal population from real git metrics | Deferred — `signals-pipeline.md` spec inline above; Phase 4 ticket |
| Operator dev loop script | Shipped (`scripts/glass-session-init.sh`) |
| Token rotation procedure | Shipped (this doc) |
| Glass-side automation (PostToolUse hook → `glass_emit_turn`) | Deferred — passive decision documented; Phase 4 |
| Bidirectional x-change → Glass write | Out of scope (one-directional per `glass-contract-v0.md`) |

---

## Phase 4 tickets (file-level pointers)

1. **Signal automation hook** — Add `PostToolUse` hook in `~/.claude/hooks/` that reads `git diff --stat` and calls `glass_emit_turn({signals: {git_diff_lines: N, iteration_count: N+1}})`. Acceptance: `bridge/schema.ts:BridgeSignals.git_diff_lines` updates within 500 ms of a file edit.

2. **Graceful token rotation** — `main.py:_require_ingest_token` to support two accepted tokens during overlap window. Config: `XCHANGE_INGEST_TOKEN_PREV` env var checked for 5 minutes after `XCHANGE_INGEST_TOKEN` changes.

3. **Evidence → reward linking** — Retroactive `reward_id` association for evidence rows recorded without a reward. Endpoint: `PATCH /v0/evidence/<id>` with `reward_id`. Required before team-scale use where session evidence arrives before reward is drafted.
