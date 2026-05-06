#!/bin/bash
# Smoke check for viewer sanitization on main branch
set -e

SMOKE_DB="xchange-smoke.sqlite"
PORT=8788
TOKEN="smoke-test-token-$(date +%s)"

export XCHANGE_DB_PATH="$SMOKE_DB"
export XCHANGE_INGEST_TOKEN="$TOKEN"
export STRIPE_WEBHOOK_SECRET="whsec_smoke_test"
export PYTHONPATH="$PWD/src"

echo "▶ Starting x-change server (port $PORT)..."
uv run python -m xchange &
SERVER_PID=$!
sleep 3

cleanup() {
    echo "▶ Stopping server (PID $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT

echo "▶ Creating reward draft with evidence..."
REWARD_ID=$(curl -s -X POST "http://localhost:$PORT/v0/rewards/draft" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reward_id": "smoke-reward-001",
    "student_id": "alice",
    "title": "Production Smoke Check",
    "description": "Viewer sanitization verification",
    "amount_cents": 1000,
    "currency": "usd",
    "evidence": [
      {
        "type": "screenshot",
        "description": "Internal evidence item",
        "payload": {
          "secret_field": "should be redacted",
          "stdout": "do not leak"
        }
      }
    ]
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['reward_id'])")

echo "▶ Reward created: $REWARD_ID"

echo "▶ Issuing token on reward..."
curl -s -X POST "http://localhost:$PORT/v0/tokens/issue" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reward_id": "'"$REWARD_ID"'",
    "insight_tier": "foundational",
    "struggle_depth": 0.6,
    "autonomy_coefficient": 0.8
  }' > /dev/null

echo "▶ Fetching viewer HTML..."
curl -s "http://localhost:$PORT/v0/viewer?reward_id=$REWARD_ID" \
  -H "Authorization: Bearer $TOKEN" > /tmp/viewer-smoke-check.html

echo "▶ Viewer HTML saved to /tmp/viewer-smoke-check.html"

# Also fetch JSON directly for verification
echo "▶ Fetching JSON state for comparison..."
curl -s "http://localhost:$PORT/v0/state/reward/$REWARD_ID" \
  -H "Authorization: Bearer $TOKEN" > /tmp/viewer-smoke-check.json

echo "▶ Verifying sanitization..."
python3 -c "
import sys, json
data = json.load(open('/tmp/viewer-smoke-check.json'))
print(json.dumps(data, indent=2))

# Verify sanitization
has_evidence = 'evidence' in data and isinstance(data['evidence'], list) and len(data['evidence']) > 0
if has_evidence:
    print('\n❌ FAIL: evidence array should be empty/sanitized', file=sys.stderr)
    sys.exit(1)
    
# Check HTML contains expected elements
html = open('/tmp/viewer-smoke-check.html').read()
if 'READ-ONLY' not in html:
    print('\n❌ FAIL: HTML missing READ-ONLY badge', file=sys.stderr)
    sys.exit(1)
if 'Reward Details' not in html:
    print('\n❌ FAIL: HTML missing reward panel', file=sys.stderr)
    sys.exit(1)
    
print('\n✓ PASS: State sanitized correctly')
print('✓ PASS: HTML viewer rendered')
"

echo "▶ Smoke check complete!"
