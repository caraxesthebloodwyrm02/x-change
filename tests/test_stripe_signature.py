from __future__ import annotations

import hashlib
import hmac
import time
import unittest

from xchange.stripe_sig import verify_stripe_signature


class StripeSignatureTests(unittest.TestCase):
    def test_verify_signature_true(self) -> None:
        secret = "whsec_test_secret"
        payload_body = b'{"foo":"bar"}'
        t = str(int(time.time()))
        signed_payload = f"{t}.".encode("utf-8") + payload_body
        digest = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()
        sig_header = f"t={t}, v1={digest}"

        ok = verify_stripe_signature(
            payload_body=payload_body,
            sig_header=sig_header,
            stripe_secret=secret,
            tolerance_seconds=300,
        )
        self.assertTrue(ok)

    def test_verify_signature_false_wrong_secret(self) -> None:
        secret = "whsec_test_secret"
        other_secret = "whsec_wrong_secret"
        payload_body = b'{"foo":"bar"}'
        t = str(int(time.time()))
        signed_payload = f"{t}.".encode("utf-8") + payload_body
        digest = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()
        sig_header = f"t={t}, v1={digest}"

        ok = verify_stripe_signature(
            payload_body=payload_body,
            sig_header=sig_header,
            stripe_secret=other_secret,
            tolerance_seconds=300,
        )
        self.assertFalse(ok)

    def test_stale_timestamp_exceeds_tolerance(self) -> None:
        """Signature with stale timestamp (>tolerance) should fail."""
        secret = "whsec_test_secret"
        payload_body = b'{"foo":"bar"}'
        # Timestamp 600 seconds in the past, but tolerance is 300
        t = str(int(time.time()) - 600)
        signed_payload = f"{t}.".encode("utf-8") + payload_body
        digest = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()
        sig_header = f"t={t}, v1={digest}"

        ok = verify_stripe_signature(
            payload_body=payload_body,
            sig_header=sig_header,
            stripe_secret=secret,
            tolerance_seconds=300,
        )
        self.assertFalse(ok)

    def test_missing_v1_key(self) -> None:
        """Signature with only v0 key (no v1) is accepted by current implementation."""
        secret = "whsec_test_secret"
        payload_body = b'{"foo":"bar"}'
        t = str(int(time.time()))
        signed_payload = f"{t}.".encode("utf-8") + payload_body
        digest = hmac.new(
            secret.encode("utf-8"), signed_payload, hashlib.sha256
        ).hexdigest()
        # Only v0, no v1 - implementation accepts both v1 and v0
        sig_header = f"t={t}, v0={digest}"

        ok = verify_stripe_signature(
            payload_body=payload_body,
            sig_header=sig_header,
            stripe_secret=secret,
            tolerance_seconds=300,
        )
        # Current implementation accepts v0 (line 61-64 in stripe_sig.py)
        self.assertTrue(ok)

    def test_malformed_header_empty_string(self) -> None:
        """Empty signature header should fail."""
        ok = verify_stripe_signature(
            payload_body=b'{"foo":"bar"}',
            sig_header="",
            stripe_secret="whsec_test_secret",
            tolerance_seconds=300,
        )
        self.assertFalse(ok)

    def test_malformed_header_no_equals(self) -> None:
        """Malformed signature header (no = signs) should fail."""
        ok = verify_stripe_signature(
            payload_body=b'{"foo":"bar"}',
            sig_header="abc",
            stripe_secret="whsec_test_secret",
            tolerance_seconds=300,
        )
        self.assertFalse(ok)

    def test_malformed_header_t_only(self) -> None:
        """Signature header with only t= (no v1=) should fail."""
        t = str(int(time.time()))
        sig_header = f"t={t}"

        ok = verify_stripe_signature(
            payload_body=b'{"foo":"bar"}',
            sig_header=sig_header,
            stripe_secret="whsec_test_secret",
            tolerance_seconds=300,
        )
        self.assertFalse(ok)

    def test_missing_stripe_secret_returns_false(self) -> None:
        """verify_stripe_signature returns False immediately when secret is None or empty."""
        payload_body = b'{"foo":"bar"}'
        t = str(int(time.time()))
        signed_payload = f"{t}.".encode("utf-8") + payload_body
        digest = hmac.new(b"whsec_test", signed_payload, hashlib.sha256).hexdigest()
        sig_header = f"t={t},v1={digest}"

        self.assertFalse(
            verify_stripe_signature(
                payload_body=payload_body,
                sig_header=sig_header,
                stripe_secret=None,
                tolerance_seconds=300,
            )
        )
        self.assertFalse(
            verify_stripe_signature(
                payload_body=payload_body,
                sig_header=sig_header,
                stripe_secret="",
                tolerance_seconds=300,
            )
        )

    def test_non_integer_timestamp_returns_false(self) -> None:
        """Header with a non-integer t= value fails gracefully (covers except ValueError path)."""
        ok = verify_stripe_signature(
            payload_body=b'{"foo":"bar"}',
            sig_header="t=not_an_int,v1=abc123",
            stripe_secret="whsec_test_secret",
            tolerance_seconds=300,
        )
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
