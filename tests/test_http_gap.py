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
from xchange.storage import (
    create_reward_draft,
    ingest_glass_session,
    insert_support_signal,
    open_db,
    process_stripe_payment_intent_succeeded,
    record_failure,
    resolve_support_signal,
)


class QuietAppHandler(AppHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class _BaseHttpCase(unittest.TestCase):
    """Shared live-server setup for all HTTP gap tests."""

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


# ---------------------------------------------------------------------------
# Group 1: Unknown paths → 404
# ---------------------------------------------------------------------------


class UnknownPathTests(_BaseHttpCase):
    def test_get_unknown_path_returns_404(self) -> None:
        status, payload, _ = self._request("GET", "/v0/totally/unknown")
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "not_found")

    def test_post_unknown_path_returns_404(self) -> None:
        body = json.dumps({}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/unknown",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "not_found")


# ---------------------------------------------------------------------------
# Group 2: GET /v0/state/reward/<id> — reward not found
# ---------------------------------------------------------------------------


class RewardStateNotFoundTests(_BaseHttpCase):
    def test_get_reward_state_not_found_returns_404(self) -> None:
        status, payload, _ = self._request(
            "GET",
            "/v0/state/reward/nonexistent",
            headers=self._auth_headers(),
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "reward_not_found")


# ---------------------------------------------------------------------------
# Group 3: GET /v0/support-signals — _handle_list_support_signals
# ---------------------------------------------------------------------------


class ListSupportSignalsTests(_BaseHttpCase):
    def test_list_support_signals_requires_auth(self) -> None:
        status, payload, _ = self._request("GET", "/v0/support-signals")
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")

    def test_list_support_signals_empty(self) -> None:
        status, payload, _ = self._request(
            "GET", "/v0/support-signals", headers=self._auth_headers()
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["signals"], [])
        self.assertEqual(payload["count"], 0)

    def test_list_support_signals_with_kind_filter(self) -> None:
        with open_db(self._path) as conn:
            insert_support_signal(conn=conn, kind="kindA", payload={"x": 1})
            insert_support_signal(conn=conn, kind="kindB", payload={"x": 2})

        status, payload, _ = self._request(
            "GET",
            "/v0/support-signals?kind=kindA",
            headers=self._auth_headers(),
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["signals"][0]["kind"], "kindA")

    def test_list_support_signals_invalid_limit_uses_default(self) -> None:
        # Non-integer limit must not crash — server falls back to 50.
        status, payload, _ = self._request(
            "GET",
            "/v0/support-signals?limit=notanint",
            headers=self._auth_headers(),
        )
        self.assertEqual(status, 200)
        self.assertIn("signals", payload)
        self.assertIn("count", payload)


# ---------------------------------------------------------------------------
# Group 4: POST /v0/support-signals/<id>/resolve
# ---------------------------------------------------------------------------


class ResolveSupportSignalTests(_BaseHttpCase):
    def test_resolve_support_signal_success(self) -> None:
        with open_db(self._path) as conn:
            signal_id = insert_support_signal(
                conn=conn, kind="test_kind", payload={"key": "value"}
            )

        body = json.dumps({"resolution_note": "fixed"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            f"/v0/support-signals/{signal_id}/resolve",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])

    def test_resolve_support_signal_not_found(self) -> None:
        body = json.dumps({"resolution_note": "noop"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/support-signals/99999/resolve",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 404)
        self.assertEqual(payload["error"], "signal_not_found")

    def test_resolve_support_signal_invalid_id(self) -> None:
        body = json.dumps({"resolution_note": "noop"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/support-signals/not-an-int/resolve",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "invalid_signal_id")

    def test_resolve_support_signal_requires_auth(self) -> None:
        body = json.dumps({"resolution_note": "noop"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/support-signals/1/resolve",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")


# ---------------------------------------------------------------------------
# Group 5: POST /v0/rewards/draft — _handle_reward_draft
# ---------------------------------------------------------------------------


class RewardDraftTests(_BaseHttpCase):
    def test_reward_draft_happy_path(self) -> None:
        body = json.dumps({"reward_id": "r1", "student_id": "s1"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/draft",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])

    def test_reward_draft_missing_fields_returns_400(self) -> None:
        body = json.dumps({}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/draft",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_reward_draft_requires_auth(self) -> None:
        body = json.dumps({"reward_id": "r1", "student_id": "s1"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/draft",
            body=body,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")


# ---------------------------------------------------------------------------
# Group 6: POST /v0/rewards/<id>/acknowledge — _handle_acknowledge_reward
# ---------------------------------------------------------------------------


class AcknowledgeRewardTests(_BaseHttpCase):
    def _setup_payment_confirmed(
        self, *, reward_id: str = "r1", student_id: str = "s1"
    ) -> None:
        """Create a reward and move it all the way to payment_confirmed."""
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id=reward_id, student_id=student_id)
            # earned → payment_pending in one ingest call
            ingest_glass_session(
                conn=conn,
                session_id=f"setup-{reward_id}",
                student_id=student_id,
                payload={
                    "reward_id": reward_id,
                    "contract_satisfied": True,
                    "ready_for_payment": True,
                },
            )
            # payment_pending → payment_confirmed via storage helper
            process_stripe_payment_intent_succeeded(
                conn=conn,
                stripe_event_id=f"evt_setup_{reward_id}",
                stripe_payment_intent_id=f"pi_setup_{reward_id}",
                reward_id=reward_id,
                student_id=student_id,
                raw_event={},
            )

    def test_acknowledge_reward_happy_path_via_http(self) -> None:
        self._setup_payment_confirmed(reward_id="r1", student_id="s1")

        body = json.dumps({"student_id": "s1"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/r1/acknowledge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])

    def test_acknowledge_reward_missing_student_id_returns_400(self) -> None:
        self._setup_payment_confirmed(reward_id="r2", student_id="s2")

        body = json.dumps({}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/r2/acknowledge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_acknowledge_reward_wrong_state_returns_409(self) -> None:
        # Reward is only drafted — acknowledging it requires payment_confirmed.
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r3", student_id="s3")

        body = json.dumps({"student_id": "s3"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/r3/acknowledge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 409)
        self.assertEqual(payload["error"], "ack_requires_payment_confirmed")

    def test_acknowledge_reward_not_found_returns_400(self) -> None:
        # reward_not_found is not a CONFLICT error, so main.py returns 400.
        body = json.dumps({"student_id": "s1"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/nonexistent/acknowledge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "reward_not_found")


# ---------------------------------------------------------------------------
# Group 7: POST /v0/ingest/glass-session — _handle_ingest_glass_session
# ---------------------------------------------------------------------------


class GlassSessionTests(_BaseHttpCase):
    def test_glass_session_missing_fields_returns_400(self) -> None:
        body = json.dumps({}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-session",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")


# ---------------------------------------------------------------------------
# Group 8: POST /v0/ingest/glass-bridge — _handle_ingest_glass_bridge
# ---------------------------------------------------------------------------


class GlassBridgeTests(_BaseHttpCase):
    def test_glass_bridge_missing_bridge_returns_400(self) -> None:
        # Payload has student_id but no "bridge" key at all.
        body = json.dumps({"student_id": "s1"}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-bridge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_or_invalid_bridge")

    def test_glass_bridge_missing_student_id_returns_400(self) -> None:
        # bridge is present, but student_id is absent.
        body = json.dumps({"bridge": {"session_id": "s1"}}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-bridge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_glass_bridge_mapper_error_returns_400(self) -> None:
        # bridge dict is valid JSON object but lacks session_id — the
        # map_glass_bridge_to_ingest adapter raises ValueError.
        body = json.dumps({"student_id": "s1", "bridge": {}}).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-bridge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        # Exact message comes from the adapter; just confirm it's a 400.
        self.assertIn("error", payload)


# ---------------------------------------------------------------------------
# Group 9: POST /v0/stripe/webhook — varied scenarios
# ---------------------------------------------------------------------------


class StripeWebhookTests(_BaseHttpCase):
    def test_stripe_webhook_missing_secret_returns_500(self) -> None:
        saved = os.environ.pop("STRIPE_WEBHOOK_SECRET", None)
        try:
            body = json.dumps(
                {"id": "evt_x", "type": "noop", "data": {"object": {}}}
            ).encode("utf-8")
            status, payload, _ = self._request(
                "POST",
                "/v0/stripe/webhook",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": "t=1,v1=abc",
                },
            )
            self.assertEqual(status, 500)
            self.assertEqual(payload["error"], "missing_STRIPE_WEBHOOK_SECRET")
        finally:
            if saved is not None:
                os.environ["STRIPE_WEBHOOK_SECRET"] = saved

    def test_stripe_webhook_invalid_json_returns_400(self) -> None:
        body = b"not json at all"
        status, payload, _ = self._request(
            "POST",
            "/v0/stripe/webhook",
            body=body,
            headers=self._stripe_headers(body),
        )
        self.assertEqual(status, 400)
        self.assertTrue(
            payload["error"].startswith("invalid_json"),
            msg=f"Expected 'invalid_json...' but got: {payload['error']!r}",
        )

    def test_stripe_webhook_payment_intent_succeeded_missing_metadata(self) -> None:
        # Valid event type, event_id present, but metadata has no reward_id/student_id.
        event = {
            "id": "evt_missing_meta",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_x", "metadata": {}}},
        }
        body = json.dumps(event).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/stripe/webhook",
            body=body,
            headers=self._stripe_headers(body),
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["accepted"])
        self.assertEqual(payload["reason"], "missing_metadata")

    def test_stripe_webhook_payment_intent_succeeded_applies_payment(self) -> None:
        # Set up reward at payment_pending via storage helpers.
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r-apply", student_id="s-apply")
            ingest_glass_session(
                conn=conn,
                session_id="setup-apply",
                student_id="s-apply",
                payload={
                    "reward_id": "r-apply",
                    "contract_satisfied": True,
                    "ready_for_payment": True,
                },
            )

        event = {
            "id": "evt_apply_1",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_apply_1",
                    "metadata": {
                        "reward_id": "r-apply",
                        "student_id": "s-apply",
                    },
                }
            },
        }
        body = json.dumps(event).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/stripe/webhook",
            body=body,
            headers=self._stripe_headers(body),
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["applied"])

    def test_stripe_webhook_payment_intent_succeeded_with_nudge(self) -> None:
        # Set up reward at payment_pending and record a failure for the student.
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r-nudge", student_id="s-nudge")
            ingest_glass_session(
                conn=conn,
                session_id="setup-nudge",
                student_id="s-nudge",
                payload={
                    "reward_id": "r-nudge",
                    "contract_satisfied": True,
                    "ready_for_payment": True,
                },
            )
            record_failure(
                conn=conn,
                session_id="fail-nudge",
                student_id="s-nudge",
                failure={"command": "git push origin main", "exit_code": 1},
            )

        event = {
            "id": "evt_nudge_1",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_nudge_1",
                    "metadata": {
                        "reward_id": "r-nudge",
                        "student_id": "s-nudge",
                    },
                }
            },
        }
        body = json.dumps(event).encode("utf-8")
        status, payload, _ = self._request(
            "POST",
            "/v0/stripe/webhook",
            body=body,
            headers=self._stripe_headers(body),
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["applied"])

        # Verify nudge row was created in the database.
        with open_db(self._path) as conn:
            row = conn.execute(
                "SELECT * FROM nudges WHERE student_id='s-nudge' AND reward_id='r-nudge'"
            ).fetchone()
        self.assertIsNotNone(
            row, "nudge row should exist after payment applied with failure on record"
        )


# ---------------------------------------------------------------------------
# Group 10: _read_json_body / _parse_body edge cases
# ---------------------------------------------------------------------------


class ParseBodyEdgeCaseTests(_BaseHttpCase):
    """Cover _read_json_body lines 94-95, 101, 106-107 and _parse_body 126-132."""

    def test_absent_content_length_defaults_to_empty_body(self) -> None:
        # body=None → http.client omits Content-Length → length_str is None
        # → L101 else branch → raw = b"{}" → parsed as {} → missing fields → 400
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-session",
            body=None,
            headers=self._auth_headers(),
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_required_fields")

    def test_invalid_content_length_header_falls_back_to_zero(self) -> None:
        # Non-integer Content-Length → L94-95 except ValueError → length=0 → raw=b"{}"
        body = json.dumps({"session_id": "s", "student_id": "x"}).encode()
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-session",
            body=body,
            headers={"Content-Length": "not-an-int", **self._auth_headers()},
        )
        # length=0 → raw=b"{}" → missing fields → 400
        self.assertEqual(status, 400)

    def test_invalid_json_body_returns_400(self) -> None:
        # Valid Content-Length but body is not JSON → L106-107 ValueError → L126-132 400
        raw_body = b"not valid json at all"
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/draft",
            body=raw_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(raw_body)),
                **self._auth_headers(),
            },
        )
        self.assertEqual(status, 400)
        self.assertIn("error", payload)


# ---------------------------------------------------------------------------
# Group 11: list_support_signals ?resolved= filter (L307)
# ---------------------------------------------------------------------------


class SupportSignalsResolvedFilterTests(_BaseHttpCase):
    def test_resolved_filter_true(self) -> None:
        with open_db(self._path) as conn:
            sid = insert_support_signal(conn=conn, kind="k", payload={"x": 1})
            resolve_support_signal(conn=conn, signal_id=sid, resolution_note="done")
            insert_support_signal(conn=conn, kind="k", payload={"x": 2})  # unresolved

        status, payload, _ = self._request(
            "GET", "/v0/support-signals?resolved=true", headers=self._auth_headers()
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 1)
        self.assertIsNotNone(payload["signals"][0]["resolved_at"])

    def test_resolved_filter_false(self) -> None:
        with open_db(self._path) as conn:
            sid = insert_support_signal(conn=conn, kind="k", payload={"x": 1})
            resolve_support_signal(conn=conn, signal_id=sid, resolution_note="done")
            insert_support_signal(conn=conn, kind="k", payload={"x": 2})  # unresolved

        status, payload, _ = self._request(
            "GET", "/v0/support-signals?resolved=false", headers=self._auth_headers()
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], 1)
        self.assertIsNone(payload["signals"][0]["resolved_at"])


# ---------------------------------------------------------------------------
# Group 12: resolve signal — missing signal_id (L349-354) + invalid JSON body (L368)
# ---------------------------------------------------------------------------


class ResolveSupportSignalEdgeCaseTests(_BaseHttpCase):
    def test_missing_signal_id_segment_returns_400(self) -> None:
        # Path ends with //resolve so the id segment is empty string → missing_signal_id
        body = json.dumps({"resolution_note": "x"}).encode()
        status, payload, _ = self._request(
            "POST",
            "/v0/support-signals//resolve",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_signal_id")

    def test_invalid_json_body_in_resolve_returns_400(self) -> None:
        # Valid integer id but invalid JSON body → _parse_body returns None → 400
        with open_db(self._path) as conn:
            sid = insert_support_signal(conn=conn, kind="k", payload={})
        raw_body = b"not json"
        status, payload, _ = self._request(
            "POST",
            f"/v0/support-signals/{sid}/resolve",
            body=raw_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(raw_body)),
                **self._auth_headers(),
            },
        )
        self.assertEqual(status, 400)


# ---------------------------------------------------------------------------
# Group 13: acknowledge reward — empty reward_id (L390) + invalid JSON body (L396-401)
# ---------------------------------------------------------------------------


class AcknowledgeRewardEdgeCaseTests(_BaseHttpCase):
    def test_empty_reward_id_segment_returns_400(self) -> None:
        # /v0/rewards//acknowledge → parts[3]="" → falsy → missing_reward_id
        body = json.dumps({"student_id": "s1"}).encode()
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards//acknowledge",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "missing_reward_id")

    def test_invalid_json_body_in_acknowledge_returns_400(self) -> None:
        # Valid reward_id in path but invalid JSON body → _parse_body returns None → 400
        raw_body = b"not json"
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/r1/acknowledge",
            body=raw_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(raw_body)),
                **self._auth_headers(),
            },
        )
        self.assertEqual(status, 400)


# ---------------------------------------------------------------------------
# Group 14: reward draft — bad reward_token_amount (L460-461)
# ---------------------------------------------------------------------------


class RewardDraftAmountParseTests(_BaseHttpCase):
    def test_non_integer_reward_token_amount_defaults_to_one(self) -> None:
        body = json.dumps(
            {
                "reward_id": "r_amt",
                "student_id": "s1",
                "reward_token_amount": "not-an-int",
            }
        ).encode()
        status, payload, _ = self._request(
            "POST",
            "/v0/rewards/draft",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])


# ---------------------------------------------------------------------------
# Group 15: glass-session success path (L497-504)
# ---------------------------------------------------------------------------


class GlassSessionSuccessTests(_BaseHttpCase):
    def test_glass_session_happy_path_returns_200(self) -> None:
        body = json.dumps({"session_id": "sess-http-1", "student_id": "stu1"}).encode()
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-session",
            body=body,
            headers={"Content-Type": "application/json", **self._auth_headers()},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["evidence_recorded"])


# ---------------------------------------------------------------------------
# Group 16: glass-bridge payload=None (L512)
# ---------------------------------------------------------------------------


class GlassBridgeInvalidBodyTests(_BaseHttpCase):
    def test_invalid_json_body_returns_400(self) -> None:
        raw_body = b"not json"
        status, payload, _ = self._request(
            "POST",
            "/v0/ingest/glass-bridge",
            body=raw_body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(raw_body)),
                **self._auth_headers(),
            },
        )
        self.assertEqual(status, 400)


# ---------------------------------------------------------------------------
# Group 17: stripe webhook — oversized body (L575-580)
# ---------------------------------------------------------------------------


class StripeWebhookBodySizeTests(_BaseHttpCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ["XCHANGE_MAX_BODY_BYTES"] = "64"  # tiny cap for the test
        self._saved_env["XCHANGE_MAX_BODY_BYTES"] = None  # ensure cleanup removes it

    def test_oversized_stripe_body_returns_413(self) -> None:
        # Claim a large Content-Length to trigger the size guard before signature check
        oversized = b"x" * 200
        status, payload, _ = self._request(
            "POST",
            "/v0/stripe/webhook",
            body=oversized,
            headers={"Content-Length": "200"},
        )
        self.assertEqual(status, 413)
        self.assertEqual(payload["error"], "body_too_large")


# ---------------------------------------------------------------------------
# Group 18: list exchange requests — ?approved= filter + invalid limit (L873, 877-878)
# ---------------------------------------------------------------------------


class ListExchangeRequestsHttpTests(_BaseHttpCase):
    def test_approved_filter_query_param(self) -> None:
        status, payload, _ = self._request(
            "GET",
            "/v0/exchange/requests?approved=true",
            headers=self._auth_headers(),
        )
        self.assertEqual(status, 200)
        self.assertIn("exchange_requests", payload)

    def test_invalid_limit_query_param_uses_default(self) -> None:
        status, payload, _ = self._request(
            "GET",
            "/v0/exchange/requests?limit=notanint",
            headers=self._auth_headers(),
        )
        self.assertEqual(status, 200)
        self.assertIn("exchange_requests", payload)


if __name__ == "__main__":
    unittest.main()
