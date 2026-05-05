from __future__ import annotations

import os
import tempfile
import unittest

from xchange.storage import (
  create_reward_draft,
  get_reward_state,
  ingest_glass_session,
  open_db,
  process_stripe_payment_intent_succeeded,
)


class RewardFoundationTests(unittest.TestCase):
  def setUp(self) -> None:
    self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
    os.close(self._fd)
    self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

  def test_e2e_flow(self) -> None:
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
      ingest_glass_session(
        conn=conn,
        session_id="sess-1",
        student_id="s1",
        payload={
          "reward_id": "r1",
          "contract_satisfied": True,
        },
      )
      ingest_glass_session(
        conn=conn,
        session_id="sess-2",
        student_id="s1",
        payload={
          "reward_id": "r1",
          "ready_for_payment": True,
        },
      )
      st = get_reward_state(conn, reward_id="r1")
      self.assertIsNotNone(st)
      assert st is not None
      self.assertEqual(st["state"], "payment_pending")

      out = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_1",
        stripe_payment_intent_id="pi_1",
        reward_id="r1",
        student_id="s1",
        raw_event={"id": "evt_1", "type": "payment_intent.succeeded"},
      )
      self.assertTrue(out.get("applied"))

      ingest_glass_session(
        conn=conn,
        session_id="sess-3",
        student_id="s1",
        payload={"reward_id": "r1", "student_ack": True},
      )
      final = get_reward_state(conn, reward_id="r1")
      self.assertIsNotNone(final)
      assert final is not None
      self.assertEqual(final["state"], "student_acknowledged")
      self.assertTrue(len(final["evidence"]) >= 3)

  def test_stripe_idempotent(self) -> None:
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r2", student_id="s2")
      ingest_glass_session(conn=conn, session_id="a", student_id="s2", payload={"reward_id": "r2", "contract_satisfied": True})
      ingest_glass_session(conn=conn, session_id="b", student_id="s2", payload={"reward_id": "r2", "ready_for_payment": True})
      ev = {"id": "evt_dup", "type": "payment_intent.succeeded"}
      o1 = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_dup",
        stripe_payment_intent_id="pi_d",
        reward_id="r2",
        student_id="s2",
        raw_event=ev,
      )
      self.assertTrue(o1.get("applied"))
      o2 = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_dup",
        stripe_payment_intent_id="pi_d",
        reward_id="r2",
        student_id="s2",
        raw_event=ev,
      )
      self.assertTrue(o2.get("duplicate"))

  def test_support_signal_on_missing_reward(self) -> None:
    with open_db(self._path) as conn:
      out = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_x",
        stripe_payment_intent_id="pi_x",
        reward_id="missing",
        student_id="s9",
        raw_event={"id": "evt_x"},
      )
      self.assertFalse(out.get("applied"))
      cur = conn.execute("SELECT kind FROM support_signals ORDER BY id DESC LIMIT 1")
      row = cur.fetchone()
      self.assertIsNotNone(row)
      self.assertEqual(row["kind"], "stripe_reward_missing")


  def test_stripe_student_mismatch(self) -> None:
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r3", student_id="s3")
      ingest_glass_session(conn=conn, session_id="a", student_id="s3", payload={"reward_id": "r3", "contract_satisfied": True})
      ingest_glass_session(conn=conn, session_id="b", student_id="s3", payload={"reward_id": "r3", "ready_for_payment": True})
      out = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_ms",
        stripe_payment_intent_id="pi_ms",
        reward_id="r3",
        student_id="wrong",
        raw_event={"id": "evt_ms"},
      )
      self.assertFalse(out.get("applied"))
      cur = conn.execute(
        "SELECT kind FROM support_signals WHERE kind='stripe_student_mismatch' ORDER BY id DESC LIMIT 1"
      )
      self.assertIsNotNone(cur.fetchone())

  def test_replay_with_different_reward(self) -> None:
    """Same stripe_event_id with different reward_id: second call returns duplicate, first reward untouched."""
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r_first", student_id="s1")
      create_reward_draft(conn=conn, reward_id="r_second", student_id="s1")
      ingest_glass_session(conn=conn, session_id="a", student_id="s1", payload={"reward_id": "r_first", "contract_satisfied": True, "ready_for_payment": True})
      ingest_glass_session(conn=conn, session_id="b", student_id="s1", payload={"reward_id": "r_second", "contract_satisfied": True, "ready_for_payment": True})
      
      # First call with r_first
      out1 = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_replay",
        stripe_payment_intent_id="pi_replay",
        reward_id="r_first",
        student_id="s1",
        raw_event={"id": "evt_replay"},
      )
      self.assertTrue(out1.get("applied"))
      
      # Second call with same event_id but different reward_id
      out2 = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_replay",
        stripe_payment_intent_id="pi_replay",
        reward_id="r_second",
        student_id="s1",
        raw_event={"id": "evt_replay"},
      )
      self.assertTrue(out2.get("duplicate"))
      
      # Verify first reward is confirmed, second is not
      state1 = get_reward_state(conn, reward_id="r_first")
      state2 = get_reward_state(conn, reward_id="r_second")
      self.assertIsNotNone(state1)
      self.assertIsNotNone(state2)
      assert state1 is not None
      assert state2 is not None
      self.assertEqual(state1["state"], "payment_confirmed")
      self.assertEqual(state2["state"], "payment_pending")


if __name__ == "__main__":
  unittest.main()
