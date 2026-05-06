# Scope Integration — Token + Tool + Evidence for x-change v0

**Document date:** 2026-05-07
**Tied to:** `policy-core-v0.md`, `glass-contract-v0.md`, `token-scope.md`, `tool-scope.md`
**Purpose:** Define how tokens, tools, and evidence integrate organically.

---

## 1. Integration Model

Data flow:

```
Tool Sources (Glass, GRID, Calculator)
        |
  Ingest / Adapter Layer
        |
  Evidence Ledger (evidence_ledger)
        |
  Reward Ledger (reward_ledger)
        |
  Token Scope (InsightTier, RarityScore, Exchange)
```

Scope is *emergent*, not pre-declared.

| Scope | How it emerges |
|---|---|
| Token scope | InsightTier enum, rarity_score, exchange constraint layers |
| Tool scope | EvidenceType enum, provenance strings, ingest payload schema |
| Linkage | Shared reward_id in ledger; no explicit tool-token mapping |

---

## 2. Linkage Patterns

### Token -> Reward

- One reward can emit one or many tokens (v0 default: 1)
- Token emitted at reward approval, not at draft
- Token attributes: insight_tier, rarity_score, amount, issued_at

### Reward -> Evidence

- Evidence recorded with optional reward_id
- Retroactive linking via PATCH /v0/evidence/<id>
- No implicit reward_id injection

### Tool -> Reward

- Tool state does NOT imply reward state (no auto-inference)
- Transition booleans must be explicit in ingest payload
- contract_satisfied -> drafted -> earned
- ready_for_payment -> earned -> payment_pending
- request_review -> any -> review_requested

### Tool -> Token (indirect)

Tools influence tokens through rewards. No direct tool-token mapping needed.

---

## 3. Payload Trace Examples

### 3.1 Glass Session

1. Glass bridge writes field-bridge.json
2. Ingest call: POST /v0/ingest/glass-bridge with student_id, reward_id, contract_satisfied, bridge payload
3. Evidence row written: evidence_type=glass_session_event, provenance=glass_ingest
4. Reward transition: drafted -> earned (if contract_satisfied=true)
5. Token issuance: RewardToken stamped with insight_tier, rarity_score, amount

### 3.2 GRID Substantiation

1. GRID health check produces substantiation payload (version v1, source, summary, fingerprints)
2. Ingest call: POST /v0/ingest/glass-session with _grid_substantiation attachment
3. Evidence row written: evidence_type=agent_interpretation, provenance=grid_substantiation
4. Same reward transition and token issuance path

### 3.3 Calculator (token scope only)

1. Calculator reads token data from SQLite or CSV
2. Generates xchange_reward_token_calculator.xlsx
3. Calculator is a consumer, not an evidence source
4. No reward linkage -- operates on existing tokens

---

## 4. Validation Pattern

| Check | Pattern | Code reference |
|---|---|---|
| EvidenceType | Enum, exactly 6 types | domain.py:EvidenceType |
| InsightTier | Enum, 5 tiers | domain.py:InsightTier |
| Rarity score | Computed, clamped [0.0, 1.0], 4dp | domain.py:compute_rarity_score() |
| No auto-inference | Always read explicit booleans via ingest_bool() | domain.py:ingest_bool() |
| Reward linkage | reward_id optional, patched later if needed | storage.py:patch_evidence_reward_id() |
| Exchange constraints | 3-layer evaluation | domain.py:evaluate_exchange_request() |
| Payload size | XCHANGE_GRID_SUB_MAX_BYTES env var | grid_substantiation.py |

---

## 5. Adding New Tools (organic)

No scope enum to extend. New tools just need:

1. New EvidenceType value (if needed) or reuse existing
2. New provenance string (free-form, non-empty)
3. New ingest handler in main.py
4. Explicit boolean transitions -- no auto-inference

Example: adding a custom tool

```python
# Step 1: Add evidence type (only if existing ones don't fit)
class EvidenceType(StrEnum):
    CUSTOM_EVENT = "custom_event"

# Step 2: Ingest handler
def ingest_custom_event(conn, payload):
    append_evidence(
        student_id=payload["student_id"],
        reward_id=payload.get("reward_id"),
        evidence_type=EvidenceType.CUSTOM_EVENT,
        payload=payload,
        provenance="custom_event"
    )
```

No schema migration, no mapping table, no scope enum.

---

## 6. Deferred (not v0)

- Tool scope enum -- EvidenceType + provenance sufficient
- Token-tool mapping table -- reward_id linkage sufficient
- Cross-system tool sync -- independent operations per stripe-boundary.md

---

## References

- docs/policy-core-v0.md
- docs/glass-contract-v0.md
- docs/token-scope.md
- docs/tool-scope.md
- src/xchange/domain.py
- src/xchange/storage.py
- src/xchange/glass_adapter.py
- src/xchange/grid_substantiation.py