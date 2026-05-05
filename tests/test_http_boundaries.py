from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import HTTPServer
from typing import Any

from xchange.main import AppHandler, _reset_rate_limit_for_tests
from xchange.storage import create_reward_draft, open_db


class QuietAppHandler(AppHandler):
  def log_message(self, format: str, *args: object) -> None:
    return


class HttpBoundaryTests(unittest.TestCase):
  def setUp(self) -> None:
    self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
    os.close(self._fd)
    self._saved_env = {
      name: os.environ.get(name)
      for name in (
        "XCHANGE_DB_PATH",
        "XCHANGE_INGEST_TOKEN",
        "STRIPE_WEBHOOK_SECRET",
        "XCHANGE_RATE_LIMIT_REQUESTS",
        "XCHANGE_RATE_LIMIT_WINDOW_SECONDS",
      )
    }
    os.environ["XCHANGE_DB_PATH"] = self._path
    os.environ["XCHANGE_INGEST_TOKEN"] = "test-token"
    os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
    os.environ["XCHANGE_RATE_LIMIT_REQUESTS"] = "100"
    os.environ["XCHANGE_RATE_LIMIT_WINDOW_SECONDS"] = "60"
    _reset_rate_limit_for_tests()

    self.server = HTTPServer(("127.0.0.1", 0), QuietAppHandler)
    self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
    self.thread.start()
    self.addCleanup(self._cleanup)

  def _cleanup(self) -> None:
    self.server.shutdown()
    self.server.server_close()
    self.thread.join(timeout=2)
    _reset_rate_limit_for_tests()
    for name, value in self._saved_env.items():
      if value is None:
        os.environ.pop(name, None)
      else:
        os.environ[name] = value
    if os.path.exists(self._path):
      os.remove(self._path)

  def _request(
    self,
    method: str,
    path: str,
    *,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
  ) -> tuple[int, dict[str, Any], dict[str, str]]:
    conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
    conn.request(method, path, body=body, headers=headers or {})
    resp = conn.getresponse()
    raw = resp.read()
    response_headers = {k: v for k, v in resp.getheaders()}
    conn.close()
    return resp.status, json.loads(raw.decode("utf-8")), response_headers

  def _auth_headers(self) -> dict[str, str]:
    return {"Authorization": "Bearer test-token"}

  def _stripe_headers(self, body: bytes) -> dict[str, str]:
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.".encode("utf-8") + body
    sig = hmac.new(b"whsec_test", signed_payload, hashlib.sha256).hexdigest()
    return {
      "Content-Type": "application/json",
      "Stripe-Signature": f"t={timestamp},v1={sig}",
    }

  def test_reward_state_requires_ingest_token(self) -> None:
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r1", student_id="s1")

    status, payload, _ = self._request("GET", "/v0/state/reward/r1")
    self.assertEqual(status, 401)
    self.assertEqual(payload["error"], "unauthorized")

    status, payload, _ = self._request(
      "GET",
      "/v0/state/reward/r1",
      headers=self._auth_headers(),
    )
    self.assertEqual(status, 200)
    self.assertEqual(payload["reward_id"], "r1")

  def test_unauthorized_operator_reads_are_not_rate_limited_first(self) -> None:
    os.environ["XCHANGE_RATE_LIMIT_REQUESTS"] = "1"
    _reset_rate_limit_for_tests()

    first, _, _ = self._request("GET", "/v0/state/reward/missing")
    second, payload, _ = self._request("GET", "/v0/state/reward/missing")

    self.assertEqual(first, 401)
    self.assertEqual(second, 401)
    self.assertEqual(payload["error"], "unauthorized")

  def test_operator_routes_return_429_after_authenticated_limit(self) -> None:
    os.environ["XCHANGE_RATE_LIMIT_REQUESTS"] = "1"
    _reset_rate_limit_for_tests()

    first, _, _ = self._request(
      "GET",
      "/v0/outcomes/summary",
      headers=self._auth_headers(),
    )
    second, payload, headers = self._request(
      "GET",
      "/v0/outcomes/summary",
      headers=self._auth_headers(),
    )

    self.assertEqual(first, 200)
    self.assertEqual(second, 429)
    self.assertEqual(payload["error"], "rate_limited")
    self.assertIn("Retry-After", headers)

  def test_stripe_webhook_is_not_operator_rate_limited(self) -> None:
    os.environ["XCHANGE_RATE_LIMIT_REQUESTS"] = "1"
    _reset_rate_limit_for_tests()
    body = json.dumps({"id": "evt_ignored", "type": "invoice.paid", "data": {"object": {}}}).encode("utf-8")

    first, first_payload, _ = self._request(
      "POST",
      "/v0/stripe/webhook",
      body=body,
      headers=self._stripe_headers(body),
    )
    second, second_payload, _ = self._request(
      "POST",
      "/v0/stripe/webhook",
      body=body,
      headers=self._stripe_headers(body),
    )

    self.assertEqual(first, 200)
    self.assertEqual(second, 200)
    self.assertTrue(first_payload["ignored"])
    self.assertTrue(second_payload["ignored"])

  def test_glass_bridge_http_ingest_records_evidence(self) -> None:
    with open_db(self._path) as conn:
      create_reward_draft(conn=conn, reward_id="r1", student_id="s1")

    body = json.dumps(
      {
        "student_id": "s1",
        "reward_id": "r1",
        "contract_satisfied": True,
        "bridge": {"session_id": "glass-1", "agent_state": "idle"},
      }
    ).encode("utf-8")

    status, payload, _ = self._request(
      "POST",
      "/v0/ingest/glass-bridge",
      body=body,
      headers={"Content-Type": "application/json", **self._auth_headers()},
    )

    self.assertEqual(status, 200)
    self.assertTrue(payload["ok"])
    with open_db(self._path) as conn:
      row = conn.execute(
        "SELECT payload_json FROM evidence_ledger WHERE session_id='glass-1'"
      ).fetchone()
    self.assertIsNotNone(row)
    assert row is not None
    evidence_payload = json.loads(row["payload_json"])
    self.assertEqual(evidence_payload["_glass_bridge"]["agent_state"], "idle")


if __name__ == "__main__":
  unittest.main()
