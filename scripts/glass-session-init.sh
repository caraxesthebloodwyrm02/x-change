#!/usr/bin/env bash
# glass-session-init.sh — dev loop: Glass bridge snapshot → x-change ingest
#
# Prerequisites:
#   - x-change running on localhost:8788 (see README "Run locally")
#   - XCHANGE_INGEST_TOKEN set to the same value as the server
#
# NEVER COMMIT credentials. Use a local .env file (gitignored) or export
# vars in your shell before running this script.
#
# Usage:
#   export XCHANGE_INGEST_TOKEN="dev-secret"
#   bash scripts/glass-session-init.sh [student_id] [reward_id]

set -euo pipefail

HOST="${XCHANGE_HOST:-localhost}"
PORT="${XCHANGE_PORT:-8788}"
TOKEN="${XCHANGE_INGEST_TOKEN:?XCHANGE_INGEST_TOKEN is required}"

STUDENT_ID="${1:-stu-dev-001}"
REWARD_ID="${2:-rwd-dev-001}"
SESSION_ID="dev-$(date +%Y%m%dT%H%M)-$(openssl rand -hex 4 2>/dev/null || echo 'xxxxxxxx')"

BASE="http://${HOST}:${PORT}"
AUTH="Authorization: Bearer ${TOKEN}"

echo "==> 1/4  Draft reward ${REWARD_ID} for student ${STUDENT_ID}"
curl -sf -X POST "${BASE}/v0/rewards/draft" \
  -H "${AUTH}" \
  -H "Content-Type: application/json" \
  -d "{\"reward_id\":\"${REWARD_ID}\",\"student_id\":\"${STUDENT_ID}\"}" | jq . || true

echo ""
echo "==> 2/4  Ingest Glass bridge snapshot (session ${SESSION_ID})"
BRIDGE_PAYLOAD="$(cat <<EOF
{
  "student_id": "${STUDENT_ID}",
  "reward_id": "${REWARD_ID}",
  "contract_satisfied": true,
  "bridge": {
    "session_id": "${SESSION_ID}",
    "agent_state": "reviewing",
    "threshold_state": "ground",
    "progress": 0.0,
    "blocks": [],
    "conversation": [],
    "voices": [],
    "signals": { "git_diff_lines": 42, "iteration_count": 7, "session_age_minutes": 18 },
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
  }
}
EOF
)"

curl -sf -X POST "${BASE}/v0/ingest/glass-bridge" \
  -H "${AUTH}" \
  -H "Content-Type: application/json" \
  -d "${BRIDGE_PAYLOAD}" | jq .

echo ""
echo "==> 3/4  Verify reward state"
curl -sf "${BASE}/v0/state/reward/${REWARD_ID}" \
  -H "${AUTH}" | jq '{reward_id, state, outcome_state}'

echo ""
echo "==> 4/4  Failure path: wrong token → expect 401"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${BASE}/v0/ingest/glass-bridge" \
  -H "Authorization: Bearer wrong-token" \
  -H "Content-Type: application/json" \
  -d '{}')
if [ "${STATUS}" = "401" ]; then
  echo "    PASS: got 401 for wrong token"
else
  echo "    FAIL: expected 401, got ${STATUS}"
  exit 1
fi

echo ""
echo "Done. Reward ${REWARD_ID} should be in state 'earned'."
echo "Run 'uv run python -m unittest discover -s tests -v' to confirm all tests pass."
