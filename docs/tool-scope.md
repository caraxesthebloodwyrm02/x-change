# Tool Scope — Organic Definition for x-change v0

**Document date:** 2026-05-07  
**Tied to:** `policy-core-v0.md`, `glass-contract-v0.md`, `token-scope.md`  
**Philosophy:** Tools are evidence sources with observable state, not abstract categories.

---

## TL;DR — What this document covers

1. **Tool scope** — what *tool* means in this ecosystem (Glass, GRID, Calculator)  
2. **Tool evidence** — how tools generate `EvidenceType` rows and `provenance` strings  
3. **Tool→Reward linkage** — no auto-inference, all linkage via explicit reward_id  
4. **Scope validation** — how to ensure tools don’t exceed their boundaries  

---

## 1. Tool Scope: What *is* a tool?

A **tool** is an *observable operation* that:

1. Produces state (Glass `BridgeState`, GRID `grid_substantiation`, Calculator outputs)  
2. Leaves evidence (writes to `evidence_ledger` with `provenance` string)  
3. Can propose reward transitions (via explicit booleans: `contract_satisfied`, `ready_for_payment`, etc.)

### Tool is not...

- **Not a domain entity** — tools don’t have rows in `reward_ledger`, `tool_scopes`, etc.  
- **Not a token** — tools don’t carry `insight_tier`, `rarity_score`, `amount`  
- **Not a state machine** — tools operate *within* the reward state machine  

### Tool *is*...

- **An evidence generator** — each tool call can produce evidence rows  
- **A context carrier** — tool state captured in `payload_json` (Glass `bridge`, GRID `substantiation`)  
- **A trigger** — tool outcomes propose reward state transitions via `ingest_bool()`  

---

## 2. Tool Sources (v0)

### 2.1 Glass

**File:** `glass_adapter.py`, `INTEGRATION-SPIKE.md`  
**Evidence type:** `EvidenceType.GLASS_SESSION_EVENT`  
**Provenance:** `"glass_ingest"`  
**Tool state:** `bridge/schema.ts::BridgeState` (session_id, agent_state, threshold_state, signals, etc.)  

Glass tools produce:
- Session events → evidence rows  
- Failure snapshots → evidence rows  
- **No automatic transition** — explicit booleans required  

### 2.2 GRID

**File:** `grid_substantiation.py`  
**Evidence type:** `EvidenceType.AGENT_INTERPRETATION` (provisional)  
**Provenance:** `"grid_substantiation"`  
**Tool state:** `grid_substantiation` object (version, captured_at, source, summary, workspace_roots, repo_fingerprints)  

 GRID tools produce:
- Substantiation records → evidence rows  
- Workspace/health/momentum signals → context for reward evaluation  
- **No automatic transition** — explicit booleans required  

### 2.3 Calculator

**File:** `tools/calculator/`  
**Evidence type:** N/A (Calculator is a *consumer*, not evidence source)  
**Provenance:** N/A  
**Tool state:** Excel workbook + Python build scripts  

Calculator is a **token scope tool** — it operates *on* RewardToken, not *as* a reward trigger.

---

## 3. Tool Evidence Model

### Evidence schema (per `EvidenceType`)

| EvidenceType | Typical source | Provenance | Payload keys |  
|---|---|---|---|  
| `glass_session_event` | Glass bridge → `ingest_glass_session()` | `"glass_ingest"` | `session_id`, `student_id`, `reward_id`, `_glass_bridge`, `contract_satisfied`, `ready_for_payment`, etc. |  
| `failure_snapshot` | Failure记录 | `"fail_snapshot"` | `command`, `exit_code`, `stdout`, `stderr`, `payload` |  
| `agent_interpretation` | GRID/Glass interpretation | `"agent_interp"` | `summary`, `rationale`, `confidence`, `substantiation` |  
| `student_confirmation` | Student API call | `"student_ack"` | `student_id`, `reward_id`, `acknowledged_at` |  
| `return_attempt` | Retry markers | `"retry"` | `attempt_id`, `previous_evidence_id`, `reason` |  
| `success_after_support` | Support follow-up | `"success_after_support"` | `support_id`, `resolution`, `outcome` |  

### Provenance rules (v0)

- **Provenance is not an enum** — it’s a free-form string  
- **Provenance must be non-empty** — enforced by `append_evidence()`  
- **Provenance links to tool source** — `"glass_ingest"`, `"grid_substantiation"`, `"student_ack"`, etc.  

---

## 4. Tool→Reward Linkage Model

### No auto-inference rule

From `glass-contract-v0.md:Design rule: no auto-inference`:

> `threshold_state=elevated` does NOT imply `contract_satisfied=true`  
> `progress=1.0` does NOT imply `ready_for_payment=true`  
> `agent_state=reviewing` does NOT imply `request_review=true`

### Organic linkage pattern

```
Tool call (Glass/GRID/Calculator)
     ↓
Ingest payload (explicit booleans)
     ↓
Evidence row (evidence_ledger)
     ↓
Reward row (reward_ledger) ← linked via reward_id
     ↓
Reward tokens (reward_token_json)
```

### Linkage via reward_id

```python
# Evidence can be recorded without reward_id (optional)
append_evidence(
    student_id="stu-123",
    session_id="sess-456",
    reward_id=None,  # ← optional
    evidence_type=EvidenceType.GLASS_SESSION_EVENT,
    payload={"contract_satisfied": True},
    provenance="glass_ingest"
)

# Later, link evidence to reward via PATCH
patch_evidence_reward_id(evidence_id=123, reward_id="rwd-789")
```

**Result:** Scope linkage is *implicit* via reward_id, not explicit via tool-token mapping table.

---

## 5. Tool Scope Validation

### Validation rules (v0)

| Rule | Description | Code reference |  
|---|---|---|  
| **EvidenceType whitelist** | Only six evidence types allowed | `EvidenceType` enum in `domain.py` |  
| **Provenance non-empty** | Must be a non-empty string | `append_evidence()` validation |  
| **Payload size bound** | `XCHANGE_GRID_SUB_MAX_BYTES` env var | `_grid_substantiation_max_bytes()` |  
| **No auto-inference** | Tool state ≠ policy booleans | `ingest_bool()` only reads explicit keys |  
| **Reward linkage** | `reward_id` optional, can be patched later | `PATCH /v0/evidence/<id>` endpoint |  

### Validation gate

```python
def ingest_glass_session(conn, payload):
    # 1. Check evidence_type (implicit: glass_session_event)
    # 2. Check provenance (implicit: "glass_ingest")
    # 3. Read explicit booleans only
    if ingest_bool(payload, "request_review"):
        return transition_to_review()
    if ingest_bool(payload, "contract_satisfied"):
        return transition_to_earned()
    # ...
```

**No pre-declared “tool scope enum”** — validation is schema-based and type-checked.

---

## 6. Tool-Specific Constraints

### Glass constraints

| Constraint | Reason |  
|---|---|  
| `student_id` required | Glass has no student concept |  
| `contract_satisfied` must be explicit | Cannot infer from `threshold_state` or `progress` |  
| `ready_for_payment` must be explicit | Cannot infer from `progress=1.0` |  
| `failure` optional | Evidence-only; no transition |  

### GRID constraints

| Constraint | Reason |  
|---|---|  
| `version="v1"` | Schema version check |  
| `captured_at` ISO8601 | Time domain |  
| `workspace_roots` max 32 | Size bound |  
| `repo_fingerprints` max 50 | Size bound |  

### Calculator constraints

| Constraint | Reason |  
|---|---|  
| N/A | Calculator is a consumer, not an evidence source |  

---

## 7. Deferred — not v0

| Item | Reason |  
|---|---|  
| **Tool type enum** | `EvidenceType` covers evidence sources; `agent_state`/`threshold_state` are Glass-side |  
| **Tool-to-reward mapping table** | Scope linkage via `reward_id` is sufficient |  
| **Tool state sync** | GRID, Glass, x-change operate independently per `stripe-boundary.md` |  

---

## 8. Plain-language summary

- **Tool scope** is *what* triggers rewards (Glass sessions, GRID operations, Calculator outputs)  
- **Tool evidence** is *how* tools leave traces (provenance strings, EvidenceType rows)  
- **Tool→Reward linkage** is *how* they connect (via `reward_id`, not auto-inference)  
- **Validation** is *how* boundaries are enforced (schema, types, explicit booleans only)  

No pre-declared “tool scope enum”. Tools are evidence sources with observable state, constrained by schema and type checks.

---

## 9. References

- `docs/policy-core-v0.md` — canonical reward lifecycle  
- `docs/glass-contract-v0.md` — Glass → x-change data boundary  
- `INTEGRATION-SPIKE.md` — typed payload trace and failure paths  
- `src/xchange/glass_adapter.py` — Glass schema mapping  
- `src/xchange/grid_substantiation.py` — GRID validation and normalization  
- `src/xchange/storage.py` — evidence ledger operations  
- `docs/token-scope.md` — RewardToken characteristics and properties  
