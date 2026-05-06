# Viewer Sanitization Production Smoke Check

**Date**: 2026-05-06  
**Branch**: main  
**Commit**: 5e36e6b  
**PR**: #2 (merged)

## Test Execution

```bash
PYTHONPATH="$PWD/src" uv run python -m xchange &
# Server started on port 8788

# Created test reward with internal evidence
curl -X POST http://localhost:8788/v0/rewards/draft \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "reward_id": "smoke-reward-001",
    "student_id": "alice",
    "evidence": [{
      "type": "screenshot",
      "payload": {"secret_field": "should be redacted"}
    }]
  }'

# Fetched viewer HTML
curl http://localhost:8788/v0/viewer?reward_id=smoke-reward-001 \
  -H "Authorization: Bearer $TOKEN"

# Fetched JSON state
curl http://localhost:8788/v0/state/reward/smoke-reward-001 \
  -H "Authorization: Bearer $TOKEN"
```

## Verification Results

### ✓ PASS: State Sanitization
```json
{
  "reward_id": "smoke-reward-001",
  "evidence": [],           // ✓ Empty (internal evidence removed)
  "payment_confirmations": [],
  "state": "drafted",
  "outcome_state": "unknown"
}
```

**Key Observations**:
- Internal `evidence[]` array sanitized (empty in collaborator view)
- Sensitive payload fields not exposed
- Core state fields present (reward_id, state, outcome_state)

### ✓ PASS: HTML Viewer Render
- **READ-ONLY badge**: Present
- **Trust Signal panel**: Rendered with lifecycle + outcome
- **Reward Details panel**: Shows student_id, reward_id, timestamps
- **Outcomes Snapshot**: Aggregate counts visible
- **Field Guide**: Educational context included

### Security Boundary Confirmed
- Operator auth required (ingest token check enforced)
- No write operations exposed via viewer
- Evidence payloads never serialized to collaborator-facing JSON

## Artifacts

- **HTML**: `docs/viewer-smoke-check-main.html`
- **JSON**: `docs/viewer-smoke-check-main.json`

## Next: Operator Feedback Collection

Open GitHub issue to gather first impressions:
- Label clarity (lifecycle vs outcome)
- Trust signal usefulness
- Additional context needs
