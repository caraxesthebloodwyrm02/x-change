"""Tests exercising uncovered execution paths in storage.py and nudge.py.

Covers record_failure, latest_failure_for_student, create_nudge,
suggest_path_semantics(None), store_exchange_request duplicate,
list_exchange_requests with approved filter, error-handling for
nonexistent rewards, apply_evidence_to_reward for missing rewards,
ingest_glass_session with failure payload, and _reward_token_from_dict.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from xchange.domain import (
    ConstraintConfig,
    ExchangeRequest,
    InsightTier,
)
from xchange.nudge import suggest_path_semantics
from xchange.storage import (
    acknowledge_reward,
    apply_evidence_to_reward,
    create_nudge,
    create_reward_draft,
    get_reward_state,
    ingest_glass_session,
    latest_failure_for_student,
    list_exchange_requests,
    open_db,
    record_failure,
    store_exchange_request,
    _reward_token_from_dict,
)
from xchange.domain import evaluate_exchange_request


class StorageCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(self._fd)
        self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))

    # -- record_failure + latest_failure_for_student -----------------------

    def test_record_failure_and_latest_failure_for_student(self) -> None:
        with open_db(self._path) as conn:
            record_failure(
                conn=conn,
                session_id="sess-1",
                student_id="student-a",
                failure={
                    "command": "cat missing.txt",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": "cat: missing.txt: No such file or directory",
                    "failure_at": "2026-05-06T10:00:00Z",
                },
            )
            snap = latest_failure_for_student(conn, student_id="student-a")
            self.assertIsNotNone(snap)
            assert snap is not None
            self.assertEqual(snap.command, "cat missing.txt")
            self.assertEqual(snap.exit_code, 1)

    def test_latest_failure_for_student_none_when_no_failures(self) -> None:
        with open_db(self._path) as conn:
            snap = latest_failure_for_student(conn, student_id="nobody")
            self.assertIsNone(snap)

    # -- ingest_glass_session with failure dict ----------------------------

    def test_ingest_glass_session_with_failure_payload(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r-fail", student_id="s1")
            summary = ingest_glass_session(
                conn=conn,
                session_id="sess-fail",
                student_id="s1",
                payload={
                    "reward_id": "r-fail",
                    "contract_satisfied": True,
                    "failure": {
                        "command": "bash broken.sh",
                        "exit_code": 127,
                        "stdout": "",
                        "stderr": "command not found",
                    },
                },
            )
            self.assertTrue(summary.get("ok"))
            snap = latest_failure_for_student(conn, student_id="s1")
            self.assertIsNotNone(snap)
            assert snap is not None
            self.assertEqual(snap.command, "bash broken.sh")

    # -- create_nudge ------------------------------------------------------

    def test_create_nudge_stores_row(self) -> None:
        with open_db(self._path) as conn:
            create_nudge(
                conn=conn,
                student_id="s1",
                reward_id="r1",
                failure_command="cat missing.txt",
                suggestion="Try: ls first, then cat <filename>",
            )
            cur = conn.execute(
                "SELECT student_id, reward_id, failure_command, suggestion FROM nudges"
            )
            rows = cur.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["student_id"], "s1")
            self.assertEqual(rows[0]["reward_id"], "r1")
            self.assertEqual(rows[0]["failure_command"], "cat missing.txt")

    # -- suggest_path_semantics with None command --------------------------

    def test_suggest_path_semantics_no_command(self) -> None:
        result = suggest_path_semantics(failure_command=None)
        self.assertIn("Student failure captured.", result)
        self.assertNotIn("Failure command: `", result)

    # -- store_exchange_request duplicate idempotency ----------------------

    def test_store_exchange_request_idempotent_by_request_id(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r-dup", student_id="s-dup")
            req = ExchangeRequest(
                request_id="req-1",
                student_id="s-dup",
                reward_id="r-dup",
                requested_scope={"token_amount": 5},
                submitted_at="2026-05-06T10:00:00Z",
            )
            cfg = ConstraintConfig(
                blocked_scope_keys=frozenset(),
                irreversible_scope_keys=frozenset(),
                require_explicit_irreversible_approval=False,
                max_token_amount=10,
                max_scope_items=10,
            )
            result = evaluate_exchange_request(req, cfg)
            constraint_snapshot = {
                "blocked_scope_keys": [],
                "irreversible_scope_keys": [],
                "require_explicit_irreversible_approval": False,
                "max_token_amount": 10,
                "max_scope_items": 10,
            }
            out1 = store_exchange_request(
                conn=conn,
                request=req,
                result=result,
                constraint_config_snapshot=constraint_snapshot,
            )
            self.assertTrue(out1.get("ok"))

            out2 = store_exchange_request(
                conn=conn,
                request=req,
                result=result,
                constraint_config_snapshot=constraint_snapshot,
            )
            self.assertTrue(out2.get("ok"))
            self.assertEqual(out2["request_id"], "req-1")

    # -- list_exchange_requests with approved filter -----------------------

    def test_list_exchange_requests_approved_filter(self) -> None:
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r-a", student_id="s-a")
            req_approved = ExchangeRequest(
                request_id="req-approved",
                student_id="s-a",
                reward_id="r-a",
                requested_scope={"token_amount": 3},
                submitted_at="2026-05-06T10:00:00Z",
            )
            req_denied = ExchangeRequest(
                request_id="req-denied",
                student_id="s-a",
                reward_id="r-a",
                requested_scope={"token_amount": 99, "blocked_op": True},
                submitted_at="2026-05-06T10:01:00Z",
            )
            cfg_approved = ConstraintConfig(
                blocked_scope_keys=frozenset(),
                irreversible_scope_keys=frozenset(),
                require_explicit_irreversible_approval=False,
                max_token_amount=10,
                max_scope_items=10,
            )
            cfg_denied = ConstraintConfig(
                blocked_scope_keys=frozenset(["blocked_op"]),
                irreversible_scope_keys=frozenset(),
                require_explicit_irreversible_approval=False,
                max_token_amount=10,
                max_scope_items=10,
            )
            constraint_snapshot = {
                "blocked_scope_keys": [],
                "irreversible_scope_keys": [],
                "require_explicit_irreversible_approval": False,
                "max_token_amount": 10,
                "max_scope_items": 10,
            }
            res_a = evaluate_exchange_request(req_approved, cfg_approved)
            store_exchange_request(
                conn=conn,
                request=req_approved,
                result=res_a,
                constraint_config_snapshot=constraint_snapshot,
            )
            res_d = evaluate_exchange_request(req_denied, cfg_denied)
            store_exchange_request(
                conn=conn,
                request=req_denied,
                result=res_d,
                constraint_config_snapshot=constraint_snapshot,
            )

            approved_only = list_exchange_requests(conn=conn, approved=True)
            self.assertEqual(len(approved_only), 1)
            self.assertEqual(approved_only[0]["request_id"], "req-approved")

            denied_only = list_exchange_requests(conn=conn, approved=False)
            self.assertEqual(len(denied_only), 1)
            self.assertEqual(denied_only[0]["request_id"], "req-denied")

    # -- Nonexistent reward error handling ---------------------------------

    def test_get_reward_state_nonexistent_returns_none(self) -> None:
        with open_db(self._path) as conn:
            state = get_reward_state(conn, reward_id="nonexistent")
            self.assertIsNone(state)

    def test_acknowledge_reward_nonexistent(self) -> None:
        with open_db(self._path) as conn:
            result = acknowledge_reward(
                conn=conn, reward_id="nonexistent", student_id="s1"
            )
            self.assertEqual(result.get("error"), "reward_not_found")

    def test_apply_evidence_to_reward_nonexistent_returns_none(self) -> None:
        from xchange.storage import EvidenceType

        with open_db(self._path) as conn:
            result = apply_evidence_to_reward(
                conn=conn,
                reward_id="nonexistent",
                evidence_type=EvidenceType.GLASS_SESSION_EVENT,
                ingest_payload={"contract_satisfied": True},
            )
            self.assertIsNone(result)

    # -- _reward_token_from_dict deserialization ---------------------------

    def test_reward_token_from_dict_round_trip(self) -> None:
        d = {
            "insight_tier": "theoretical",
            "base_bank_depth": 5,
            "inferential_richness": 0.8,
            "trend_position": 0.6,
            "rarity_score": 0.42,
            "issuance_trigger": "manual_review",
            "issued_at": "2026-05-06T10:00:00Z",
        }
        deserialized = _reward_token_from_dict(d)
        self.assertEqual(deserialized.insight_tier, InsightTier.THEORETICAL)
        self.assertEqual(deserialized.base_bank_depth, 5)
        self.assertEqual(deserialized.inferential_richness, 0.8)
        self.assertEqual(deserialized.rarity_score, 0.42)


if __name__ == "__main__":
    unittest.main()
