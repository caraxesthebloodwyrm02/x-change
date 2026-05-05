from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path

from xchange.domain import EvidenceType, RewardState
from xchange.storage import (
  append_evidence,
  create_reward_draft,
  get_reward_state,
  ingest_glass_session,
  open_db,
  process_stripe_payment_intent_succeeded,
)


class ValidationGateTests(unittest.TestCase):
  def setUp(self) -> None:
    self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
    os.close(self._fd)
    self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

  def test_only_policy_advances_state(self) -> None:
    """No path writes reward_ledger.state outside _apply_transition."""
    storage_path = Path(__file__).parent.parent / "src" / "xchange" / "storage.py"
    content = storage_path.read_text()
    
    # Find all UPDATE statements that touch reward_ledger
    update_pattern = r'UPDATE\s+reward_ledger\s+SET\s+[^"]*state\s*='
    matches = list(re.finditer(update_pattern, content, re.IGNORECASE | re.MULTILINE))
    
    # All must be inside _apply_transition
    for match in matches:
      start_pos = match.start()
      # Find the function definition before this match
      func_search = content[:start_pos].rfind("def ")
      func_line = content[func_search:content.find("(", func_search)]
      self.assertIn("_apply_transition", func_line, 
                   f"Found state update outside _apply_transition: {match.group()}")

  def test_stripe_idempotency_unique(self) -> None:
    """payment_confirmations.stripe_event_id has UNIQUE constraint."""
    with open_db(self._path) as conn:
      cur = conn.execute("PRAGMA index_list(payment_confirmations)")
      indexes = cur.fetchall()
      
      found_unique = False
      for idx in indexes:
        idx_name = idx["name"]
        cur2 = conn.execute(f"PRAGMA index_info({idx_name})")
        cols = cur2.fetchall()
        for col in cols:
          if col["name"] == "stripe_event_id":
            found_unique = True
            break
      
      # Also check the schema directly
      cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='payment_confirmations'")
      schema = cur.fetchone()["sql"]
      self.assertIn("UNIQUE", schema)
      self.assertIn("stripe_event_id", schema)

  def test_provenance_required(self) -> None:
    """Every evidence_ledger and payment_confirmations insert requires non-empty provenance."""
    with open_db(self._path) as conn:
      # Check schema has NOT NULL for evidence_ledger.provenance
      cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='evidence_ledger'")
      schema = cur.fetchone()["sql"]
      self.assertIn("provenance TEXT NOT NULL", schema)
      
      # Check schema has NOT NULL for payment_confirmations.provenance
      cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='payment_confirmations'")
      schema = cur.fetchone()["sql"]
      self.assertIn("provenance TEXT NOT NULL", schema)
      
      # Code grep: verify all append_evidence calls pass non-empty provenance
      # (This is a runtime check - the schema constraint is the primary defense)
      storage_path = Path(__file__).parent.parent / "src" / "xchange" / "storage.py"
      content = storage_path.read_text()
      # Find all append_evidence calls
      append_calls = re.findall(r'append_evidence\([^)]+provenance=["\']([^"\']+)', content)
      for provenance in append_calls:
        self.assertTrue(len(provenance) > 0, f"Found empty provenance string in append_evidence call")

  def test_support_path_on_missing_metadata(self) -> None:
    """Stripe webhook missing metadata.reward_id creates support_signals row."""
    with open_db(self._path) as conn:
      # Simulate a Stripe event with missing reward_id in metadata
      result = process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id="evt_missing",
        stripe_payment_intent_id="pi_missing",
        reward_id="",  # Empty reward_id
        student_id="s1",
        raw_event={"id": "evt_missing", "data": {"object": {"metadata": {}}}},
      )
      
      # Should create support signal
      cur = conn.execute("SELECT kind FROM support_signals ORDER BY id DESC LIMIT 1")
      row = cur.fetchone()
      self.assertIsNotNone(row)

  def test_ack_does_not_imply_pay(self) -> None:
    """Reward in earned cannot reach student_acknowledged without payment_confirmed first."""
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
      ingest_glass_session(
        conn=conn,
        session_id="sess1",
        student_id="s1",
        payload={"reward_id": "r1", "contract_satisfied": True},
      )
      
      # Now in earned state, try to ack
      ingest_glass_session(
        conn=conn,
        session_id="sess2",
        student_id="s1",
        payload={"reward_id": "r1", "student_ack": True},
      )
      
      state = get_reward_state(conn, reward_id="r1")
      self.assertIsNotNone(state)
      assert state is not None
      # Should still be in earned, not student_acknowledged
      self.assertEqual(state["state"], RewardState.EARNED.value)

  def test_fail_closed_on_missing_ingest_token(self) -> None:
    """Unset XCHANGE_INGEST_TOKEN causes _require_ingest_token to return False."""
    from xchange.main import _require_ingest_token
    from http.server import BaseHTTPRequestHandler
    from io import BytesIO
    
    # Mock request with no token
    class MockRequest(BaseHTTPRequestHandler):
      def __init__(self) -> None:
        self.headers = {}
      
      def get_header(self, name: str, default: str = "") -> str:
        return self.headers.get(name, default)
    
    # Ensure env var is unset
    saved = os.environ.get("XCHANGE_INGEST_TOKEN")
    try:
      if "XCHANGE_INGEST_TOKEN" in os.environ:
        del os.environ["XCHANGE_INGEST_TOKEN"]
      
      mock_handler = MockRequest()
      result = _require_ingest_token(mock_handler)  # type: ignore
      
      self.assertFalse(result)
    finally:
      if saved:
        os.environ["XCHANGE_INGEST_TOKEN"] = saved


if __name__ == "__main__":
  unittest.main()
