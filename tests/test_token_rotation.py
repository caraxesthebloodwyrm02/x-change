"""Tests for graceful token rotation via XCHANGE_INGEST_TOKEN_PREV.

Phase 4 ticket: token-pairs with a grace window (old + new both valid during
overlap).  The operator sets XCHANGE_INGEST_TOKEN_PREV at rotation time and
removes it after the overlap window has elapsed.
"""
from __future__ import annotations

import http.client
import json
import os
import tempfile
import threading
import unittest
from http.server import HTTPServer
from typing import Any

from xchange.main import AppHandler, _reset_rate_limit_for_tests


class QuietAppHandler(AppHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class TokenRotationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self._saved_env = {
            name: os.environ.get(name)
            for name in (
                "XCHANGE_DB_PATH",
                "XCHANGE_INGEST_TOKEN",
                "XCHANGE_INGEST_TOKEN_PREV",
                "XCHANGE_RATE_LIMIT_REQUESTS",
                "XCHANGE_RATE_LIMIT_WINDOW_SECONDS",
            )
        }
        os.environ["XCHANGE_DB_PATH"] = self._path
        os.environ["XCHANGE_INGEST_TOKEN"] = "new-token"
        os.environ.pop("XCHANGE_INGEST_TOKEN_PREV", None)
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
    ) -> tuple[int, dict[str, Any]]:
        conn = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        raw = resp.read()
        conn.close()
        return resp.status, json.loads(raw.decode("utf-8"))

    # ------------------------------------------------------------------ basic

    def test_new_token_accepted(self) -> None:
        """Current XCHANGE_INGEST_TOKEN is always accepted."""
        status, _ = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"Authorization": "Bearer new-token"},
        )
        self.assertEqual(status, 200)

    def test_old_token_rejected_when_no_prev_set(self) -> None:
        """Without XCHANGE_INGEST_TOKEN_PREV, old tokens are rejected."""
        status, payload = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"Authorization": "Bearer old-token"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    def test_wrong_token_rejected(self) -> None:
        """Completely wrong token is always rejected."""
        status, payload = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"Authorization": "Bearer wrong"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    # ---------------------------------------------------------------- overlap

    def test_prev_token_accepted_during_overlap(self) -> None:
        """XCHANGE_INGEST_TOKEN_PREV is accepted while set (overlap window)."""
        os.environ["XCHANGE_INGEST_TOKEN_PREV"] = "old-token"
        status, _ = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"Authorization": "Bearer old-token"},
        )
        self.assertEqual(status, 200)

    def test_new_token_still_accepted_during_overlap(self) -> None:
        """New token is still accepted when PREV is also set."""
        os.environ["XCHANGE_INGEST_TOKEN_PREV"] = "old-token"
        status, _ = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"Authorization": "Bearer new-token"},
        )
        self.assertEqual(status, 200)

    def test_x_ingest_token_header_prev_accepted(self) -> None:
        """X-Ingest-Token header also works with the prev token."""
        os.environ["XCHANGE_INGEST_TOKEN_PREV"] = "old-token"
        status, _ = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"X-Ingest-Token": "old-token"},
        )
        self.assertEqual(status, 200)

    def test_prev_token_not_accepted_after_removal(self) -> None:
        """Once XCHANGE_INGEST_TOKEN_PREV is unset, old token is rejected."""
        os.environ["XCHANGE_INGEST_TOKEN_PREV"] = "old-token"
        # Simulate operator removing prev after overlap window
        del os.environ["XCHANGE_INGEST_TOKEN_PREV"]
        status, payload = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"Authorization": "Bearer old-token"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    def test_unrelated_token_not_accepted_when_prev_is_set(self) -> None:
        """A third random token is rejected even when PREV is set."""
        os.environ["XCHANGE_INGEST_TOKEN_PREV"] = "old-token"
        status, payload = self._request(
            "GET",
            "/v0/outcomes/summary",
            headers={"Authorization": "Bearer random-other-token"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")


if __name__ == "__main__":
    unittest.main()
