from __future__ import annotations

import os
import tempfile
import unittest

from xchange.storage import (
    create_reward_draft,
    get_outcome_summary,
    ingest_glass_session,
    open_db,
    process_stripe_payment_intent_succeeded,
)


class OutcomeSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

    def test_empty_ledger(self) -> None:
        with open_db(self._path) as conn:
            s = get_outcome_summary(conn)
        self.assertEqual(s["total_rewards"], 0)
        self.assertEqual(s["by_state"], {})
        self.assertEqual(s["student_count"], 0)

    def test_counts_by_state(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            create_reward_draft(conn=conn, reward_id="r2", student_id="s1")
            create_reward_draft(conn=conn, reward_id="r3", student_id="s2")
            ingest_glass_session(conn=conn, session_id="a", student_id="s1",
                                 payload={"reward_id": "r1", "contract_satisfied": True})
            s = get_outcome_summary(conn)
        self.assertEqual(s["total_rewards"], 3)
        self.assertEqual(s["by_state"].get("drafted"), 2)
        self.assertEqual(s["by_state"].get("earned"), 1)
        self.assertEqual(s["student_count"], 2)

    def test_filter_by_student(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            create_reward_draft(conn=conn, reward_id="r2", student_id="s2")
            s = get_outcome_summary(conn, student_id="s1")
        self.assertEqual(s["total_rewards"], 1)
        self.assertEqual(s["student_count"], 1)

    def test_full_lifecycle_reflected(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            ingest_glass_session(conn=conn, session_id="a", student_id="s1",
                                 payload={"reward_id": "r1", "contract_satisfied": True})
            ingest_glass_session(conn=conn, session_id="b", student_id="s1",
                                 payload={"reward_id": "r1", "ready_for_payment": True})
            process_stripe_payment_intent_succeeded(
                conn=conn, stripe_event_id="evt_1", stripe_payment_intent_id="pi_1",
                reward_id="r1", student_id="s1",
                raw_event={"id": "evt_1", "type": "payment_intent.succeeded"})
            s = get_outcome_summary(conn)
        self.assertEqual(s["total_rewards"], 1)
        self.assertEqual(s["by_state"].get("payment_confirmed"), 1)


if __name__ == "__main__":
    unittest.main()
