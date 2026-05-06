"""Tests for PATCH /v0/evidence/<id> — retroactive reward_id association.

Phase 4 ticket: evidence rows recorded without a reward_id (evidence-only
ingest path) can be linked to a reward after the fact.
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
from xchange.storage import (
    append_evidence,
    create_reward_draft,
    open_db,
)
from xchange.domain import EvidenceType


class QuietAppHandler(AppHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class EvidencePatchTests(unittest.TestCase):
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

    def _auth_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {"Authorization": "Bearer test-token", "Content-Type": "application/json"}
        if extra:
            h.update(extra)
        return h

    def _patch(self, path: str, body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        return self._request(
            "PATCH",
            path,
            body=json.dumps(body).encode("utf-8"),
            headers=self._auth_headers(),
        )

    def _seed_unlinked_evidence(self) -> int:
        """Insert an evidence row with no reward_id; return its id."""
        with open_db(self._path) as conn:
            eid = append_evidence(
                conn=conn,
                student_id="stu-001",
                session_id="sess-001",
                reward_id=None,
                evidence_type=EvidenceType.GLASS_SESSION_EVENT,
                payload={"demo": True},
                provenance="glass_ingest",
            )
        return eid

    def _seed_reward(self, reward_id: str = "rwd-001") -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id=reward_id, student_id="stu-001")

    # ------------------------------------------------------------------ happy path

    def test_links_unlinked_evidence_to_reward(self) -> None:
        eid = self._seed_unlinked_evidence()
        self._seed_reward("rwd-001")

        status, payload = self._patch(f"/v0/evidence/{eid}", {"reward_id": "rwd-001"})

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["evidence_id"], eid)
        self.assertEqual(payload["reward_id"], "rwd-001")

    # ------------------------------------------------------------------ auth guard

    def test_requires_auth(self) -> None:
        eid = self._seed_unlinked_evidence()
        self._seed_reward()

        status, payload = self._request(
            "PATCH",
            f"/v0/evidence/{eid}",
            body=json.dumps({"reward_id": "rwd-001"}).encode("utf-8"),
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    # ------------------------------------------------------------------ not-found

    def test_evidence_not_found(self) -> None:
        self._seed_reward()
        status, payload = self._patch("/v0/evidence/99999", {"reward_id": "rwd-001"})
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "evidence_not_found")

    def test_reward_not_found(self) -> None:
        eid = self._seed_unlinked_evidence()
        status, payload = self._patch(f"/v0/evidence/{eid}", {"reward_id": "does-not-exist"})
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "reward_not_found")

    # ------------------------------------------------------------------ conflict

    def test_already_linked_returns_conflict(self) -> None:
        """Evidence that already has a reward_id returns 409 Conflict."""
        self._seed_reward("rwd-a")
        self._seed_reward("rwd-b")
        # Insert evidence already linked to rwd-a
        with open_db(self._path) as conn:
            eid = append_evidence(
                conn=conn,
                student_id="stu-001",
                session_id="sess-002",
                reward_id="rwd-a",
                evidence_type=EvidenceType.GLASS_SESSION_EVENT,
                payload={"demo": True},
                provenance="glass_ingest",
            )

        status, payload = self._patch(f"/v0/evidence/{eid}", {"reward_id": "rwd-b"})
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"], "already_linked")
        self.assertEqual(payload["linked_reward_id"], "rwd-a")

    # ------------------------------------------------------------------ bad input

    def test_missing_reward_id_in_body(self) -> None:
        eid = self._seed_unlinked_evidence()
        status, payload = self._patch(f"/v0/evidence/{eid}", {})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_invalid_evidence_id(self) -> None:
        self._seed_reward()
        status, payload = self._patch("/v0/evidence/not-a-number", {"reward_id": "rwd-001"})
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_evidence_id")

    def test_unknown_patch_path_returns_404(self) -> None:
        status, payload = self._patch("/v0/unknown/path", {"reward_id": "x"})
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
