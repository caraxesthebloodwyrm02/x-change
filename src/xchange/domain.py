"""Pure domain types and reward transition rules for x-change v0.

No I/O, no framework imports — policy logic only.
"""

from __future__ import annotations

from dataclasses import dataclass
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


DEFAULT_CONTRACT_ID: Final[str] = "psc-v0-default"
POLICY_VERSION: Final[str] = "policy-core-v0"


@dataclass(frozen=True)
class RewardToken:
  """x-change governance unit for a reward (not a signal-rate token)."""

  amount: int


@dataclass(frozen=True)
class TransitionResult:
  """Result of a proposed state change."""

  new_state: RewardState
  new_outcome: OutcomeState
  notes: tuple[str, ...]


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


def _boolish(payload: dict[str, Any], key: str) -> bool:
  return ingest_bool(payload, key)


def next_state_after_glass_evidence(
  *,
  current: RewardState,
  outcome: OutcomeState,
  evidence_type: EvidenceType,
  ingest_payload: dict[str, Any],
) -> TransitionResult | None:
  """Apply ingest-derived evidence proposals. Returns None if no change."""

  notes: list[str] = []

  if _boolish(ingest_payload, "request_review"):
    return TransitionResult(
      new_state=RewardState.REVIEW_REQUESTED,
      new_outcome=OutcomeState.REVIEW_OPEN,
      notes=("review_requested via ingest",),
    )

  if evidence_type is EvidenceType.STUDENT_CONFIRMATION or _boolish(ingest_payload, "student_ack"):
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

  satisfied = _boolish(ingest_payload, "contract_satisfied")
  if satisfied and current is RewardState.DRAFTED:
    new_state = RewardState.EARNED
    new_outcome = OutcomeState.UNKNOWN
    notes.append("contract_satisfied: drafted -> earned")

  ready_pay = _boolish(ingest_payload, "ready_for_payment")
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
  """Return new reward state after Stripe payment success, or None if student mismatch (signal elsewhere)."""

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
