from __future__ import annotations

import os
import tempfile
import unittest

from xchange import mcp_read
from xchange.storage import (
    create_reward_draft,
    insert_support_signal,
    list_payment_confirmations,
    list_support_signals,
    open_db,
)


class McpReadHelpersTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

    def test_support_signals_pagination_has_more(self) -> None:
        with open_db(self._path) as conn:
            for i in range(5):
                insert_support_signal(conn=conn, kind="t", payload={"i": i})
        page = mcp_read.list_support_signals_page(self._path, limit=2, offset=0)
        self.assertTrue(page["has_more"])
        self.assertEqual(len(page["items"]), 2)
        self.assertEqual(page["items"][0]["payload"]["i"], 4)
        self.assertEqual(page["items"][1]["payload"]["i"], 3)

    def test_read_reward_state_missing(self) -> None:
        out = mcp_read.read_reward_state(self._path, reward_id="nope")
        self.assertEqual(out.get("error"), "reward_not_found")

    def test_list_payment_confirmations_empty(self) -> None:
        with open_db(self._path) as conn:
            rows = list_payment_confirmations(conn=conn)
        self.assertEqual(rows, [])


class ListSupportSignalsOffsetTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

    def test_offset_skips_newest(self) -> None:
        with open_db(self._path) as conn:
            for i in range(4):
                insert_support_signal(conn=conn, kind="x", payload={"i": i})
            rows = list_support_signals(conn=conn, limit=2, offset=1)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["payload"]["i"], 2)
        self.assertEqual(rows[1]["payload"]["i"], 1)


class McpReadRewardBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

    def test_read_reward_state_found(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(
                conn=conn, reward_id="r1", student_id="s1"
            )
        out = mcp_read.read_reward_state(self._path, reward_id="r1")
        self.assertEqual(out["reward_id"], "r1")
        self.assertEqual(out["student_id"], "s1")
        self.assertIn("evidence", out)


if __name__ == "__main__":
    unittest.main()
