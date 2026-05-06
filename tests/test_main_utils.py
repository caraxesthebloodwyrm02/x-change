from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from xchange.domain import ConstraintConfig
from xchange.main import (
    AppHandler,
    _check_rate_limit,
    _default_constraint_config,
    _max_body_bytes,
    _rate_limit_settings,
    _require_ingest_token,
    _reset_rate_limit_for_tests,
    run_server,
)


class _FakeHandler:
    """Minimal stand-in for BaseHTTPRequestHandler — only headers are used."""

    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


# ---------------------------------------------------------------------------
# _max_body_bytes
# ---------------------------------------------------------------------------


class MaxBodyBytesTests(unittest.TestCase):
    def test_invalid_env_returns_default(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_MAX_BODY_BYTES": "not_a_number"}):
            result = _max_body_bytes()
        self.assertEqual(result, 65536)

    def test_valid_env_returns_int(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_MAX_BODY_BYTES": "1024"}):
            result = _max_body_bytes()
        self.assertEqual(result, 1024)


# ---------------------------------------------------------------------------
# _rate_limit_settings
# ---------------------------------------------------------------------------


class RateLimitSettingsTests(unittest.TestCase):
    def test_invalid_limit_returns_default(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_RATE_LIMIT_REQUESTS": "bad"}):
            limit, _ = _rate_limit_settings()
        self.assertEqual(limit, 60)

    def test_invalid_window_returns_default(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_RATE_LIMIT_WINDOW_SECONDS": "bad"}):
            _, window = _rate_limit_settings()
        self.assertEqual(window, 60.0)


# ---------------------------------------------------------------------------
# _require_ingest_token
# ---------------------------------------------------------------------------


class RequireIngestTokenTests(unittest.TestCase):
    def test_x_ingest_token_header_accepted(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_INGEST_TOKEN": "secret123"}):
            handler = _FakeHandler({"X-Ingest-Token": "secret123"})
            self.assertTrue(_require_ingest_token(handler))  # type: ignore[arg-type]

    def test_bearer_header_accepted(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_INGEST_TOKEN": "secret123"}):
            handler = _FakeHandler({"Authorization": "Bearer secret123"})
            self.assertTrue(_require_ingest_token(handler))  # type: ignore[arg-type]

    def test_wrong_token_rejected(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_INGEST_TOKEN": "secret123"}):
            handler = _FakeHandler({"Authorization": "Bearer wrong"})
            self.assertFalse(_require_ingest_token(handler))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# _check_rate_limit
# ---------------------------------------------------------------------------


class CheckRateLimitTests(unittest.TestCase):
    def test_zero_limit_always_allows(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_RATE_LIMIT_REQUESTS": "0"}):
            _reset_rate_limit_for_tests()
            allowed, _ = _check_rate_limit(route_class="operator", key="k")
        self.assertTrue(allowed)


# ---------------------------------------------------------------------------
# _default_constraint_config
# ---------------------------------------------------------------------------


class DefaultConstraintConfigTests(unittest.TestCase):
    def test_reads_blocked_scope_keys_from_env(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_BLOCKED_SCOPE_KEYS": "foo,bar"}):
            config: ConstraintConfig = _default_constraint_config()
        self.assertIn("foo", config.blocked_scope_keys)
        self.assertIn("bar", config.blocked_scope_keys)

    def test_reads_max_token_amount_from_env(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_MAX_TOKEN_AMOUNT": "100"}):
            config = _default_constraint_config()
        self.assertEqual(config.max_token_amount, 100)

    def test_reads_max_scope_items_from_env(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_MAX_SCOPE_ITEMS": "10"}):
            config = _default_constraint_config()
        self.assertEqual(config.max_scope_items, 10)

    def test_invalid_max_token_amount_ignored(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_MAX_TOKEN_AMOUNT": "notanint"}):
            config = _default_constraint_config()
        self.assertIsNone(config.max_token_amount)

    def test_invalid_max_scope_items_ignored(self) -> None:
        with patch.dict(os.environ, {"XCHANGE_MAX_SCOPE_ITEMS": "notanint"}):
            config = _default_constraint_config()
        self.assertIsNone(config.max_scope_items)


# ---------------------------------------------------------------------------
# run_server (L946-948)
# ---------------------------------------------------------------------------


class RunServerTests(unittest.TestCase):
    def test_run_server_creates_http_server_and_calls_serve_forever(self) -> None:
        with patch("xchange.main.HTTPServer") as mock_server_class:
            mock_instance = mock_server_class.return_value
            # serve_forever would block; mock it so run_server returns immediately
            mock_instance.serve_forever.side_effect = KeyboardInterrupt
            try:
                run_server(host="127.0.0.1", port=9999)
            except KeyboardInterrupt:
                pass
            mock_server_class.assert_called_once_with(("127.0.0.1", 9999), AppHandler)
            mock_instance.serve_forever.assert_called_once()


if __name__ == "__main__":
    unittest.main()
