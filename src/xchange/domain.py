"""Pure domain types and reward transition rules for x-change v0.

No I/O, no framework imports — policy logic only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Final


class RewardState(StrEnum):
  """Canonical reward lifecycle states (policy-core-v0)."""

  DRAFTED = "drafted"
  EARNED = "earned"
  PAYMENT_PENDING = "payment_pending"
  PAYMENT_CONFIRMED = "payment_confirmed"
  STUDENT_ACKNOWLEDGED = "student_acknowledged"
  REVIEW_REQUESTED = "review_requested"


class EvidenceType(StrEnum):
  GLASS_SESSION_EVENT = "glass_session_event"
  FAILURE_SNAPSHOT = "failure_snapshot"
  RETURN_ATTEMPT = "return_attempt"
  SUCCESS_AFTER_SUPPORT = "success_after_support"
  AGENT_INTERPRETATION = "agent_interpretation"
  STUDENT_CONFIRMATION = "student_confirmation"


class PaymentConfirmationStatus(StrEnum):
  RECEIVED = "received"
  APPLIED = "applied"
  DUPLICATE_IGNORED = "duplicate_ignored"
  NOT_APPLIED_MISMATCH = "not_applied_mismatch"


class OutcomeState(StrEnum):
  UNKNOWN = "unknown"
  DELIVERED_PENDING_ACK = "delivered_pending_ack"
  ACKNOWLEDGED = "acknowledged"
  REVIEW_OPEN = "review_open"


class InsightTier(StrEnum):
  """Epistemic classification tier for a RewardToken.

  Ordered from least to most cognitively demanding.
  """

  SURFACE = "surface"           # Fact recall, basic recognition
  PATTERN = "pattern"           # Cross-domain pattern recognition
  STRUCTURAL = "structural"     # Structural understanding, system maps
  CAUSAL = "causal"             # Causal chain modelling, root cause
  THEORETICAL = "theoretical"   # Novel synthesis, theory building


class ConstraintLayer(StrEnum):
  """Exchange constraint evaluation layers, applied in order."""

  SAFETY_SECURITY = "safety_security"
  ETHICS_IRREVERSIBILITY = "ethics_irreversibility"
  ECONOMIC_STABILITY = "economic_stability"


class ToolProvenance(StrEnum):
  """Known tool provenance strings — not a closed set; new tools add new values.

  This enum documents the *currently known* provenance strings.
  Storage and ingest do NOT reject unknown provenance — new tools are
  free to introduce new provenance strings organically.
  """

  GLASS_INGEST = "glass_ingest"
  GRID_SUBSTANTIATION = "grid_substantiation"
  STUDENT_ACK = "student_ack"
  FAIL_SNAPSHOT = "fail_snapshot"
  AGENT_INTERP = "agent_interp"
  CALCULATOR = "calculator"


@dataclass(frozen=True)
class TokenScope:
  """Organic scope descriptor for a RewardToken.

  Emerges from the token's properties at issuance time — not pre-declared.
  Captures what the token *is for* based on its tier, trigger, and evidence.
  """

  insight_tier: InsightTier
  rarity_band: str               # "very_rare" / "rare" / "uncommon" / "common"
  issuance_trigger: str          # cognitive event that triggered issuance
  provenance: str                # tool provenance string
  evidence_type: EvidenceType     # evidence row type that led to issuance

  @staticmethod
  def rarity_band_from_score(score: float) -> str:
    """Classify a rarity score into a human band."""
    if score >= 0.75:
      return "very_rare"
    if score >= 0.50:
      return "rare"
    if score >= 0.25:
      return "uncommon"
    return "common"


@dataclass(frozen=True)
class ToolScope:
  """Organic scope descriptor for a tool evidence source.

  Emerges from what the tool produces — not pre-declared.
  Captures what the tool *does* based on its evidence type and provenance.
  """

  provenance: str                # tool provenance string
  evidence_type: EvidenceType    # evidence row type this tool produces
  source_system: str            # "glass" / "grid" / "calculator" / other
  produces_transitions: bool     # whether this tool can propose reward transitions
  payload_keys: tuple[str, ...]  # expected top-level keys in tool payload


  @staticmethod
  def from_provenance(provenance: str) -> "ToolScope | None":
    """Infer a ToolScope from a known provenance string.

    Returns None for unrecognised provenance — new tools don't need
    to be registered here; this is a convenience, not a gate.
    """
    _KNOWN: dict[str, ToolScope] = {
      ToolProvenance.GLASS_INGEST: ToolScope(
        provenance="glass_ingest",
        evidence_type=EvidenceType.GLASS_SESSION_EVENT,
        source_system="glass",
        produces_transitions=True,
        payload_keys=("session_id", "student_id", "reward_id", "contract_satisfied", "ready_for_payment"),
      ),
      ToolProvenance.GRID_SUBSTANTIATION: ToolScope(
        provenance="grid_substantiation",
        evidence_type=EvidenceType.AGENT_INTERPRETATION,
        source_system="grid",
        produces_transitions=True,
        payload_keys=("student_id", "reward_id", "_grid_substantiation"),
      ),
      ToolProvenance.FAIL_SNAPSHOT: ToolScope(
        provenance="fail_snapshot",
        evidence_type=EvidenceType.FAILURE_SNAPSHOT,
        source_system="glass",
        produces_transitions=False,
        payload_keys=("session_id", "student_id", "command", "exit_code"),
      ),
      ToolProvenance.STUDENT_ACK: ToolScope(
        provenance="student_ack",
        evidence_type=EvidenceType.STUDENT_CONFIRMATION,
        source_system="xchange",
        produces_transitions=True,
        payload_keys=("student_id", "reward_id"),
      ),
      ToolProvenance.AGENT_INTERP: ToolScope(
        provenance="agent_interp",
        evidence_type=EvidenceType.AGENT_INTERPRETATION,
        source_system="grid",
        produces_transitions=True,
        payload_keys=("student_id", "reward_id", "summary", "rationale"),
      ),
      ToolProvenance.CALCULATOR: ToolScope(
        provenance="calculator",
        evidence_type=EvidenceType.AGENT_INTERPRETATION,
        source_system="calculator",
        produces_transitions=False,
        payload_keys=("token_log", "exchange_eval", "summary"),
      ),
    }
    return _KNOWN.get(provenance)


def infer_token_scope(
  *,
  token: RewardToken,
  provenance: str,
  evidence_type: EvidenceType,
) -> TokenScope:
  """Build a TokenScope from a RewardToken and its issuance context.

  Scope *emerges* from token properties — this function does not
  consult any registry or mapping table.
  """
  return TokenScope(
    insight_tier=token.insight_tier,
    rarity_band=TokenScope.rarity_band_from_score(token.rarity_score),
    issuance_trigger=token.issuance_trigger,
    provenance=provenance,
    evidence_type=evidence_type,
  )


DEFAULT_CONTRACT_ID: Final[str] = "psc-v0-default"
POLICY_VERSION: Final[str] = "policy-core-v0"

# Integer value per insight tier — used for backward-compatible amount property.
_TIER_AMOUNTS: Final[dict[InsightTier, int]] = {
  InsightTier.SURFACE: 1,
  InsightTier.PATTERN: 2,
  InsightTier.STRUCTURAL: 3,
  InsightTier.CAUSAL: 4,
  InsightTier.THEORETICAL: 5,
}


@dataclass(frozen=True)
class RewardToken:
  """x-change epistemic credential for a reward issuance.

  Rarity is stamped once at issuance via compute_rarity_score().
  Do NOT recompute rarity_score after issuance — it is a stable baseline.
  The `amount` property is a backward-compatible integer derived from insight_tier.
  """

  insight_tier: InsightTier
  base_bank_depth: int         # 0–100: knowledge-base depth score
  inferential_richness: float  # 0.0–1.0: reasoning-chain depth
  trend_position: float        # 0.0–1.0: 0 = emerging edge, 1 = well-established
  rarity_score: float          # 0.0–1.0: stamped at issuance, never recalculated
  issuance_trigger: str        # cognitive event that triggered issuance
  issued_at: str               # ISO 8601 timestamp

  @property
  def amount(self) -> int:
    """Backward-compatible integer value derived from insight_tier."""
    return _TIER_AMOUNTS[self.insight_tier]


def compute_rarity_score(
  *,
  insight_tier: InsightTier,
  inferential_richness: float,
  trend_position: float,
) -> float:
  """Compute rarity score for a token at issuance time.

  Weights:
    40 %  emergence  (1 - trend_position): rare tokens live at the emerging edge
    40 %  inferential richness: depth of reasoning chain required
    20 %  epistemic tier weight: higher tier = rarer to achieve

  Result is clamped to [0.0, 1.0] and rounded to 4 decimal places.
  Stamp this value at issuance and never recompute it.
  """
  _tier_weights: dict[InsightTier, float] = {
    InsightTier.SURFACE: 0.0,
    InsightTier.PATTERN: 0.25,
    InsightTier.STRUCTURAL: 0.50,
    InsightTier.CAUSAL: 0.75,
    InsightTier.THEORETICAL: 1.0,
  }
  tier_w = _tier_weights[insight_tier]
  rarity = (
    (1.0 - trend_position) * 0.4
    + inferential_richness * 0.4
    + tier_w * 0.2
  )
  return round(max(0.0, min(1.0, rarity)), 4)


@dataclass(frozen=True)
class TransitionResult:
  """Result of a proposed state change."""

  new_state: RewardState
  new_outcome: OutcomeState
  notes: tuple[str, ...]


@dataclass(frozen=True)
class ExchangeRequest:
  """A student's request to exchange a token for a scope of value."""

  request_id: str
  student_id: str
  reward_id: str
  requested_scope: dict[str, Any]  # scope keys and values to exchange
  submitted_at: str                # ISO 8601 timestamp


@dataclass(frozen=True)
class ConstraintConfig:
  """Configuration for the layered exchange constraint evaluator.

  Safety/Security layer (hard gate):
    blocked_scope_keys — any request containing these keys is rejected outright.

  Ethics/Irreversibility layer (scope narrowing):
    irreversible_scope_keys — operations that cannot be undone.
    require_explicit_irreversible_approval — if True, irreversible keys are
      stripped from the approved scope unless the key
      'explicit_irreversible_approval' is present and truthy in the request.

  Economic Stability layer (scope narrowing):
    max_token_amount — caps the 'token_amount' key in the approved scope.
    max_scope_items  — caps the total number of scope keys approved.
  """

  blocked_scope_keys: frozenset[str]
  irreversible_scope_keys: frozenset[str]
  require_explicit_irreversible_approval: bool
  max_token_amount: int | None
  max_scope_items: int | None


@dataclass(frozen=True)
class LayerResult:
  """Result of a single constraint layer evaluation."""

  layer: ConstraintLayer
  passed: bool
  approved_scope: dict[str, Any]  # scope after this layer's narrowing
  blocked_keys: tuple[str, ...]   # keys removed or blocked at this layer
  notes: tuple[str, ...]


@dataclass(frozen=True)
class ExchangeResult:
  """Result of full layered exchange constraint evaluation."""

  request_id: str
  layers: tuple[LayerResult, ...]
  final_approved_scope: dict[str, Any]
  approved: bool       # False if any hard-gate layer rejected the request
  evaluated_at: str    # ISO 8601 timestamp


def evaluate_exchange_request(
  request: ExchangeRequest,
  config: ConstraintConfig,
) -> ExchangeResult:
  """Apply layered constraint evaluation to an exchange request.

  Layers applied in order:
    1. SAFETY_SECURITY       — hard gate; rejection returns immediately.
    2. ETHICS_IRREVERSIBILITY — narrows scope.
    3. ECONOMIC_STABILITY     — narrows scope.

  Returns ExchangeResult with approved=True if all hard gates passed.
  final_approved_scope may be smaller than requested_scope.
  """
  evaluated_at = datetime.now(timezone.utc).isoformat()
  layers: list[LayerResult] = []
  current_scope: dict[str, Any] = dict(request.requested_scope)

  # -- Layer 1: Safety / Security (hard gate) --------------------------------
  blocked_in_safety = tuple(k for k in current_scope if k in config.blocked_scope_keys)
  if blocked_in_safety:
    layers.append(
      LayerResult(
        layer=ConstraintLayer.SAFETY_SECURITY,
        passed=False,
        approved_scope={},
        blocked_keys=blocked_in_safety,
        notes=("safety_security: blocked scope keys present; request denied",),
      )
    )
    return ExchangeResult(
      request_id=request.request_id,
      layers=tuple(layers),
      final_approved_scope={},
      approved=False,
      evaluated_at=evaluated_at,
    )
  layers.append(
    LayerResult(
      layer=ConstraintLayer.SAFETY_SECURITY,
      passed=True,
      approved_scope=dict(current_scope),
      blocked_keys=(),
      notes=("safety_security: passed — no blocked keys",),
    )
  )

  # -- Layer 2: Ethics / Irreversibility (scope narrowing) -------------------
  irreversible_present = tuple(k for k in current_scope if k in config.irreversible_scope_keys)
  if irreversible_present and config.require_explicit_irreversible_approval:
    has_approval = bool(current_scope.get("explicit_irreversible_approval"))
    if not has_approval:
      narrowed = {k: v for k, v in current_scope.items() if k not in config.irreversible_scope_keys}
      layers.append(
        LayerResult(
          layer=ConstraintLayer.ETHICS_IRREVERSIBILITY,
          passed=True,
          approved_scope=narrowed,
          blocked_keys=irreversible_present,
          notes=("ethics_irreversibility: irreversible keys removed — no explicit approval",),
        )
      )
      current_scope = narrowed
    else:
      layers.append(
        LayerResult(
          layer=ConstraintLayer.ETHICS_IRREVERSIBILITY,
          passed=True,
          approved_scope=dict(current_scope),
          blocked_keys=(),
          notes=("ethics_irreversibility: irreversible operations approved explicitly",),
        )
      )
  else:
    layers.append(
      LayerResult(
        layer=ConstraintLayer.ETHICS_IRREVERSIBILITY,
        passed=True,
        approved_scope=dict(current_scope),
        blocked_keys=(),
        notes=("ethics_irreversibility: no irreversible operations present",),
      )
    )

  # -- Layer 3: Economic Stability (scope narrowing) -------------------------
  economic_notes: list[str] = []
  economic_blocked: list[str] = []
  narrowed_economic: dict[str, Any] = dict(current_scope)

  if config.max_scope_items is not None and len(current_scope) > config.max_scope_items:
    allowed_keys = list(current_scope.keys())[: config.max_scope_items]
    removed = [k for k in current_scope if k not in allowed_keys]
    economic_blocked.extend(removed)
    narrowed_economic = {k: v for k, v in current_scope.items() if k in allowed_keys}
    economic_notes.append(f"economic_stability: scope narrowed to {config.max_scope_items} items")

  if config.max_token_amount is not None:
    token_amount = narrowed_economic.get("token_amount")
    if isinstance(token_amount, (int, float)) and token_amount > config.max_token_amount:
      narrowed_economic = {**narrowed_economic, "token_amount": config.max_token_amount}
      economic_notes.append(f"economic_stability: token_amount capped at {config.max_token_amount}")

  if not economic_notes:
    economic_notes.append("economic_stability: within bounds")

  layers.append(
    LayerResult(
      layer=ConstraintLayer.ECONOMIC_STABILITY,
      passed=True,
      approved_scope=narrowed_economic,
      blocked_keys=tuple(economic_blocked),
      notes=tuple(economic_notes),
    )
  )

  return ExchangeResult(
    request_id=request.request_id,
    layers=tuple(layers),
    final_approved_scope=narrowed_economic,
    approved=True,
    evaluated_at=evaluated_at,
  )


def ingest_bool(payload: dict[str, Any], key: str) -> bool:
  """Return True for common truthy representations in ingest JSON."""
  v = payload.get(key)
  if v is True:
    return True
  if v is False or v is None:
    return False
  if isinstance(v, str):
    return v.strip().lower() in {"1", "true", "yes", "y"}
  return bool(v)


def next_state_after_glass_evidence(
  *,
  current: RewardState,
  outcome: OutcomeState,
  evidence_type: EvidenceType,
  ingest_payload: dict[str, Any],
) -> TransitionResult | None:
  """Apply ingest-derived evidence proposals. Returns None if no change.

  Ingest payloads may include evidence attachments such as ``_glass_bridge`` and
  ``_grid_substantiation``. Those nested blobs are never consulted here — only
  explicit top-level policy booleans (``contract_satisfied``, ``ready_for_payment``,
  ``request_review``, ``student_ack``) drive transitions.
  """

  notes: list[str] = []

  if ingest_bool(ingest_payload, "request_review"):
    return TransitionResult(
      new_state=RewardState.REVIEW_REQUESTED,
      new_outcome=OutcomeState.REVIEW_OPEN,
      notes=("review_requested via ingest",),
    )

  if evidence_type is EvidenceType.STUDENT_CONFIRMATION or ingest_bool(ingest_payload, "student_ack"):
    if current is not RewardState.PAYMENT_CONFIRMED:
      return TransitionResult(
        new_state=current,
        new_outcome=outcome,
        notes=("student_ack ignored: requires payment_confirmed",),
      )
    return TransitionResult(
      new_state=RewardState.STUDENT_ACKNOWLEDGED,
      new_outcome=OutcomeState.ACKNOWLEDGED,
      notes=("student acknowledged",),
    )

  new_state = current
  new_outcome = outcome

  satisfied = ingest_bool(ingest_payload, "contract_satisfied")
  if satisfied and current is RewardState.DRAFTED:
    new_state = RewardState.EARNED
    new_outcome = OutcomeState.UNKNOWN
    notes.append("contract_satisfied: drafted -> earned")

  ready_pay = ingest_bool(ingest_payload, "ready_for_payment")
  if ready_pay and new_state is RewardState.EARNED:
    new_state = RewardState.PAYMENT_PENDING
    notes.append("ready_for_payment: earned -> payment_pending")

  if evidence_type is EvidenceType.FAILURE_SNAPSHOT:
    notes.append("failure_snapshot recorded")

  if not notes and evidence_type in (
    EvidenceType.GLASS_SESSION_EVENT,
    EvidenceType.SUCCESS_AFTER_SUPPORT,
    EvidenceType.RETURN_ATTEMPT,
  ):
    return None

  if not notes:
    return None

  return TransitionResult(new_state=new_state, new_outcome=new_outcome, notes=tuple(notes))


def next_state_after_stripe_payment(
  *,
  current: RewardState,
  outcome: OutcomeState,
  reward_student_id: str,
  payment_student_id: str,
) -> TransitionResult | None:
  """Return new reward state after Stripe payment success, or None if student mismatch."""

  if reward_student_id != payment_student_id:
    return None

  if current in (RewardState.PAYMENT_CONFIRMED, RewardState.STUDENT_ACKNOWLEDGED):
    return TransitionResult(
      new_state=current,
      new_outcome=outcome,
      notes=("stripe replay: reward already confirmed",),
    )

  if current not in (RewardState.EARNED, RewardState.PAYMENT_PENDING):
    return TransitionResult(
      new_state=current,
      new_outcome=outcome,
      notes=(f"stripe not applied: invalid prior state {current}",),
    )

  new_outcome = outcome
  if outcome in (OutcomeState.UNKNOWN, OutcomeState.DELIVERED_PENDING_ACK):
    new_outcome = OutcomeState.DELIVERED_PENDING_ACK

  return TransitionResult(
    new_state=RewardState.PAYMENT_CONFIRMED,
    new_outcome=new_outcome,
    notes=("payment confirmed via Stripe",),
  )
