# Token Scope — Organic Definition for x-change v0

**Document date:** 2026-05-07  
**Tied to:** `policy-core-v0.md`, `glass-contract-v0.md`, `grid-substantiation.md` (proposed)  
**Philosophy:** Scope emerges from usage context, not pre-declared boundaries.

---

## TL;DR — What this document covers

1. **Token scope** — what *RewardToken* can represent, how it relates to rewards, tools, and evidence  
2. **Tool scope** — what *tool* means in this ecosystem, how it differs from token  
3. **Scope linkage** — how tokens and tools connect organically through usage patterns  
4. **Validation gate** — how to enforce boundaries without pre-defining a closed set  

We define scope *after* observing existing patterns; no “scope enum” that must be extended.

---

## 1. Token Scope: What is a RewardToken *for*?

Per `policy-core-v0.md`, `RewardToken` is:

- **x-change governance unit** — internal ledger token, not signal-rate tokens elsewhere  
- **epistemic credential** —证明 of cognitive work, insight, or educational outcome  
- **issued per reward** — one reward row → one or many tokens (v0 default: 1)  
- **immutable after issuance** — `rarity_score` stamped and never recalculated  

### Token is not...

- **Not a currency** — not traded externally, not exchanged for money  
- **Not a signal** — not counted toward Glass or GRID thresholds  
- **Not a license** — does not grant API access, quota, or rate limits  

### Token *is*...

- **A certificate** — signed by the policy layer, stored in the ledger  
- **An evidence anchor** — links evidence rows to a reward outcome  
- **A scope handle** — can be exchanged for *value scopes* (see `domain.py:ExchangeRequest`)  
- **A classification** — `InsightTier` captures epistemic depth  

---

## 2. Tool Scope: What is a *tool* in this ecosystem?

**Tool** is not defined in `domain.py`. We infer it from context:

| Context | What *tool* means | Evidence |  
|---|---|---|  
| **Glass** | `agent_state` values (`idle`, `thinking`, `writing`, `reviewing`, `elevated`) | `bridge/schema.ts`, `field-bridge.json` |  
| **GRID** | Workspace state operations (`health`, `trust`, `drift`, `fail`, `momentum`) | `grid_substantiation.py::normalize_grid_substantiation_evidence` |  
| **x-change** | Calculator `build_calculator.py`, export scripts, API endpoints | `tools/calculator/`, `src/xchange/` |  

### Tool characteristics (v0)

| Characteristic | Meaning | Example |  
|---|---|---|  
| **Stateful** | Has observable state that changes over time | `agent_state: thinking → writing` |  
| **Traceable** | Leaves evidence rows in `evidence_ledger` | `glass_session_event`, `failure_snapshot` |  
| **Auditable** | Has provenance string and timestamp | `provenance=\"glass_ingest\"` |  
| **Non-inferable** | Cannot derive policy booleans from tool state alone | `threshold_state=elevated` ≠ `contract_satisfied=true` |  

### Tool is not...

- **Not a reward** — tools trigger rewards, but are not rewards themselves  
- **Not a token** — tools don’t carry `InsightTier`, `rarity_score`, or `amount`  
- **Not a state machine** — tools operate *within* the reward state machine  

### Tool *is*...

- **An evidence source** — each tool call can generate an evidence row  
- **A trigger** — tool success/failure can propose reward state transitions  
- **A context container** — `bridge` data carries tool state verbatim  

---

## 3. Scope Linkage: How tokens and tools connect

The linkage is **organic**, not pre-declared:

```
Tool (Glass/GRID/Calculator)
     ↓
Evidence Row (evidence_ledger)
     ↓
Reward Row (reward_ledger)
     ↓
Reward Token(s) (reward_token_json column)
```

### Linkage pattern (v0)

1. **Tool call** → generates evidence row with `provenance=\"...\"`  
2. **Evidence processing** → calls `next_state_after_glass_evidence()` → proposes reward transition  
3. **Reward approval** → `apply_evidence_to_reward()` writes new reward row  
4. **Token issuance** → `issue_reward_token()` stamps token into reward row  

**No explicit token-tool mapping table** — linkage is via `reward_id` in the ledger.

### Organic scope boundaries

| Boundary | How it emerges |  
|---|---|  
| **Token scope** | Defined by `InsightTier`, `rarity_score`, `amount` and exchange constraints |  
| **Tool scope** | Defined by `EvidenceType`, `provenance`, and ingest payload keys |  
| **Linkage** | Emerges via shared `reward_id` in reward → token → evidence chain |  

---

## 4. Validation Gate: Enforce boundaries organically

### Rule: No auto-inference

From `glass-contract-v0.md:Design rule: no auto-inference`:

> The adapter **MUST NOT** infer policy booleans from Glass state.

This extends to tool scope: **Tool state does not imply reward state**.

### Validation patterns (v0)

| Validation target | Pattern | Code reference |  
|---|---|---|  
| **Ingest token** | Check `XCHANGE_INGEST_TOKEN` or `X-Ingest-Token` header | `_require_operator_access()` in `main.py` |  
| **Token scope** | `RewardToken` must have valid `InsightTier` and `amount` derived from tier | `compute_rarity_score()`, `RewardToken.amount` property |  
| **Tool evidence** | `EvidenceType` must be one of the six defined | `EvidenceType` enum in `domain.py` |  
| **Provenance** | `provenance` must be a non-empty string | `append_evidence()` validates |  
| **Tool→Reward linkage** | `reward_id` optional on evidence → reward linking via `PATCH /v0/evidence/<id>` | `patch_evidence_reward_id()` |  

### Organic enforcement

We enforce boundaries by **schema and type**, not by pre-declaring a “scope enum”:

```python
# Token scope: only these tiers are valid
class InsightTier(StrEnum):
    SURFACE = "surface"
    PATTERN = "pattern"
    STRUCTURAL = "structural"
    CAUSAL = "causal"
    THEORETICAL = "theoretical"

# Tool evidence: only these types are valid
class EvidenceType(StrEnum):
    GLASS_SESSION_EVENT = "glass_session_event"
    FAILURE_SNAPSHOT = "failure_snapshot"
    RETURN_ATTEMPT = "return_attempt"
    SUCCESS_AFTER_SUPPORT = "success_after_support"
    AGENT_INTERPRETATION = "agent_interpretation"
    STUDENT_CONFIRMATION = "student_confirmation"

# Tool→Reward linkage: via reward_id, not auto-inference
def ingest_bool(payload: dict[str, Any], key: str) -> bool:
    # Only explicit booleans drive transitions
    ...
```

---

## 5. Deferred — not v0

| Item | Reason |  
|---|---|  
| **Token-tool mapping table** | Scope linkage via `reward_id` is sufficient; explicit mapping adds complexity |  
| **Tool scope enum** | `EvidenceType` covers evidence sources; `agent_state`/`threshold_state` are Glass-side |  
| **Cross-system tool sync** | GRID, Glass, x-change operate independently per `stripe-boundary.md` |  

---

## 6. Plain-language summary

- **Token scope** is *what* gets issued (epistemic credentials with tiers, rarity, exchangeability)  
- **Tool scope** is *what* triggers issuance (Glass sessions, GRID operations, Calculator operations)  
- **Linkage** is *how* they connect (via `reward_id` in the ledger, not explicit mapping)  
- **Validation** is *how* boundaries are enforced (schema, types, no auto-inference)  

No pre-declared “scope” list. Scope emerges from usage patterns and policy constraints.

---

## 7. References

- `docs/policy-core-v0.md` — canonical reward lifecycle  
- `docs/glass-contract-v0.md` — Glass → x-change data boundary  
- `INTEGRATION-SPIKE.md` — typed payload trace and failure paths  
- `src/xchange/domain.py` — `RewardToken`, `EvidenceType`, `InsightTier`  
- `src/xchange/storage.py` — ledger operations, evidence append  
- `tools/calculator/` — token calculator (rarity, exchange, scope)  
