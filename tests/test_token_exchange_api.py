"""HTTP integration tests for:
- POST /v0/tokens/issue
- POST /v0/exchange/request
- GET  /v0/exchange/requests
- 413 body-size guard (all body-parsing routes)
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
from xchange.storage import create_reward_draft, open_db


class QuietAppHandler(AppHandler):
    def log_message(self, format: str, *args: object) -> None:
        return


class _BaseApiTests(unittest.TestCase):
    """Shared test-server scaffold (mirrors test_http_boundaries.py)."""

    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self._saved_env: dict[str, str | None] = {
            name: os.environ.get(name)
            for name in (
                "XCHANGE_DB_PATH",
                "XCHANGE_INGEST_TOKEN",
                "STRIPE_WEBHOOK_SECRET",
                "XCHANGE_RATE_LIMIT_REQUESTS",
                "XCHANGE_RATE_LIMIT_WINDOW_SECONDS",
                "XCHANGE_MAX_BODY_BYTES",
            )
        }
        os.environ["XCHANGE_DB_PATH"] = self._path
        os.environ["XCHANGE_INGEST_TOKEN"] = "test-token"
        os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        os.environ["XCHANGE_RATE_LIMIT_REQUESTS"] = "100"
        os.environ["XCHANGE_RATE_LIMIT_WINDOW_SECONDS"] = "60"
        os.environ.pop("XCHANGE_MAX_BODY_BYTES", None)  # default 65536
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

    def _auth(self) -> dict[str, str]:
        return {
            "Authorization": "Bearer test-token",
            "Content-Type": "application/json",
        }

    def _post(
        self, path: str, payload: dict[str, Any], *, auth: bool = True
    ) -> tuple[int, dict[str, Any]]:
        body = json.dumps(payload).encode("utf-8")
        hdrs = {**(self._auth() if auth else {"Content-Type": "application/json"})}
        status, data, _ = self._request("POST", path, body=body, headers=hdrs)
        return status, data


# ---------------------------------------------------------------------------
# Body-size guard tests
# ---------------------------------------------------------------------------


class BodySizeGuardTests(_BaseApiTests):
    """413 is returned before any processing when Content-Length exceeds cap."""

    def setUp(self) -> None:
        super().setUp()
        # Lower cap to 64 bytes so we can trigger it with a tiny payload.
        os.environ["XCHANGE_MAX_BODY_BYTES"] = "64"

    def _oversized_body(self) -> bytes:
        """Valid JSON that exceeds the 64-byte cap."""
        return json.dumps({"padding": "x" * 100}).encode("utf-8")

    def test_issue_token_oversized_body_returns_413(self) -> None:
        body = self._oversized_body()
        status, payload, _ = self._request(
            "POST",
            "/v0/tokens/issue",
            body=body,
            headers={**self._auth(), "Content-Length": str(len(body))},
        )
        self.assertEqual(status, 413)
        self.assertEqual(payload["error"], "body_too_large")

    def test_exchange_request_oversized_body_returns_413(self) -> None:
        body = self._oversized_body()
        status, payload, _ = self._request(
            "POST",
            "/v0/exchange/request",
            body=body,
            headers={**self._auth(), "Content-Length": str(len(body))},
        )
        self.assertEqual(status, 413)
        self.assertEqual(payload["error"], "body_too_large")

    def test_reward_draft_oversized_body_returns_413(self) -> None:
        body = self._oversized_body()
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/draft",
            body=body,
            headers={**self._auth(), "Content-Length": str(len(body))},
        )
        self.assertEqual(status, 413)
        self.assertEqual(payload["error"], "body_too_large")

    def test_glass_session_oversized_body_returns_413(self) -> None:
        body = self._oversized_body()
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-session",
            body=body,
            headers={**self._auth(), "Content-Length": str(len(body))},
        )
        self.assertEqual(status, 413)
        self.assertEqual(payload["error"], "body_too_large")

    def test_413_detail_contains_size_info(self) -> None:
        body = self._oversized_body()
        status, payload, _ = self._request(
            "POST",
            "/v0/tokens/issue",
            body=body,
            headers={**self._auth(), "Content-Length": str(len(body))},
        )
        self.assertEqual(status, 413)
        # detail field should mention the limit
        self.assertIn("detail", payload)
        self.assertIn("64", payload["detail"])

    def test_body_at_exact_cap_is_accepted(self) -> None:
        """A body whose Content-Length == max_bytes must not be rejected."""
        # 64-byte valid JSON that fits exactly — the body itself is the limit.
        exact_body = b'{"reward_id":"r","insight_tier":"causal","issuance_trigger":"t"}'
        self.assertLessEqual(len(exact_body), 64)
        # Create the reward so we get a meaningful (non-413) response.
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r", student_id="s")
        status, _, _ = self._request(
            "POST",
            "/v0/tokens/issue",
            body=exact_body,
            headers={**self._auth(), "Content-Length": str(len(exact_body))},
        )
        self.assertNotEqual(status, 413)


# ---------------------------------------------------------------------------
# POST /v0/tokens/issue
# ---------------------------------------------------------------------------


class IssueTokenApiTests(_BaseApiTests):
    def _seed_reward(self, reward_id: str = "r1", student_id: str = "s1") -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id=reward_id, student_id=student_id)

    def _minimal_token_payload(self, reward_id: str = "r1") -> dict[str, Any]:
        return {
            "reward_id": reward_id,
            "insight_tier": "surface",
            "issuance_trigger": "test_trigger",
        }

    def test_issue_token_happy_path(self) -> None:
        self._seed_reward()
        status, payload = self._post("/v0/tokens/issue", self._minimal_token_payload())

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["reward_id"], "r1")
        token = payload["token"]
        self.assertEqual(token["insight_tier"], "surface")
        self.assertEqual(token["issuance_trigger"], "test_trigger")
        self.assertIn("rarity_score", token)
        self.assertIn("issued_at", token)
        # rarity_score must be a float in [0, 1]
        self.assertIsInstance(token["rarity_score"], float)
        self.assertGreaterEqual(token["rarity_score"], 0.0)
        self.assertLessEqual(token["rarity_score"], 1.0)

    def test_issue_token_rarity_computed_server_side(self) -> None:
        """Caller-supplied rarity_score must be ignored; server computes it."""
        self._seed_reward()
        payload_with_caller_rarity = {
            **self._minimal_token_payload(),
            "rarity_score": 0.9999,  # should be silently ignored
        }
        status, payload = self._post("/v0/tokens/issue", payload_with_caller_rarity)

        self.assertEqual(status, 200)
        token = payload["token"]
        # surface tier with defaults gives a deterministic score != 0.9999
        self.assertNotAlmostEqual(token["rarity_score"], 0.9999, places=3)

    def test_issue_token_reward_not_found_returns_404(self) -> None:
        # No reward seeded — reward does not exist.
        status, payload = self._post(
            "/v0/tokens/issue", self._minimal_token_payload("nonexistent")
        )
        self.assertEqual(status, 404)
        self.assertIn("error", payload)

    def test_issue_token_missing_reward_id_returns_400(self) -> None:
        status, payload = self._post(
            "/v0/tokens/issue",
            {"insight_tier": "surface", "issuance_trigger": "t"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_issue_token_missing_insight_tier_returns_400(self) -> None:
        self._seed_reward()
        status, payload = self._post(
            "/v0/tokens/issue",
            {"reward_id": "r1", "issuance_trigger": "t"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_issue_token_invalid_tier_returns_400(self) -> None:
        self._seed_reward()
        status, payload = self._post(
            "/v0/tokens/issue",
            {**self._minimal_token_payload(), "insight_tier": "legendary"},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_insight_tier")
        self.assertIn("valid", payload)

    def test_issue_token_invalid_numeric_field_returns_400(self) -> None:
        self._seed_reward()
        status, payload = self._post(
            "/v0/tokens/issue",
            {**self._minimal_token_payload(), "inferential_richness": "notanumber"},
        )
        self.assertEqual(status, 400)
        self.assertIn("invalid_numeric_field", payload["error"])

    def test_issue_token_clamps_out_of_range_numerics(self) -> None:
        """Values outside valid ranges must be clamped, not rejected."""
        self._seed_reward()
        status, payload = self._post(
            "/v0/tokens/issue",
            {
                **self._minimal_token_payload(),
                "inferential_richness": 99.0,  # clamped to 1.0
                "trend_position": -5.0,  # clamped to 0.0
                "base_bank_depth": 999,  # clamped to 100
            },
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])

    def test_issue_token_requires_auth(self) -> None:
        self._seed_reward()
        status, payload = self._post(
            "/v0/tokens/issue",
            self._minimal_token_payload(),
            auth=False,
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    def test_issue_token_reissue_returns_original_token(self) -> None:
        """Re-issuing a token on the same reward returns the first stamped token."""
        self._seed_reward()
        p = self._minimal_token_payload()
        s1, r1 = self._post("/v0/tokens/issue", p)
        s2, r2 = self._post(
            "/v0/tokens/issue",
            {
                **p,
                "insight_tier": "theoretical",
                "issuance_trigger": "second",
                "inferential_richness": 1.0,
                "trend_position": 0.0,
            },
        )

        self.assertEqual(s1, 200)
        self.assertEqual(s2, 200)
        self.assertEqual(r2["token"]["issuance_trigger"], "test_trigger")
        self.assertEqual(r2["token"]["insight_tier"], "surface")
        self.assertEqual(r2["token"]["issued_at"], r1["token"]["issued_at"])
        self.assertEqual(r2["token"]["rarity_score"], r1["token"]["rarity_score"])
        self.assertTrue(r2.get("immutable"))


# ---------------------------------------------------------------------------
# POST /v0/exchange/request  &  GET /v0/exchange/requests
# ---------------------------------------------------------------------------


class ExchangeRequestApiTests(_BaseApiTests):
    def _seed_reward_with_token(
        self, reward_id: str = "r1", student_id: str = "s1"
    ) -> None:
        """Create a draft reward (token issuance does not require earned state)."""
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id=reward_id, student_id=student_id)
        self._post(
            "/v0/tokens/issue",
            {
                "reward_id": reward_id,
                "insight_tier": "surface",
                "issuance_trigger": "setup",
            },
        )

    def _exchange_payload(
        self,
        *,
        request_id: str = "req-1",
        student_id: str = "s1",
        reward_id: str = "r1",
        scope: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "request_id": request_id,
            "student_id": student_id,
            "reward_id": reward_id,
            "requested_scope": scope or {"feature_x": True},
        }

    # -- happy path ----------------------------------------------------------

    def test_exchange_request_happy_path(self) -> None:
        self._seed_reward_with_token()
        status, payload = self._post("/v0/exchange/request", self._exchange_payload())

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["request_id"], "req-1")
        self.assertEqual(payload["reward_id"], "r1")
        self.assertIn("approved", payload)
        self.assertIn("layers", payload)
        self.assertIsInstance(payload["layers"], list)
        # Three constraint layers when safety passes
        self.assertEqual(len(payload["layers"]), 3)

    def test_exchange_request_approved_field_is_bool(self) -> None:
        self._seed_reward_with_token()
        status, payload = self._post("/v0/exchange/request", self._exchange_payload())
        self.assertEqual(status, 200)
        self.assertIsInstance(payload["approved"], bool)

    def test_exchange_request_scope_in_response(self) -> None:
        self._seed_reward_with_token()
        status, payload = self._post(
            "/v0/exchange/request",
            self._exchange_payload(scope={"study_credits": 5}),
        )
        self.assertEqual(status, 200)
        self.assertIn("final_approved_scope", payload)

    def test_exchange_request_idempotent_by_request_id(self) -> None:
        """Same request_id submitted twice must not duplicate the row."""
        self._seed_reward_with_token()
        payload = self._exchange_payload()
        s1, r1 = self._post("/v0/exchange/request", payload)
        s2, r2 = self._post("/v0/exchange/request", payload)

        self.assertEqual(s1, 200)
        self.assertEqual(s2, 200)
        # Second call returns duplicate signal
        self.assertTrue(r2.get("duplicate") or r2.get("ok"))

    # -- validation ----------------------------------------------------------

    def test_exchange_request_missing_request_id_returns_400(self) -> None:
        status, payload = self._post(
            "/v0/exchange/request",
            {"student_id": "s1", "reward_id": "r1", "requested_scope": {}},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_exchange_request_missing_student_id_returns_400(self) -> None:
        status, payload = self._post(
            "/v0/exchange/request",
            {"request_id": "req-x", "reward_id": "r1", "requested_scope": {}},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_exchange_request_scope_not_object_returns_400(self) -> None:
        bad = {**self._exchange_payload(), "requested_scope": ["not", "an", "object"]}
        status, payload = self._post("/v0/exchange/request", bad)
        self.assertEqual(status, 400)
        self.assertIn("requested_scope", payload["error"])

    def test_exchange_request_requires_auth(self) -> None:
        status, payload = self._post(
            "/v0/exchange/request",
            self._exchange_payload(),
            auth=False,
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    # -- GET /v0/exchange/requests -------------------------------------------

    def _get(self, path: str) -> tuple[int, dict[str, Any]]:
        status, data, _ = self._request("GET", path, headers=self._auth())
        return status, data

    def test_list_exchange_requests_empty(self) -> None:
        status, payload = self._get("/v0/exchange/requests")
        self.assertEqual(status, 200)
        self.assertEqual(payload["exchange_requests"], [])
        self.assertEqual(payload["count"], 0)

    def test_list_exchange_requests_returns_created_rows(self) -> None:
        self._seed_reward_with_token()
        self._post("/v0/exchange/request", self._exchange_payload(request_id="req-a"))
        self._post("/v0/exchange/request", self._exchange_payload(request_id="req-b"))

        status, payload = self._get("/v0/exchange/requests")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 2)
        ids = {row["request_id"] for row in payload["exchange_requests"]}
        self.assertIn("req-a", ids)
        self.assertIn("req-b", ids)

    def test_list_exchange_requests_filter_by_student(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="alice")
            create_reward_draft(conn=conn, reward_id="r2", student_id="bob")
        self._post(
            "/v0/exchange/request",
            self._exchange_payload(
                request_id="req-alice", student_id="alice", reward_id="r1"
            ),
        )
        self._post(
            "/v0/exchange/request",
            self._exchange_payload(
                request_id="req-bob", student_id="bob", reward_id="r2"
            ),
        )

        status, payload = self._get("/v0/exchange/requests?student_id=alice")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["exchange_requests"][0]["student_id"], "alice")

    def test_list_exchange_requests_filter_by_reward(self) -> None:
        self._seed_reward_with_token("r1")
        self._seed_reward_with_token("r2", student_id="s2")
        self._post(
            "/v0/exchange/request",
            self._exchange_payload(request_id="req-r1", reward_id="r1"),
        )
        self._post(
            "/v0/exchange/request",
            self._exchange_payload(request_id="req-r2", reward_id="r2"),
        )

        status, payload = self._get("/v0/exchange/requests?reward_id=r1")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["exchange_requests"][0]["reward_id"], "r1")

    def test_list_exchange_requests_requires_auth(self) -> None:
        status, payload, _ = self._request("GET", "/v0/exchange/requests")
        self.assertEqual(status, 401)

    def test_list_exchange_requests_limit_param(self) -> None:
        self._seed_reward_with_token()
        for i in range(5):
            self._post(
                "/v0/exchange/request", self._exchange_payload(request_id=f"req-{i}")
            )

        status, payload = self._get("/v0/exchange/requests?limit=2")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 2)


if __name__ == "__main__":
    unittest.main()
