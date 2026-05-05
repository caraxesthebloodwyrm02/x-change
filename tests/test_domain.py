from __future__ import annotations

import unittest

from xchange.domain import (
  EvidenceType,
  OutcomeState,
  RewardState,
  next_state_after_glass_evidence,
  next_state_after_stripe_payment,
)


class DomainTransitionTests(unittest.TestCase):
  def test_contract_satisfied_drafted_to_earned(self) -> None:
    r = next_state_after_glass_evidence(
      current=RewardState.DRAFTED,
      outcome=OutcomeState.UNKNOWN,
      evidence_type=EvidenceType.GLASS_SESSION_EVENT,
      ingest_payload={"contract_satisfied": True},
    )
    self.assertIsNotNone(r)
    assert r is not None
    self.assertEqual(r.new_state, RewardState.EARNED)

  def test_ready_for_payment_moves_to_pending(self) -> None:
    r = next_state_after_glass_evidence(
      current=RewardState.EARNED,
      outcome=OutcomeState.UNKNOWN,
      evidence_type=EvidenceType.GLASS_SESSION_EVENT,
      ingest_payload={"ready_for_payment": True},
    )
    self.assertIsNotNone(r)
    assert r is not None
    self.assertEqual(r.new_state, RewardState.PAYMENT_PENDING)

  def test_student_ack_requires_payment_confirmed(self) -> None:
    r = next_state_after_glass_evidence(
      current=RewardState.EARNED,
      outcome=OutcomeState.UNKNOWN,
      evidence_type=EvidenceType.STUDENT_CONFIRMATION,
      ingest_payload={"student_ack": True},
    )
    self.assertIsNotNone(r)
    assert r is not None
    self.assertEqual(r.new_state, RewardState.EARNED)

  def test_student_ack_after_payment(self) -> None:
    r = next_state_after_glass_evidence(
      current=RewardState.PAYMENT_CONFIRMED,
      outcome=OutcomeState.DELIVERED_PENDING_ACK,
      evidence_type=EvidenceType.STUDENT_CONFIRMATION,
      ingest_payload={"student_ack": True},
    )
    self.assertIsNotNone(r)
    assert r is not None
    self.assertEqual(r.new_state, RewardState.STUDENT_ACKNOWLEDGED)

  def test_stripe_payment(self) -> None:
    r = next_state_after_stripe_payment(
      current=RewardState.PAYMENT_PENDING,
      outcome=OutcomeState.UNKNOWN,
      reward_student_id="stu-1",
      payment_student_id="stu-1",
    )
    self.assertIsNotNone(r)
    assert r is not None
    self.assertEqual(r.new_state, RewardState.PAYMENT_CONFIRMED)

  def test_stripe_mismatch_student(self) -> None:
    r = next_state_after_stripe_payment(
      current=RewardState.PAYMENT_PENDING,
      outcome=OutcomeState.UNKNOWN,
      reward_student_id="stu-1",
      payment_student_id="stu-2",
    )
    self.assertIsNone(r)

  def test_review_requested(self) -> None:
    r = next_state_after_glass_evidence(
      current=RewardState.PAYMENT_PENDING,
      outcome=OutcomeState.DELIVERED_PENDING_ACK,
      evidence_type=EvidenceType.GLASS_SESSION_EVENT,
      ingest_payload={"request_review": True},
    )
    self.assertIsNotNone(r)
    assert r is not None
    self.assertEqual(r.new_state, RewardState.REVIEW_REQUESTED)


if __name__ == "__main__":
  unittest.main()
