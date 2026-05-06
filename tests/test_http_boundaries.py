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
        conn = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )
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
        body = json.dumps(
            {"id": "evt_ignored", "type": "invoice.paid", "data": {"object": {}}}
        ).encode("utf-8")

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

    def test_ingest_endpoints_require_token(self) -> None:
        # Both glass-session and glass-bridge must return 401 without a valid token.
        for path, body_dict in [
            ("/v0/ingest/glass-session", {"session_id": "s1", "student_id": "stu1"}),
            (
                "/v0/ingest/glass-bridge",
                {
                    "student_id": "stu1",
                    "bridge": {"session_id": "s1", "agent_state": "idle"},
                },
            ),
        ]:
            body = json.dumps(body_dict).encode("utf-8")
            status, payload, _ = self._request(
                "POST",
                path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer wrong-token",
                },
            )
            self.assertEqual(status, 401, f"{path} should return 401 for wrong token")
            self.assertEqual(
                payload["error"], "unauthorized", f"{path} error key mismatch"
            )

            status_no_auth, payload_no_auth, _ = self._request(
                "POST",
                path,
                body=body,
                headers={"Content-Type": "application/json"},
            )
            self.assertEqual(
                status_no_auth, 401, f"{path} should return 401 with no auth header"
            )

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


class StripeLivemodeTests(unittest.TestCase):
    """Verify the XCHANGE_LIVE_MODE guard.

    Every event is signed so it passes HMAC.  We vary ``livemode`` in the
    JSON body and ``XCHANGE_LIVE_MODE`` in the environment.
    """

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
                "XCHANGE_LIVE_MODE",
            )
        }
        os.environ["XCHANGE_DB_PATH"] = self._path
        os.environ["XCHANGE_INGEST_TOKEN"] = "test-token"
        os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        os.environ["XCHANGE_RATE_LIMIT_REQUESTS"] = "100"
        os.environ["XCHANGE_RATE_LIMIT_WINDOW_SECONDS"] = "60"
        os.environ.pop("XCHANGE_LIVE_MODE", None)
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

    def _signed_webhook(
        self, body_dict: dict[str, Any]
    ) -> tuple[bytes, dict[str, str]]:
        """Return (body_bytes, signed_headers) for a Stripe webhook request."""
        body = json.dumps(body_dict).encode("utf-8")
        timestamp = str(int(time.time()))
        signed_payload = f"{timestamp}.".encode("utf-8") + body
        sig = hmac.new(b"whsec_test", signed_payload, hashlib.sha256).hexdigest()
        headers = {
            "Content-Type": "application/json",
            "Stripe-Signature": f"t={timestamp},v1={sig}",
        }
        return body, headers

    def _post_webhook(self, body_dict: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        body, headers = self._signed_webhook(body_dict)
        conn = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )
        conn.request("POST", "/v0/stripe/webhook", body=body, headers=headers)
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, json.loads(raw.decode("utf-8"))

    def _ignored_event(self, livemode: bool) -> dict[str, Any]:
        """Minimal Stripe event payload for an unsupported type."""
        return {
            "id": "evt_test",
            "type": "invoice.paid",  # unsupported — ignored after livemode check
            "livemode": livemode,
            "data": {"object": {}},
        }

    # -- guard inactive when env var not set ------------------------------------

    def test_livemode_check_skipped_when_env_not_set(self) -> None:
        """Without XCHANGE_LIVE_MODE any livemode value is accepted."""
        for livemode in (True, False):
            status, payload = self._post_webhook(self._ignored_event(livemode))
            self.assertEqual(status, 200, f"livemode={livemode} should be accepted")
            self.assertTrue(payload.get("ignored"))
            self.assertNotEqual(payload.get("reason"), "livemode_mismatch")

    # -- production server (XCHANGE_LIVE_MODE=true) ----------------------------

    def test_live_event_accepted_on_production_server(self) -> None:
        os.environ["XCHANGE_LIVE_MODE"] = "true"
        status, payload = self._post_webhook(self._ignored_event(livemode=True))
        self.assertEqual(status, 200)
        self.assertNotEqual(payload.get("reason"), "livemode_mismatch")

    def test_test_event_rejected_on_production_server(self) -> None:
        """livemode=false ignored when server expects livemode=true."""
        os.environ["XCHANGE_LIVE_MODE"] = "true"
        status, payload = self._post_webhook(self._ignored_event(livemode=False))
        self.assertEqual(status, 200)
        self.assertTrue(payload["ignored"])
        self.assertEqual(payload["reason"], "livemode_mismatch")
        self.assertFalse(payload["event_livemode"])
        self.assertTrue(payload["expected_livemode"])

    def test_livemode_env_accepts_numeric_true(self) -> None:
        """XCHANGE_LIVE_MODE=1 is equivalent to true."""
        os.environ["XCHANGE_LIVE_MODE"] = "1"
        status, payload = self._post_webhook(self._ignored_event(livemode=True))
        self.assertEqual(status, 200)
        self.assertNotEqual(payload.get("reason"), "livemode_mismatch")
        status2, payload2 = self._post_webhook(self._ignored_event(livemode=False))
        self.assertEqual(status2, 200)
        self.assertEqual(payload2["reason"], "livemode_mismatch")

    # -- test server (XCHANGE_LIVE_MODE=false) ---------------------------------

    def test_test_event_accepted_on_test_server(self) -> None:
        os.environ["XCHANGE_LIVE_MODE"] = "false"
        status, payload = self._post_webhook(self._ignored_event(livemode=False))
        self.assertEqual(status, 200)
        self.assertNotEqual(payload.get("reason"), "livemode_mismatch")

    def test_live_event_rejected_on_test_server(self) -> None:
        """livemode=true ignored when server expects livemode=false."""
        os.environ["XCHANGE_LIVE_MODE"] = "false"
        status, payload = self._post_webhook(self._ignored_event(livemode=True))
        self.assertEqual(status, 200)
        self.assertTrue(payload["ignored"])
        self.assertEqual(payload["reason"], "livemode_mismatch")
        self.assertTrue(payload["event_livemode"])
        self.assertFalse(payload["expected_livemode"])

    # -- guard is post-signature -----------------------------------------------

    def test_livemode_check_does_not_fire_on_invalid_signature(self) -> None:
        """Tampered event must be rejected at the signature layer, not livemode."""
        os.environ["XCHANGE_LIVE_MODE"] = "true"
        body = json.dumps(self._ignored_event(livemode=True)).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Stripe-Signature": "t=0,v1=badhash",
        }
        conn = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )
        conn.request("POST", "/v0/stripe/webhook", body=body, headers=headers)
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()
        self.assertEqual(resp.status, 401)
        self.assertEqual(payload["error"], "invalid_stripe_signature")


if __name__ == "__main__":
    unittest.main()
