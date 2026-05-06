from __future__ import annotations

import os
import tempfile
import unittest

from xchange.glass_adapter import map_glass_bridge_to_ingest
from xchange.storage import (
    create_reward_draft,
    get_reward_state,
    ingest_glass_session,
    open_db,
)

SAMPLE_BRIDGE = {
    "timestamp": "2026-05-04T02:16:01.720118+00:00",
    "session_id": "glass-sess-001",
    "agent_state": "idle",
    "threshold_state": "ground",
    "progress": 0.0,
    "blocks": [],
    "conversation": [],
    "voices": [],
    "signals": {"git_diff_lines": 10, "iteration_count": 3, "session_age_minutes": 5},
}


class MapperTests(unittest.TestCase):
    def test_map_minimal_bridge(self) -> None:
        result = map_glass_bridge_to_ingest(SAMPLE_BRIDGE, student_id="s1")
        self.assertEqual(result["session_id"], "glass-sess-001")
        self.assertEqual(result["student_id"], "s1")
        self.assertNotIn("reward_id", result)
        self.assertNotIn("contract_satisfied", result)

    def test_map_with_all_fields(self) -> None:
        result = map_glass_bridge_to_ingest(
            SAMPLE_BRIDGE,
            student_id="s1",
            reward_id="r1",
            contract_satisfied=True,
            ready_for_payment=True,
            failure={"command": "cd foo", "exit_code": 1},
        )
        self.assertEqual(result["reward_id"], "r1")
        self.assertTrue(result["contract_satisfied"])
        self.assertTrue(result["ready_for_payment"])
        self.assertEqual(result["failure"]["command"], "cd foo")

    def test_map_missing_session_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            map_glass_bridge_to_ingest({"no_session": True}, student_id="s1")

    def test_map_missing_student_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            map_glass_bridge_to_ingest(SAMPLE_BRIDGE, student_id="")

    def test_bridge_data_preserved(self) -> None:
        result = map_glass_bridge_to_ingest(SAMPLE_BRIDGE, student_id="s1")
        self.assertIn("_glass_bridge", result)
        self.assertEqual(result["_glass_bridge"]["agent_state"], "idle")
        self.assertEqual(result["_glass_bridge"]["signals"]["git_diff_lines"], 10)

    def test_map_empty_reward_id_raises(self) -> None:
        """reward_id provided but empty string must raise ValueError (L23)."""
        with self.assertRaises(ValueError) as ctx:
            map_glass_bridge_to_ingest(SAMPLE_BRIDGE, student_id="s1", reward_id="")
        self.assertIn("reward_id", str(ctx.exception))

    def test_map_student_ack_flag_included(self) -> None:
        """student_ack=True must appear in the mapped result dict (L37)."""
        result = map_glass_bridge_to_ingest(
            SAMPLE_BRIDGE, student_id="s1", student_ack=True
        )
        self.assertTrue(result.get("student_ack"))

    def test_map_request_review_flag_included(self) -> None:
        """request_review=True must appear in the mapped result dict (L39)."""
        result = map_glass_bridge_to_ingest(
            SAMPLE_BRIDGE, student_id="s1", request_review=True
        )
        self.assertTrue(result.get("request_review"))

    def test_map_false_flags_excluded(self) -> None:
        """False-valued optional flags must not appear in the result dict."""
        result = map_glass_bridge_to_ingest(
            SAMPLE_BRIDGE,
            student_id="s1",
            student_ack=False,
            request_review=False,
            contract_satisfied=False,
            ready_for_payment=False,
        )
        self.assertNotIn("student_ack", result)
        self.assertNotIn("request_review", result)
        self.assertNotIn("contract_satisfied", result)
        self.assertNotIn("ready_for_payment", result)


class EndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

    def test_endpoint_round_trip(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            mapped = map_glass_bridge_to_ingest(
                SAMPLE_BRIDGE,
                student_id="s1",
                reward_id="r1",
                contract_satisfied=True,
            )
            result = ingest_glass_session(
                conn=conn,
                session_id=mapped["session_id"],
                student_id=mapped["student_id"],
                payload=mapped,
            )
            self.assertTrue(result["ok"])
            self.assertTrue(result["evidence_recorded"])
            state = get_reward_state(conn, reward_id="r1")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state["state"], "earned")

    def test_endpoint_rejects_missing_bridge(self) -> None:
        with self.assertRaises(ValueError):
            map_glass_bridge_to_ingest({}, student_id="s1")

    def test_endpoint_auth_required(self) -> None:
        from http.server import BaseHTTPRequestHandler
        from typing import cast

        from xchange.main import _require_ingest_token

        original = os.environ.get("XCHANGE_INGEST_TOKEN")
        try:
            os.environ.pop("XCHANGE_INGEST_TOKEN", None)

            class FakeHandler:
                headers = {"Authorization": "", "X-Ingest-Token": ""}

            self.assertFalse(_require_ingest_token(cast(BaseHTTPRequestHandler, FakeHandler())))
        finally:
            if original is not None:
                os.environ["XCHANGE_INGEST_TOKEN"] = original


if __name__ == "__main__":
    unittest.main()
