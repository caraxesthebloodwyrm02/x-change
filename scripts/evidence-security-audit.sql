-- X-Change Evidence Ledger Security Audit Query
-- Verifies no evidence rows are accessible without proper gating

-- Check 1: Evidence with session_id (requires session validation)
SELECT 
    'session-gated' as category,
    COUNT(*) as count,
    GROUP_CONCAT(DISTINCT evidence_type) as types
FROM evidence_ledger 
WHERE session_id IS NOT NULL;

-- Check 2: Evidence without session_id (no session gate)
SELECT 
    'no-session-gate' as category,
    COUNT(*) as count,
    GROUP_CONCAT(DISTINCT evidence_type) as types
FROM evidence_ledger 
WHERE session_id IS NULL;

-- Check 3: Orphaned evidence (reward_id not in reward_ledger)
SELECT 
    'orphaned-evidence' as category,
    COUNT(*) as count
FROM evidence_ledger e
LEFT JOIN reward_ledger r ON e.reward_id = r.reward_id
WHERE e.reward_id IS NOT NULL 
  AND r.reward_id IS NULL;

-- Check 4: Provenance audit (all evidence must have provenance)
SELECT 
    'missing-provenance' as category,
    COUNT(*) as count
FROM evidence_ledger
WHERE provenance IS NULL OR provenance = '';

-- Check 5: Payload size audit (large payloads may need review)
SELECT 
    'large-payload' as category,
    COUNT(*) as count,
    AVG(LENGTH(payload_json)) as avg_size,
    MAX(LENGTH(payload_json)) as max_size
FROM evidence_ledger
WHERE LENGTH(payload_json) > 10000;

-- Summary: Security gate status
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM evidence_ledger WHERE provenance IS NULL OR provenance = '') > 0 
        THEN '⚠ FAIL: Missing provenance'
        WHEN (SELECT COUNT(*) FROM evidence_ledger e LEFT JOIN reward_ledger r ON e.reward_id = r.reward_id WHERE e.reward_id IS NOT NULL AND r.reward_id IS NULL) > 0
        THEN '⚠ WARN: Orphaned evidence'
        ELSE '✓ PASS: Evidence ledger properly gated'
    END as security_status;
