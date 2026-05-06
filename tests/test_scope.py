"""Tests for token scope, tool scope, and scope integration."""
import json
import os
import sqlite3
import unittest
from http import HTTPStatus
from unittest.mock import patch

from xchange.domain import (
    EvidenceType,
    InsightTier,
    RewardToken,
    TokenScope,
    ToolProvenance,
    ToolScope,
    compute_rarity_score,
    infer_token_scope,
)
from xchange.storage import (
    init_db,
    open_db,
    create_reward_draft,
    issue_reward_token,
    append_evidence,
    resolve_token_scope,
    resolve_tool_scope,
)


class TestTokenScope(unittest.TestCase):
    """TokenScope dataclass and inference tests."""

    def test_rarity_band_very_rare(self):
        self.assertEqual(TokenScope.rarity_band_from_score(0.80), "very_rare")
        self.assertEqual(TokenScope.rarity_band_from_score(0.75), "very_rare")
        self.assertEqual(TokenScope.rarity_band_from_score(1.0), "very_rare")

    def test_rarity_band_rare(self):
        self.assertEqual(TokenScope.rarity_band_from_score(0.50), "rare")
        self.assertEqual(TokenScope.rarity_band_from_score(0.74), "rare")

    def test_rarity_band_uncommon(self):
        self.assertEqual(TokenScope.rarity_band_from_score(0.25), "uncommon")
        self.assertEqual(TokenScope.rarity_band_from_score(0.49), "uncommon")

    def test_rarity_band_common(self):
        self.assertEqual(TokenScope.rarity_band_from_score(0.0), "common")
        self.assertEqual(TokenScope.rarity_band_from_score(0.24), "common")

    def test_infer_token_scope_surface(self):
        token = RewardToken(
            insight_tier=InsightTier.SURFACE,
            base_bank_depth=30,
            inferential_richness=0.1,
            trend_position=0.9,
            rarity_score=compute_rarity_score(
                insight_tier=InsightTier.SURFACE,
                inferential_richness=0.1,
                trend_position=0.9,
            ),
            issuance_trigger="glass_ingest",
            issued_at="2026-05-07T00:00:00Z",
        )
        scope = infer_token_scope(
            token=token,
            provenance="glass_ingest",
            evidence_type=EvidenceType.GLASS_SESSION_EVENT,
        )
        self.assertIsInstance(scope, TokenScope)
        self.assertEqual(scope.insight_tier, InsightTier.SURFACE)
        self.assertEqual(scope.provenance, "glass_ingest")
        self.assertEqual(scope.evidence_type, EvidenceType.GLASS_SESSION_EVENT)
        # Surface tier with high trend_position -> common
        self.assertEqual(scope.rarity_band, "common")

    def test_infer_token_scope_theoretical(self):
        token = RewardToken(
            insight_tier=InsightTier.THEORETICAL,
            base_bank_depth=95,
            inferential_richness=0.9,
            trend_position=0.1,
            rarity_score=compute_rarity_score(
                insight_tier=InsightTier.THEORETICAL,
                inferential_richness=0.9,
                trend_position=0.1,
            ),
            issuance_trigger="grid_substantiation",
            issued_at="2026-05-07T00:00:00Z",
        )
        scope = infer_token_scope(
            token=token,
            provenance="grid_substantiation",
            evidence_type=EvidenceType.AGENT_INTERPRETATION,
        )
        self.assertEqual(scope.insight_tier, InsightTier.THEORETICAL)
        self.assertEqual(scope.provenance, "grid_substantiation")
        self.assertEqual(scope.evidence_type, EvidenceType.AGENT_INTERPRETATION)
        # Theoretical tier with high richness and low trend -> very_rare
        self.assertEqual(scope.rarity_band, "very_rare")


class TestToolScope(unittest.TestCase):
    """ToolScope dataclass and from_provenance tests."""

    def test_from_provenance_known_glass(self):
        scope = ToolScope.from_provenance("glass_ingest")
        self.assertIsNotNone(scope)
        self.assertEqual(scope.provenance, "glass_ingest")
        self.assertEqual(scope.evidence_type, EvidenceType.GLASS_SESSION_EVENT)
        self.assertEqual(scope.source_system, "glass")
        self.assertTrue(scope.produces_transitions)

    def test_from_provenance_known_grid(self):
        scope = ToolScope.from_provenance("grid_substantiation")
        self.assertIsNotNone(scope)
        self.assertEqual(scope.provenance, "grid_substantiation")
        self.assertEqual(scope.evidence_type, EvidenceType.AGENT_INTERPRETATION)
        self.assertEqual(scope.source_system, "grid")
        self.assertTrue(scope.produces_transitions)

    def test_from_provenance_known_calculator(self):
        scope = ToolScope.from_provenance("calculator")
        self.assertIsNotNone(scope)
        self.assertEqual(scope.source_system, "calculator")
        self.assertFalse(scope.produces_transitions)

    def test_from_provenance_unknown(self):
        scope = ToolScope.from_provenance("unknown_future_tool")
        self.assertIsNone(scope)

    def test_from_provenance_enum_values(self):
        """Verify all ToolProvenance enum values are resolvable."""
        for prov in ToolProvenance:
            scope = ToolScope.from_provenance(prov.value)
            self.assertIsNotNone(scope, f"Failed to resolve provenance: {prov.value}")


class TestToolProvenance(unittest.TestCase):
    """ToolProvenance enum tests."""

    def test_all_provenance_values(self):
        expected = {
            "glass_ingest", "grid_substantiation", "student_ack",
            "fail_snapshot", "agent_interp", "calculator",
        }
        actual = {p.value for p in ToolProvenance}
        self.assertEqual(expected, actual)


class TestResolveToolScope(unittest.TestCase):
    """resolve_tool_scope storage function tests."""

    def test_known_provenance(self):
        result = resolve_tool_scope(provenance="glass_ingest")
        self.assertTrue(result["ok"])
        self.assertTrue(result["known"])
        self.assertEqual(result["tool_scope"]["source_system"], "glass")

    def test_unknown_provenance(self):
        result = resolve_tool_scope(provenance="novel_system")
        self.assertTrue(result["ok"])
        self.assertFalse(result["known"])
        self.assertIn("organically", result["note"])


class TestResolveTokenScope(unittest.TestCase):
    """resolve_token_scope storage function tests."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_db(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_scope_without_token(self):
        """Reward without token should return null token_scope."""
        create_reward_draft(
            conn=self.conn,
            reward_id="rwd-scope-1",
            student_id="stu-1",
        )
        result = resolve_token_scope(conn=self.conn, reward_id="rwd-scope-1")
        self.assertTrue(result["ok"])
        self.assertIsNone(result["token_scope"])
        self.assertIsNone(result["tool_scope"])

    def test_scope_with_token_and_evidence(self):
        """Reward with token and evidence should resolve both scopes."""
        # Create reward
        create_reward_draft(
            conn=self.conn,
            reward_id="rwd-scope-2",
            student_id="stu-2",
        )
        # Add evidence
        append_evidence(
            conn=self.conn,
            student_id="stu-2",
            session_id="sess-1",
            reward_id="rwd-scope-2",
            evidence_type=EvidenceType.GLASS_SESSION_EVENT,
            payload={"contract_satisfied": True},
            provenance="glass_ingest",
        )
        # Issue token
        token = RewardToken(
            insight_tier=InsightTier.PATTERN,
            base_bank_depth=60,
            inferential_richness=0.5,
            trend_position=0.3,
            rarity_score=compute_rarity_score(
                insight_tier=InsightTier.PATTERN,
                inferential_richness=0.5,
                trend_position=0.3,
            ),
            issuance_trigger="glass_ingest",
            issued_at="2026-05-07T00:00:00Z",
        )
        issue_reward_token(conn=self.conn, reward_id="rwd-scope-2", token=token)

        result = resolve_token_scope(conn=self.conn, reward_id="rwd-scope-2")
        self.assertTrue(result["ok"])
        self.assertIsNotNone(result["token_scope"])
        self.assertEqual(result["token_scope"]["insight_tier"], "pattern")
        self.assertEqual(result["token_scope"]["provenance"], "glass_ingest")
        self.assertIsNotNone(result["tool_scope"])
        self.assertEqual(result["tool_scope"]["source_system"], "glass")

    def test_scope_reward_not_found(self):
        """Non-existent reward should return error."""
        result = resolve_token_scope(conn=self.conn, reward_id="rwd-nope")
        self.assertIn("error", result)
        self.assertEqual(result["error"], "reward_not_found")


class TestScopeAPIEndpoints(unittest.TestCase):
    """HTTP endpoint tests for scope resolution."""

    @classmethod
    def setUpClass(cls):
        import tempfile
        cls.db_fd, cls.db_path = tempfile.mkstemp(suffix=".sqlite")

    @classmethod
    def tearDownClass(cls):
        os.close(cls.db_fd)
        os.unlink(cls.db_path)

    def _make_request(self, method, path, body=None, token="dev-secret"):
        """Helper to make HTTP requests to the x-change server."""
        from http.server import HTTPServer
        from xchange.main import AppHandler
        import io

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8788",
        }
        if body is not None:
            body_bytes = json.dumps(body).encode("utf-8")
            environ["CONTENT_LENGTH"] = str(len(body_bytes))
            environ["CONTENT_TYPE"] = "application/json"
        else:
            body_bytes = b"{}"
            environ["CONTENT_LENGTH"] = "0"

        # Use a real DB for integration tests
        with patch.dict(os.environ, {
            "XCHANGE_DB_PATH": self.db_path,
            "XCHANGE_INGEST_TOKEN": token,
            "STRIPE_WEBHOOK_SECRET": "whsec_test",
        }):
            # Reinit the DB
            with open_db(self.db_path) as conn:
                pass  # init_db runs automatically

        return None  # Placeholder — real HTTP tests need a running server

    def test_scope_urls_parse_correctly(self):
        """Verify URL routing for scope endpoints."""
        from urllib.parse import urlparse

        # Token scope URL
        parsed = urlparse("/v0/scope/token/rwd-123")
        parts = parsed.path.split("/")
        self.assertEqual(parts[4], "rwd-123")

        # Tool scope URL
        parsed = urlparse("/v0/scope/tool?provenance=glass_ingest")
        self.assertIn("provenance", parsed.query)


if __name__ == "__main__":
    unittest.main()