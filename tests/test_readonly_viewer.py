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
from xchange.storage import create_reward_draft, open_db


class QuietAppHandler(AppHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class ReadonlyViewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self._saved_env = {
            name: os.environ.get(name)
            for name in (
                "XCHANGE_DB_PATH",
                "XCHANGE_INGEST_TOKEN",
                "XCHANGE_RATE_LIMIT_REQUESTS",
                "XCHANGE_RATE_LIMIT_WINDOW_SECONDS",
            )
        }
        os.environ["XCHANGE_DB_PATH"] = self._path
        os.environ["XCHANGE_INGEST_TOKEN"] = "test-token"
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

    def _request_raw(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, str, dict[str, str]]:
        conn = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=5
        )
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        raw = resp.read().decode("utf-8")
        response_headers = {k: v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, raw, response_headers

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, Any], dict[str, str]]:
        status, raw, response_headers = self._request_raw(
            method,
            path,
            body=body,
            headers=headers,
        )
        return status, json.loads(raw), response_headers

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": "Bearer test-token"}

    def test_viewer_requires_auth(self) -> None:
        status, payload, _ = self._request_json("GET", "/v0/viewer")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    def test_viewer_renders_html(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r-view", student_id="s-view")

        status, html, headers = self._request_raw(
            "GET",
            "/v0/viewer?reward_id=r-view",
            headers=self._auth_headers(),
        )

        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn("x-change Trust Surface Viewer", html)
        self.assertIn("READ-ONLY", html)
        self.assertIn("Reward State Timeline", html)
        self.assertIn("Outcomes Snapshot", html)
        self.assertIn("Exchange Requests", html)
        self.assertIn("r-view", html)

    def test_viewer_reward_not_found(self) -> None:
        status, payload, _ = self._request_json(
            "GET",
            "/v0/viewer?reward_id=missing",
            headers=self._auth_headers(),
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "reward_not_found")


if __name__ == "__main__":
    unittest.main()
