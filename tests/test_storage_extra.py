"""Extra storage coverage tests — fills gaps identified in src/xchange/storage.py.

Run with:
    PYTHONPATH="$PWD/src" uv run pytest tests/test_storage_extra.py -v
"""

from __future__ import annotations

import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone

from xchange.domain import (
    ConstraintConfig,
    EvidenceType,
    ExchangeRequest,
    InsightTier,
    OutcomeState,
    RewardState,
    RewardToken,
    TransitionResult,
    compute_rarity_score,
    evaluate_exchange_request,
)
from xchange.storage import (
    LEGACY_SCHEMA_SQL,
    _apply_transition,
    _reward_token_from_dict,
    acknowledge_reward,
    apply_evidence_to_reward,
    create_nudge,
    create_reward_draft,
    get_reward_state,
    ingest_glass_session,
    init_db,
    issue_reward_token,
    latest_failure_for_student,
    list_exchange_requests,
    open_db,
    process_stripe_payment_intent_succeeded,
    record_failure,
    store_exchange_request,
)

# ---------------------------------------------------------------------------
# Module-level state-advance helpers
# ---------------------------------------------------------------------------


def _advance_to_payment_pending(
    conn: sqlite3.Connection, reward_id: str, student_id: str
) -> None:
    """Draft → earned → payment_pending via glass-session ingests."""
    create_reward_draft(conn=conn, reward_id=reward_id, student_id=student_id)
    ingest_glass_session(
        conn=conn,
        session_id=f"adv-{reward_id}-cs",
        student_id=student_id,
        payload={"reward_id": reward_id, "contract_satisfied": True},
    )
    ingest_glass_session(
        conn=conn,
        session_id=f"adv-{reward_id}-rfp",
        student_id=student_id,
        payload={"reward_id": reward_id, "ready_for_payment": True},
    )


def _advance_to_payment_confirmed(
    conn: sqlite3.Connection,
    reward_id: str,
    student_id: str,
    stripe_event_id: str = "evt-confirm-default",
) -> None:
    """Draft → payment_confirmed via the full happy path."""
    _advance_to_payment_pending(conn, reward_id, student_id)
    process_stripe_payment_intent_succeeded(
        conn=conn,
        stripe_event_id=stripe_event_id,
        stripe_payment_intent_id="pi-default-1",
        reward_id=reward_id,
        student_id=student_id,
        raw_event={"id": stripe_event_id},
    )


# ---------------------------------------------------------------------------
# Base test case — temp SQLite file per test
# ---------------------------------------------------------------------------


class _TempDbCase(unittest.TestCase):
    """Provides self._path for a fresh temporary SQLite database per test."""

    def setUp(self) -> None:
        fd, self._path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self._path) and os.remove(self._path))


# ---------------------------------------------------------------------------
# 1. acknowledge_reward — reward_not_found branch (line 962)
# ---------------------------------------------------------------------------


class TestAcknowledgeRewardNotFound(_TempDbCase):
    def test_reward_not_found_returns_error_key(self) -> None:
        """acknowledge_reward on a non-existent reward returns reward_not_found."""
        with open_db(self._path) as conn:
            result = acknowledge_reward(
                conn=conn, reward_id="nonexistent", student_id="s1"
            )
        self.assertEqual(result.get("error"), "reward_not_found")


# ---------------------------------------------------------------------------
# 2. create_nudge — with and without reward_id (lines 1032-1040)
# ---------------------------------------------------------------------------


class TestCreateNudge(_TempDbCase):
    def test_nudge_with_reward_id_persists_row(self) -> None:
        """Nudge with a reward_id appears in the nudges table."""
        with open_db(self._path) as conn:
            create_nudge(
                conn=conn,
                student_id="s1",
                reward_id="r1",
                failure_command="cd /oops",
                suggestion="Try this",
            )
            row = conn.execute("SELECT * FROM nudges WHERE student_id='s1'").fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["reward_id"], "r1")
            self.assertEqual(row["failure_command"], "cd /oops")
            self.assertEqual(row["suggestion"], "Try this")

    def test_nudge_without_reward_id_persists_row(self) -> None:
        """Nudge with reward_id=None persists with a NULL reward_id column."""
        with open_db(self._path) as conn:
            create_nudge(
                conn=conn,
                student_id="s2",
                reward_id=None,
                failure_command="cd /oops",
                suggestion="Check the path",
            )
            row = conn.execute("SELECT * FROM nudges WHERE student_id='s2'").fetchone()
            self.assertIsNotNone(row)
            self.assertIsNone(row["reward_id"])
            self.assertEqual(row["suggestion"], "Check the path")


# ---------------------------------------------------------------------------
# 3. record_failure + latest_failure_for_student (lines 533-556, 569-583)
# ---------------------------------------------------------------------------


class TestFailureRecording(_TempDbCase):
    def test_record_failure_returns_snapshot_with_correct_fields(self) -> None:
        """record_failure returns a FailureSnapshot with command and exit_code set."""
        with open_db(self._path) as conn:
            snap = record_failure(
                conn=conn,
                session_id="sess-1",
                student_id="stu",
                failure={
                    "command": "cd /missing",
                    "exit_code": 1,
                    "stderr": "no such dir",
                },
            )
        self.assertEqual(snap.command, "cd /missing")
        self.assertEqual(snap.exit_code, 1)

    def test_latest_failure_for_student_returns_most_recent(self) -> None:
        """latest_failure_for_student returns the most recently recorded failure."""
        with open_db(self._path) as conn:
            record_failure(
                conn=conn,
                session_id="sess-2",
                student_id="stu",
                failure={
                    "command": "cd /missing",
                    "exit_code": 1,
                    "stderr": "no such dir",
                },
            )
            latest = latest_failure_for_student(conn, student_id="stu")
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest.command, "cd /missing")
            self.assertEqual(latest.exit_code, 1)

    def test_latest_failure_returns_none_for_unknown_student(self) -> None:
        """latest_failure_for_student returns None when the student has no failures."""
        with open_db(self._path) as conn:
            result = latest_failure_for_student(conn, student_id="ghost")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 4, 5, 6, 10 — ingest_glass_session variants (lines 630-649)
# ---------------------------------------------------------------------------


class TestIngestGlassSessionVariants(_TempDbCase):
    # --- gap 4: failure dict in payload records via record_failure path ----

    def test_ingest_with_failure_dict_records_failure(self) -> None:
        """Failure dict in payload causes record_failure and latest_failure returns it."""
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            result = ingest_glass_session(
                conn=conn,
                session_id="sess-f",
                student_id="s1",
                payload={
                    "reward_id": "r1",
                    "failure": {"command": "cd /oops", "exit_code": 1},
                },
            )
            self.assertTrue(result["ok"])
            latest = latest_failure_for_student(conn, student_id="s1")
            self.assertIsNotNone(latest)
            assert latest is not None
            self.assertEqual(latest.command, "cd /oops")

    # --- gap 5: nonexistent reward_id — ok=True, no transition key ---------

    def test_ingest_with_nonexistent_reward_ok_no_transition(self) -> None:
        """Ingesting against a non-existent reward returns ok=True with no transition."""
        with open_db(self._path) as conn:
            result = ingest_glass_session(
                conn=conn,
                session_id="sess-ghost",
                student_id="s1",
                payload={"reward_id": "does-not-exist"},
            )
        self.assertTrue(result["ok"])
        self.assertNotIn("transition", result)

    # --- gap 6: deprecated student_ack path --------------------------------

    def test_deprecated_student_ack_path_advances_to_acknowledged(self) -> None:
        """student_ack=True in ingest payload advances a payment_confirmed reward."""
        with open_db(self._path) as conn:
            _advance_to_payment_confirmed(conn, "r1", "s1", stripe_event_id="evt-gap6")
            ingest_glass_session(
                conn=conn,
                session_id="sess-ack",
                student_id="s1",
                payload={"reward_id": "r1", "student_ack": True},
            )
            state = get_reward_state(conn, reward_id="r1")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state["state"], "student_acknowledged")

    # --- gap 10: request_review sets review_requested_at -------------------

    def test_ingest_request_review_sets_review_requested_at(self) -> None:
        """request_review=True transitions to review_requested and stamps review_requested_at."""
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r2", student_id="s2")
            ingest_glass_session(
                conn=conn,
                session_id="sess-rv",
                student_id="s2",
                payload={"reward_id": "r2", "request_review": True},
            )
            state = get_reward_state(conn, reward_id="r2")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertEqual(state["state"], "review_requested")
            self.assertIsNotNone(state["review_requested_at"])


# ---------------------------------------------------------------------------
# 7. apply_evidence_to_reward — row not found returns None (line 491)
# ---------------------------------------------------------------------------


class TestApplyEvidenceNotFound(_TempDbCase):
    def test_returns_none_for_nonexistent_reward(self) -> None:
        """apply_evidence_to_reward returns None when the reward row is missing."""
        with open_db(self._path) as conn:
            result = apply_evidence_to_reward(
                conn=conn,
                reward_id="missing",
                evidence_type=EvidenceType.GLASS_SESSION_EVENT,
                ingest_payload={},
            )
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# 8, 9 — _apply_transition edge cases (lines 443, 448)
# ---------------------------------------------------------------------------


class TestApplyTransitionEdgeCases(_TempDbCase):
    # --- gap 8: early return when reward missing ----------------------------

    def test_no_exception_for_missing_reward(self) -> None:
        """_apply_transition silently returns early when the reward row is absent."""
        transition = TransitionResult(
            new_state=RewardState.EARNED,
            new_outcome=OutcomeState.UNKNOWN,
            notes=("test",),
        )
        with open_db(self._path) as conn:
            # Must not raise — returns None implicitly (early return guard)
            _apply_transition(conn, reward_id="missing", result=transition)

    # --- gap 9: extra_notes appear in the transition_log -------------------

    def test_extra_notes_stored_in_transition_log(self) -> None:
        """extra_notes kwarg is merged into the transition_log entry in notes_json."""
        transition = TransitionResult(
            new_state=RewardState.EARNED,
            new_outcome=OutcomeState.UNKNOWN,
            notes=("earned via test",),
        )
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            _apply_transition(
                conn,
                reward_id="r1",
                result=transition,
                extra_notes=["extra note"],
            )
            conn.commit()  # _apply_transition does not commit itself
            state = get_reward_state(conn, reward_id="r1")
            self.assertIsNotNone(state)
            assert state is not None
            notes = state["notes"]
            self.assertIsNotNone(notes)
            log = notes.get("transition_log", [])
            all_notes = [n for entry in log for n in entry.get("notes", [])]
            self.assertIn("extra note", all_notes)


# ---------------------------------------------------------------------------
# 11, 12 — process_stripe_payment_intent_succeeded edge cases (line 864)
# ---------------------------------------------------------------------------


class TestStripePaymentEdgeCases(_TempDbCase):
    # --- gap 11: DRAFTED reward → else branch (stripe not applicable) ------

    def test_stripe_on_drafted_reward_not_applied(self) -> None:
        """Stripe event on a drafted reward returns applied=False and new_state='drafted'."""
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            out = process_stripe_payment_intent_succeeded(
                conn=conn,
                stripe_event_id="evt-drafted-1",
                stripe_payment_intent_id="pi-d1",
                reward_id="r1",
                student_id="s1",
                raw_event={"id": "evt-drafted-1"},
            )
        self.assertFalse(out.get("applied"))
        self.assertEqual(out["new_state"], "drafted")

    # --- gap 12: second distinct event on already-confirmed reward ----------

    def test_second_distinct_stripe_event_on_confirmed_not_applied(self) -> None:
        """A fresh stripe_event_id on a payment_confirmed reward returns applied=False."""
        with open_db(self._path) as conn:
            _advance_to_payment_confirmed(
                conn, "r1", "s1", stripe_event_id="evt-first-12"
            )
            out = process_stripe_payment_intent_succeeded(
                conn=conn,
                stripe_event_id="evt-second-12",  # different event id, no IntegrityError
                stripe_payment_intent_id="pi-2",
                reward_id="r1",
                student_id="s1",
                raw_event={"id": "evt-second-12"},
            )
        self.assertFalse(out.get("applied"))
        self.assertEqual(out["new_state"], "payment_confirmed")


# ---------------------------------------------------------------------------
# 13, 14 — reward token operations (lines 888, 1098)
# ---------------------------------------------------------------------------


class TestRewardTokenOps(_TempDbCase):
    def _build_token(self, tier: InsightTier = InsightTier.CAUSAL) -> RewardToken:
        rarity = compute_rarity_score(
            insight_tier=tier,
            inferential_richness=0.8,
            trend_position=0.3,
        )
        return RewardToken(
            insight_tier=tier,
            base_bank_depth=70,
            inferential_richness=0.8,
            trend_position=0.3,
            rarity_score=rarity,
            issuance_trigger="unit-test-trigger",
            issued_at="2024-01-01T00:00:00+00:00",
        )

    # --- gap 13: get_reward_state exposes reward_token_json branch ---------

    def test_get_reward_state_shows_issued_token(self) -> None:
        """After issue_reward_token, get_reward_state returns a non-None reward_token dict."""
        with open_db(self._path) as conn:
            create_reward_draft(conn=conn, reward_id="r1", student_id="s1")
            token = self._build_token(InsightTier.CAUSAL)
            issue_result = issue_reward_token(conn=conn, reward_id="r1", token=token)
            self.assertTrue(issue_result.get("ok"))

            state = get_reward_state(conn, reward_id="r1")
            self.assertIsNotNone(state)
            assert state is not None
            self.assertIsNotNone(state["reward_token"])
            self.assertEqual(
                state["reward_token"]["insight_tier"], InsightTier.CAUSAL.value
            )

    # --- gap 14: _reward_token_from_dict round-trip ------------------------

    def test_reward_token_from_dict_correct_fields(self) -> None:
        """_reward_token_from_dict deserialises insight_tier and base_bank_depth correctly."""
        d = {
            "insight_tier": InsightTier.PATTERN.value,
            "base_bank_depth": 50,
            "inferential_richness": 0.6,
            "trend_position": 0.4,
            "rarity_score": 0.48,
            "issuance_trigger": "unit-test",
            "issued_at": "2024-06-01T00:00:00+00:00",
        }
        token = _reward_token_from_dict(d)
        self.assertEqual(token.insight_tier, InsightTier.PATTERN)
        self.assertEqual(token.base_bank_depth, 50)
        self.assertAlmostEqual(token.inferential_richness, 0.6, places=5)


# ---------------------------------------------------------------------------
# 15, 16 — migration edge cases (lines 241-244, 198-205)
# ---------------------------------------------------------------------------


class TestMigrationEdgeCases(_TempDbCase):
    # --- gap 15: _run_migration absorbs OperationalError and re-records ----

    def test_operational_error_absorbed_and_version_rerecorded(self) -> None:
        """Deleting v001 record and re-running init_db re-records it despite column existing."""
        with open_db(self._path) as conn:
            # Verify the migration was recorded during initial open
            row = conn.execute(
                "SELECT version FROM schema_migrations WHERE version='v001_reward_token_json'"
            ).fetchone()
            self.assertIsNotNone(row, "migration should be recorded after first open")

            # Delete it to force the retry path
            conn.execute(
                "DELETE FROM schema_migrations WHERE version='v001_reward_token_json'"
            )
            conn.commit()

            # Calling init_db again: ALTER TABLE will raise OperationalError
            # (column already exists); _run_migration must catch and re-record.
            init_db(conn)

            row = conn.execute(
                "SELECT version FROM schema_migrations WHERE version='v001_reward_token_json'"
            ).fetchone()
            self.assertIsNotNone(
                row, "migration should be re-recorded after OperationalError"
            )

    # --- gap 16: legacy rewards table is migrated into reward_ledger -------

    def test_legacy_rewards_migrated_to_ledger(self) -> None:
        """Two legacy rewards rows are migrated to reward_ledger with correct states."""
        # Step 1: bootstrap legacy schema and rows via raw sqlite3
        raw = sqlite3.connect(self._path)
        raw.executescript(LEGACY_SCHEMA_SQL)
        raw.execute(
            "INSERT INTO rewards (reward_id, student_id, delivered) VALUES (?, ?, ?)",
            ("r_legacy_1", "s1", 0),
        )
        raw.execute(
            "INSERT INTO rewards (reward_id, student_id, delivered) VALUES (?, ?, ?)",
            ("r_legacy_2", "s1", 1),
        )
        raw.commit()
        raw.close()

        # Step 2: open via open_db — init_db discovers 0 ledger rows, migrates both
        with open_db(self._path) as conn:
            count = conn.execute("SELECT COUNT(*) AS c FROM reward_ledger").fetchone()[
                "c"
            ]
            self.assertEqual(count, 2)

            r1 = conn.execute(
                "SELECT state FROM reward_ledger WHERE reward_id='r_legacy_1'"
            ).fetchone()
            self.assertIsNotNone(r1)
            self.assertEqual(r1["state"], "drafted")

            r2 = conn.execute(
                "SELECT state FROM reward_ledger WHERE reward_id='r_legacy_2'"
            ).fetchone()
            self.assertIsNotNone(r2)
            self.assertEqual(r2["state"], "payment_confirmed")


# ---------------------------------------------------------------------------
# 17. list_exchange_requests — filter by approved (lines 1235-1236)
# ---------------------------------------------------------------------------


class TestListExchangeRequestsFiltering(_TempDbCase):
    def _make_constraint_config(self) -> ConstraintConfig:
        return ConstraintConfig(
            blocked_scope_keys=frozenset({"delete_all"}),
            irreversible_scope_keys=frozenset(),
            require_explicit_irreversible_approval=False,
            max_token_amount=None,
            max_scope_items=None,
        )

    def test_filter_by_approved_true_and_false(self) -> None:
        """list_exchange_requests(approved=True/False) returns only matching records."""
        now = datetime.now(timezone.utc).isoformat()
        config = self._make_constraint_config()

        # Approved request: no blocked keys
        req_ok = ExchangeRequest(
            request_id="req-approved-1",
            student_id="stu1",
            reward_id="r1",
            requested_scope={"read": True},
            submitted_at=now,
        )
        # Rejected request: blocked key present
        req_bad = ExchangeRequest(
            request_id="req-rejected-1",
            student_id="stu1",
            reward_id="r1",
            requested_scope={"delete_all": True},
            submitted_at=now,
        )
        result_ok = evaluate_exchange_request(req_ok, config)
        result_bad = evaluate_exchange_request(req_bad, config)

        self.assertTrue(result_ok.approved)
        self.assertFalse(result_bad.approved)

        snapshot = {"blocked_scope_keys": ["delete_all"]}

        with open_db(self._path) as conn:
            store_exchange_request(
                conn=conn,
                request=req_ok,
                result=result_ok,
                constraint_config_snapshot=snapshot,
            )
            store_exchange_request(
                conn=conn,
                request=req_bad,
                result=result_bad,
                constraint_config_snapshot=snapshot,
            )
            approved_list = list_exchange_requests(conn=conn, approved=True)
            rejected_list = list_exchange_requests(conn=conn, approved=False)

        self.assertEqual(len(approved_list), 1)
        self.assertEqual(approved_list[0]["request_id"], "req-approved-1")
        self.assertTrue(approved_list[0]["approved"])

        self.assertEqual(len(rejected_list), 1)
        self.assertEqual(rejected_list[0]["request_id"], "req-rejected-1")
        self.assertFalse(rejected_list[0]["approved"])


if __name__ == "__main__":
    unittest.main()
