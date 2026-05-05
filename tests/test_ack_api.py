from __future__ import annotations

import os
import tempfile
import unittest

from xchange.domain import RewardState
from xchange.storage import (
  acknowledge_reward,
  create_reward_draft,
  get_reward_state,
  ingest_glass_session,
  open_db,
  process_stripe_payment_intent_succeeded,
)


class AckApiTests(unittest.TestCase):
  def setUp(self) -> None:
    self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
    os.close(self._fd)
    self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

  def test_happy_path(self) -> None:
    """Ack succeeds when reward is in payment_confirmed state."""
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
      ingest_glass_session(conn=conn, session_id="a", student_id="s1", payload={"reward_id": "r1", "contract_satisfied": True})
      ingest_glass_session(conn=conn, session_id="b", student_id="s1", payload={"reward_id": "r1", "ready_for_payment": True})
      process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_1",
        stripe_payment_intent_id="pi_1",
        reward_id="r1",
        student_id="s1",
        raw_event={"id": "evt_1"},
      )
      
      result = acknowledge_reward(conn=conn, reward_id="r1", student_id="s1", notes="Thank you!")
      
      self.assertTrue(result.get("ok"))
      self.assertIsNotNone(result.get("transition"))
      
      state = get_reward_state(conn, reward_id="r1")
      self.assertIsNotNone(state)
      assert state is not None
      self.assertEqual(state["state"], RewardState.STUDENT_ACKNOWLEDGED.value)

  def test_wrong_state_409(self) -> None:
    """Ack returns 409 when reward is not payment_confirmed."""
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r2", student_id="s2")
      
      result = acknowledge_reward(conn=conn, reward_id="r2", student_id="s2")
      
      self.assertEqual(result.get("error"), "ack_requires_payment_confirmed")
      self.assertEqual(result.get("current_state"), RewardState.DRAFTED.value)

  def test_student_mismatch_creates_support_signal(self) -> None:
    """Ack with wrong student_id creates support signal and returns 409."""
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r3", student_id="s3")
      ingest_glass_session(conn=conn, session_id="a", student_id="s3", payload={"reward_id": "r3", "contract_satisfied": True})
      ingest_glass_session(conn=conn, session_id="b", student_id="s3", payload={"reward_id": "r3", "ready_for_payment": True})
      process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_3",
        stripe_payment_intent_id="pi_3",
        reward_id="r3",
        student_id="s3",
        raw_event={"id": "evt_3"},
      )
      
      result = acknowledge_reward(conn=conn, reward_id="r3", student_id="wrong")
      
      self.assertEqual(result.get("error"), "ack_student_mismatch")
      cur = conn.execute("SELECT kind FROM support_signals WHERE kind='ack_student_mismatch' ORDER BY id DESC LIMIT 1")
      row = cur.fetchone()
      self.assertIsNotNone(row)

  def test_idempotent_re_ack_is_noop(self) -> None:
    """Re-acknowledging already acknowledged reward is idempotent."""
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r4", student_id="s4")
      ingest_glass_session(conn=conn, session_id="a", student_id="s4", payload={"reward_id": "r4", "contract_satisfied": True})
      ingest_glass_session(conn=conn, session_id="b", student_id="s4", payload={"reward_id": "r4", "ready_for_payment": True})
      process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_4",
        stripe_payment_intent_id="pi_4",
        reward_id="r4",
        student_id="s4",
        raw_event={"id": "evt_4"},
      )
      
      acknowledge_reward(conn=conn, reward_id="r4", student_id="s4")
      result2 = acknowledge_reward(conn=conn, reward_id="r4", student_id="s4")
      
      self.assertTrue(result2.get("ok"))
      state = get_reward_state(conn, reward_id="r4")
      self.assertIsNotNone(state)
      assert state is not None
      self.assertEqual(state["state"], RewardState.STUDENT_ACKNOWLEDGED.value)


if __name__ == "__main__":
  unittest.main()
