"""Tests for webhook_events idempotency dedup (T1-4).

Covers:
  - storage: record_webhook_event returns True first call, False on repeat
  - storage: schema migration (table exists after init_db)
  - HTTP: duplicate event ID returns 200 {duplicate: True} without side effects
  - HTTP: missing-metadata event deduplicated on retry (support signal not duplicated)
  - HTTP: unsupported event type is deduplicated
"""
from __future__ import annotations

import hashlib
import hmac
import http.client
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from http.server import HTTPServer

from xchange.main import AppHandler, _reset_rate_limit_for_tests
from xchange.storage import (
    create_reward_draft,
    init_db,
    open_db,
    record_webhook_event,
)


# ── helpers ───────────────────────────────────────────────────────────────────

_WEBHOOK_SECRET = "whsec_test_webhook_secret"


def _sign_payload(body: bytes, secret: str = _WEBHOOK_SECRET) -> str:
    t = str(int(time.time()))
    signed = t.encode() + b"." + body
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={t},v1={sig}"


def _make_event(
    event_id: str = "evt_test_001",
    event_type: str = "checkout.session.completed",
    reward_id: str = "rwd-test",
    student_id: str = "stu-test",
    livemode: bool = False,
) -> bytes:
    evt = {
        "id": event_id,
        "type": event_type,
        "livemode": livemode,
        "data": {
            "object": {
                "payment_intent": "pi_test_001",
                "metadata": {"reward_id": reward_id, "student_id": student_id},
            }
        },
    }
    return json.dumps(evt).encode()


def _make_unsupported_event(event_id: str = "evt_unsupported_001") -> bytes:
    evt = {
        "id": event_id,
        "type": "customer.subscription.created",
        "livemode": False,
        "data": {"object": {}},
    }
    return json.dumps(evt).encode()


def _make_missing_meta_event(event_id: str = "evt_no_meta_001") -> bytes:
    evt = {
        "id": event_id,
        "type": "checkout.session.completed",
        "livemode": False,
        "data": {"object": {"payment_intent": "pi_test_no_meta", "metadata": {}}},
    }
    return json.dumps(evt).encode()


class QuietAppHandler(AppHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


# ── storage unit tests ────────────────────────────────────────────────────────


class WebhookDeduStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        with sqlite3.connect(self._path) as conn:
            conn.row_factory = sqlite3.Row
            init_db(conn)

    def tearDown(self) -> None:
        os.unlink(self._path)

    def _conn(self):
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        return conn

    def test_table_exists_after_init_db(self) -> None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='webhook_events'"
            ).fetchone()
        self.assertIsNotNone(row, "webhook_events table should exist after init_db")

    def test_first_call_returns_true(self) -> None:
        with self._conn() as conn:
            result = record_webhook_event(
                conn,
                stripe_event_id="evt_001",
                event_type="payment_intent.succeeded",
                livemode=False,
            )
        self.assertTrue(result)

    def test_second_call_same_id_returns_false(self) -> None:
        with self._conn() as conn:
            record_webhook_event(
                conn,
                stripe_event_id="evt_002",
                event_type="payment_intent.succeeded",
                livemode=False,
            )
            result = record_webhook_event(
                conn,
                stripe_event_id="evt_002",
                event_type="payment_intent.succeeded",
                livemode=False,
            )
        self.assertFalse(result)

    def test_different_ids_both_recorded(self) -> None:
        with self._conn() as conn:
            r1 = record_webhook_event(
                conn,
                stripe_event_id="evt_a",
                event_type="payment_intent.succeeded",
                livemode=False,
            )
            r2 = record_webhook_event(
                conn,
                stripe_event_id="evt_b",
                event_type="payment_intent.succeeded",
                livemode=False,
            )
        self.assertTrue(r1)
        self.assertTrue(r2)

    def test_row_written_correctly(self) -> None:
        with self._conn() as conn:
            record_webhook_event(
                conn,
                stripe_event_id="evt_meta_check",
                event_type="customer.updated",
                livemode=True,
            )
            row = conn.execute(
                "SELECT * FROM webhook_events WHERE stripe_event_id=?",
                ("evt_meta_check",),
            ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["event_type"], "customer.updated")
        self.assertEqual(row["livemode"], 1)


# ── HTTP integration tests ────────────────────────────────────────────────────


class WebhookDeduHTTPTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self._saved_env = {
            k: os.environ.get(k)
            for k in (
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
        os.environ["STRIPE_WEBHOOK_SECRET"] = _WEBHOOK_SECRET
        os.environ["XCHANGE_RATE_LIMIT_REQUESTS"] = "200"
        os.environ["XCHANGE_RATE_LIMIT_WINDOW_SECONDS"] = "60"
        os.environ.pop("XCHANGE_LIVE_MODE", None)
        _reset_rate_limit_for_tests()

        self.server = HTTPServer(("127.0.0.1", 0), QuietAppHandler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._cleanup)

    def _cleanup(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        _reset_rate_limit_for_tests()
        for k, v in self._saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        os.unlink(self._path)

    def _post_webhook(self, body: bytes) -> tuple[int, dict]:
        sig = _sign_payload(body)
        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        conn.request(
            "POST",
            "/v0/stripe/webhook",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": sig,
                "Content-Length": str(len(body)),
            },
        )
        resp = conn.getresponse()
        return resp.status, json.loads(resp.read())

    def _setup_reward(self, reward_id: str, student_id: str) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(
                conn=conn,
                reward_id=reward_id,
                student_id=student_id,
            )

    def test_duplicate_payment_succeeded_returns_200_duplicate(self) -> None:
        """Second send of the same event_id returns 200 {duplicate: True}."""
        self._setup_reward("rwd-test", "stu-test")
        body = _make_event("evt_dup_001")
        status1, body1 = self._post_webhook(body)
        status2, body2 = self._post_webhook(body)
        self.assertEqual(status1, 200)
        self.assertEqual(status2, 200)
        self.assertTrue(body2.get("duplicate"), f"expected duplicate=True, got {body2}")
        self.assertEqual(body2["stripe_event_id"], "evt_dup_001")

    def test_duplicate_does_not_reapply_payment(self) -> None:
        """Payment state is applied only once; duplicate does not change state."""
        self._setup_reward("rwd-dedup-apply", "stu-dedup-apply")
        body = _make_event("evt_dedup_apply", reward_id="rwd-dedup-apply", student_id="stu-dedup-apply")
        self._post_webhook(body)
        self._post_webhook(body)
        # Verify only one payment_confirmation row exists.
        with open_db(self._path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM payment_confirmations WHERE stripe_event_id=?",
                ("evt_dedup_apply",),
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_missing_metadata_not_duplicated_on_retry(self) -> None:
        """Missing-metadata event only creates one support signal even on retry."""
        body = _make_missing_meta_event("evt_no_meta_retry")
        self._post_webhook(body)
        self._post_webhook(body)
        with open_db(self._path) as conn:
            sigs = conn.execute(
                "SELECT COUNT(*) FROM support_signals WHERE kind='stripe_missing_metadata'"
            ).fetchone()[0]
        self.assertEqual(sigs, 1, f"expected 1 support signal, got {sigs}")

    def test_unsupported_event_type_deduplicated(self) -> None:
        """Unsupported event type sent twice does not create two webhook_events rows."""
        body = _make_unsupported_event("evt_unsupported_retry")
        s1, _ = self._post_webhook(body)
        s2, r2 = self._post_webhook(body)
        self.assertEqual(s1, 200)
        self.assertEqual(s2, 200)
        self.assertTrue(r2.get("duplicate"), f"expected duplicate on retry, got {r2}")
        with open_db(self._path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM webhook_events WHERE stripe_event_id=?",
                ("evt_unsupported_retry",),
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_unique_events_all_processed(self) -> None:
        """Three distinct event IDs each result in a separate webhook_events row."""
        self._setup_reward("rwd-multi", "stu-multi")
        for i in range(3):
            body = _make_event(f"evt_unique_{i}", reward_id="rwd-multi", student_id="stu-multi")
            status, _ = self._post_webhook(body)
            self.assertEqual(status, 200)
        with open_db(self._path) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM webhook_events WHERE stripe_event_id LIKE 'evt_unique_%'"
            ).fetchone()[0]
        self.assertEqual(count, 3)
