from __future__ import annotations

import os
import tempfile
import unittest

from xchange.storage import (
  insert_support_signal,
  list_support_signals,
  open_db,
  resolve_support_signal,
)


class SupportSignalsApiTests(unittest.TestCase):
  def setUp(self) -> None:
    self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
    os.close(self._fd)
    self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

  def test_list_filter_by_kind(self) -> None:
    """List support signals filtered by kind."""
    with open_db(self._path) as conn:
      insert_support_signal(conn=conn, kind="stripe_missing_metadata", payload={"foo": "bar"})
      insert_support_signal(conn=conn, kind="stripe_student_mismatch", payload={"baz": "qux"})
      insert_support_signal(conn=conn, kind="stripe_missing_metadata", payload={"test": "data"})
      
      signals = list_support_signals(conn=conn, kind="stripe_missing_metadata")
      
      self.assertEqual(len(signals), 2)
      for sig in signals:
        self.assertEqual(sig["kind"], "stripe_missing_metadata")

  def test_unresolved_filter(self) -> None:
    """List only unresolved support signals."""
    with open_db(self._path) as conn:
      id1 = insert_support_signal(conn=conn, kind="test_kind", payload={"id": 1})
      insert_support_signal(conn=conn, kind="test_kind", payload={"id": 2})
      resolve_support_signal(conn=conn, signal_id=id1, resolution_note="Fixed")
      
      unresolved = list_support_signals(conn=conn, resolved=False)
      
      self.assertEqual(len(unresolved), 1)
      self.assertEqual(unresolved[0]["payload"]["id"], 2)
      self.assertIsNone(unresolved[0]["resolved_at"])

  def test_resolve_flow(self) -> None:
    """Resolve a support signal and verify resolution note."""
    with open_db(self._path) as conn:
      sig_id = insert_support_signal(conn=conn, kind="test", payload={"issue": "data"})
      
      found = resolve_support_signal(conn=conn, signal_id=sig_id, resolution_note="Manually fixed")
      
      self.assertTrue(found)
      
      signals = list_support_signals(conn=conn, resolved=True)
      self.assertEqual(len(signals), 1)
      self.assertIsNotNone(signals[0]["resolved_at"])
      self.assertEqual(signals[0]["payload"]["resolution"]["resolution_note"], "Manually fixed")

  def test_resolve_nonexistent_signal(self) -> None:
    """Resolve returns False for nonexistent signal."""
    with open_db(self._path) as conn:
      found = resolve_support_signal(conn=conn, signal_id=9999, resolution_note="test")
      self.assertFalse(found)

  def test_list_respects_limit(self) -> None:
    """List respects limit parameter."""
    with open_db(self._path) as conn:
      for i in range(10):
        insert_support_signal(conn=conn, kind="test", payload={"index": i})
      
      signals = list_support_signals(conn=conn, limit=5)
      
      self.assertEqual(len(signals), 5)

  def test_list_sorted_created_at_desc(self) -> None:
    """List returns signals in descending created_at order."""
    with open_db(self._path) as conn:
      for i in range(3):
        insert_support_signal(conn=conn, kind="test", payload={"index": i})
      
      signals = list_support_signals(conn=conn)
      
      self.assertEqual(signals[0]["payload"]["index"], 2)
      self.assertEqual(signals[1]["payload"]["index"], 1)
      self.assertEqual(signals[2]["payload"]["index"], 0)


if __name__ == "__main__":
  unittest.main()
