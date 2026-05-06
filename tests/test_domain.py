from __future__ import annotations

import dataclasses
import unittest
from typing import Any

from xchange.domain import (
    ConstraintConfig,
    ConstraintLayer,
    EvidenceType,
    ExchangeRequest,
    InsightTier,
    OutcomeState,
    RewardState,
    RewardToken,
    compute_rarity_score,
    evaluate_exchange_request,
    ingest_bool,
    next_state_after_glass_evidence,
    next_state_after_stripe_payment,
)


class DomainTransitionTests(unittest.TestCase):
    def test_contract_satisfied_drafted_to_earned(self) -> None:
        r = next_state_after_glass_evidence(
            current=RewardState.DRAFTED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.GLASS_SESSION_EVENT,
            ingest_payload={"contract_satisfied": True},
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.EARNED)

    def test_ready_for_payment_moves_to_pending(self) -> None:
        r = next_state_after_glass_evidence(
            current=RewardState.EARNED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.GLASS_SESSION_EVENT,
            ingest_payload={"ready_for_payment": True},
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.PAYMENT_PENDING)

    def test_student_ack_requires_payment_confirmed(self) -> None:
        r = next_state_after_glass_evidence(
            current=RewardState.EARNED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.STUDENT_CONFIRMATION,
            ingest_payload={"student_ack": True},
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.EARNED)

    def test_student_ack_after_payment(self) -> None:
        r = next_state_after_glass_evidence(
            current=RewardState.PAYMENT_CONFIRMED,
            outcome=OutcomeState.DELIVERED_PENDING_ACK,
            evidence_type=EvidenceType.STUDENT_CONFIRMATION,
            ingest_payload={"student_ack": True},
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.STUDENT_ACKNOWLEDGED)

    def test_stripe_payment(self) -> None:
        r = next_state_after_stripe_payment(
            current=RewardState.PAYMENT_PENDING,
            outcome=OutcomeState.UNKNOWN,
            reward_student_id="stu-1",
            payment_student_id="stu-1",
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.PAYMENT_CONFIRMED)

    def test_stripe_mismatch_student(self) -> None:
        r = next_state_after_stripe_payment(
            current=RewardState.PAYMENT_PENDING,
            outcome=OutcomeState.UNKNOWN,
            reward_student_id="stu-1",
            payment_student_id="stu-2",
        )
        self.assertIsNone(r)

    def test_review_requested(self) -> None:
        r = next_state_after_glass_evidence(
            current=RewardState.PAYMENT_PENDING,
            outcome=OutcomeState.DELIVERED_PENDING_ACK,
            evidence_type=EvidenceType.GLASS_SESSION_EVENT,
            ingest_payload={"request_review": True},
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.REVIEW_REQUESTED)


class EpistemicTokenTests(unittest.TestCase):
    """Tests for RewardToken epistemic classification and rarity scoring."""

    def test_compute_rarity_emerging_causal(self) -> None:
        """Causal tier at the emerging edge with high inferential richness = high rarity."""
        # emergence = 1.0 - 0.1 = 0.9; tier_weight = 0.75
        # rarity = 0.9*0.4 + 0.9*0.4 + 0.75*0.2 = 0.36 + 0.36 + 0.15 = 0.87
        score = compute_rarity_score(
            insight_tier=InsightTier.CAUSAL,
            inferential_richness=0.9,
            trend_position=0.1,
        )
        self.assertAlmostEqual(score, 0.87, places=4)

    def test_compute_rarity_established_surface(self) -> None:
        """Surface tier at the established end with low inferential richness = low rarity."""
        # emergence = 1.0 - 0.9 = 0.1; tier_weight = 0.0
        # rarity = 0.1*0.4 + 0.1*0.4 + 0.0*0.2 = 0.04 + 0.04 + 0.0 = 0.08
        score = compute_rarity_score(
            insight_tier=InsightTier.SURFACE,
            inferential_richness=0.1,
            trend_position=0.9,
        )
        self.assertAlmostEqual(score, 0.08, places=4)

    def test_compute_rarity_theoretical_max(self) -> None:
        """Theoretical tier fully emerging with full richness approaches max."""
        # emergence = 1.0; tier_weight = 1.0
        # rarity = 1.0*0.4 + 1.0*0.4 + 1.0*0.2 = 1.0
        score = compute_rarity_score(
            insight_tier=InsightTier.THEORETICAL,
            inferential_richness=1.0,
            trend_position=0.0,
        )
        self.assertEqual(score, 1.0)

    def test_compute_rarity_all_zeros(self) -> None:
        """All zero inputs yield rarity_score = 0.0."""
        score = compute_rarity_score(
            insight_tier=InsightTier.SURFACE,
            inferential_richness=0.0,
            trend_position=1.0,  # fully established (emergence = 0)
        )
        self.assertEqual(score, 0.0)

    def test_compute_rarity_result_clamped(self) -> None:
        """Rarity score is always in [0.0, 1.0]."""
        for tier in InsightTier:
            for richness in [0.0, 0.5, 1.0]:
                for trend in [0.0, 0.5, 1.0]:
                    score = compute_rarity_score(
                        insight_tier=tier,
                        inferential_richness=richness,
                        trend_position=trend,
                    )
                    self.assertGreaterEqual(score, 0.0)
                    self.assertLessEqual(score, 1.0)

    def test_reward_token_amount_property_per_tier(self) -> None:
        """Each InsightTier maps to its expected backward-compatible integer amount."""
        expected = {
            InsightTier.SURFACE: 1,
            InsightTier.PATTERN: 2,
            InsightTier.STRUCTURAL: 3,
            InsightTier.CAUSAL: 4,
            InsightTier.THEORETICAL: 5,
        }
        for tier, amount in expected.items():
            token = RewardToken(
                insight_tier=tier,
                base_bank_depth=50,
                inferential_richness=0.5,
                trend_position=0.5,
                rarity_score=0.5,
                issuance_trigger="test_trigger",
                issued_at="2026-01-01T00:00:00+00:00",
            )
            self.assertEqual(
                token.amount, amount, f"tier={tier} expected amount={amount}"
            )

    def test_reward_token_is_frozen(self) -> None:
        """RewardToken is a frozen dataclass — mutation raises FrozenInstanceError."""
        token = RewardToken(
            insight_tier=InsightTier.STRUCTURAL,
            base_bank_depth=60,
            inferential_richness=0.7,
            trend_position=0.3,
            rarity_score=0.65,
            issuance_trigger="human_recognition",
            issued_at="2026-01-01T00:00:00+00:00",
        )
        with self.assertRaises(
            (dataclasses.FrozenInstanceError, TypeError, AttributeError)
        ):
            token.insight_tier = InsightTier.CAUSAL  # type: ignore[misc]  # pyright: ignore[reportAttributeAccessIssue]

    def test_rarity_score_rounds_to_four_places(self) -> None:
        """compute_rarity_score result is rounded to 4 decimal places."""
        score = compute_rarity_score(
            insight_tier=InsightTier.PATTERN,
            inferential_richness=0.333,
            trend_position=0.667,
        )
        # Result should have at most 4 decimal places
        self.assertEqual(score, round(score, 4))


class ExchangeConstraintTests(unittest.TestCase):
    """Tests for layered exchange constraint evaluation."""

    def _make_config(
        self,
        *,
        blocked: frozenset[str] | None = None,
        irreversible: frozenset[str] | None = None,
        require_approval: bool = True,
        max_amount: int | None = None,
        max_items: int | None = None,
    ) -> ConstraintConfig:
        return ConstraintConfig(
            blocked_scope_keys=blocked if blocked is not None else frozenset(),
            irreversible_scope_keys=irreversible
            if irreversible is not None
            else frozenset(),
            require_explicit_irreversible_approval=require_approval,
            max_token_amount=max_amount,
            max_scope_items=max_items,
        )

    def _make_request(self, scope: dict[str, Any]) -> ExchangeRequest:
        return ExchangeRequest(
            request_id="req-test-001",
            student_id="stu-test-001",
            reward_id="rwd-test-001",
            requested_scope=scope,
            submitted_at="2026-01-01T00:00:00+00:00",
        )

    def test_safety_blocked_key_rejects_immediately(self) -> None:
        """A request with a blocked key is rejected at layer 1 with approved=False."""
        config = self._make_config(blocked=frozenset({"admin_override"}))
        request = self._make_request({"admin_override": True, "token_amount": 5})
        result = evaluate_exchange_request(request, config)
        self.assertFalse(result.approved)
        self.assertEqual(len(result.layers), 1)
        self.assertFalse(result.layers[0].passed)
        self.assertEqual(result.layers[0].layer, ConstraintLayer.SAFETY_SECURITY)
        self.assertEqual(result.final_approved_scope, {})

    def test_safety_clean_request_passes(self) -> None:
        """A request with no blocked keys passes the safety layer."""
        config = self._make_config(blocked=frozenset({"admin_override"}))
        request = self._make_request({"token_amount": 3})
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertEqual(len(result.layers), 3)
        self.assertTrue(result.layers[0].passed)

    def test_ethics_removes_irreversible_without_approval(self) -> None:
        """Irreversible keys are stripped when no explicit approval is present."""
        config = self._make_config(
            irreversible=frozenset({"delete_account"}),
            require_approval=True,
        )
        request = self._make_request({"token_amount": 2, "delete_account": True})
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertNotIn("delete_account", result.final_approved_scope)
        self.assertIn("token_amount", result.final_approved_scope)
        ethics_layer = result.layers[1]
        self.assertEqual(ethics_layer.layer, ConstraintLayer.ETHICS_IRREVERSIBILITY)
        self.assertIn("delete_account", ethics_layer.blocked_keys)

    def test_ethics_keeps_irreversible_with_explicit_approval(self) -> None:
        """Irreversible keys are kept when explicit_irreversible_approval is truthy."""
        config = self._make_config(
            irreversible=frozenset({"delete_account"}),
            require_approval=True,
        )
        request = self._make_request(
            {
                "token_amount": 2,
                "delete_account": True,
                "explicit_irreversible_approval": True,
            }
        )
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertIn("delete_account", result.final_approved_scope)
        ethics_layer = result.layers[1]
        self.assertEqual(ethics_layer.blocked_keys, ())

    def test_ethics_no_irreversible_keys_in_request(self) -> None:
        """When no irreversible keys appear in the request, ethics layer passes cleanly."""
        config = self._make_config(
            irreversible=frozenset({"delete_account", "purge"}),
            require_approval=True,
        )
        request = self._make_request({"token_amount": 2, "resource": "lecture-1"})
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertEqual(result.layers[1].blocked_keys, ())

    def test_economic_caps_token_amount(self) -> None:
        """token_amount exceeding max_token_amount is capped to the configured max."""
        config = self._make_config(max_amount=10)
        request = self._make_request({"token_amount": 50})
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertEqual(result.final_approved_scope["token_amount"], 10)

    def test_economic_narrows_scope_items(self) -> None:
        """Scope is narrowed to max_scope_items when the request has too many keys."""
        config = self._make_config(max_items=2)
        request = self._make_request({"a": 1, "b": 2, "c": 3, "d": 4})
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertLessEqual(len(result.final_approved_scope), 2)

    def test_economic_within_bounds_unchanged(self) -> None:
        """Scope is not narrowed when token_amount and item count are within limits."""
        config = self._make_config(max_amount=100, max_items=10)
        scope = {"token_amount": 5, "resource": "lecture-1"}
        request = self._make_request(scope)
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertEqual(result.final_approved_scope["token_amount"], 5)
        self.assertEqual(result.final_approved_scope["resource"], "lecture-1")

    def test_full_pass_no_narrowing(self) -> None:
        """Clean request with no constraints hit passes all 3 layers unchanged."""
        config = self._make_config()  # no blocked, no irreversible, no caps
        scope = {"token_amount": 3, "resource": "lecture-2"}
        request = self._make_request(scope)
        result = evaluate_exchange_request(request, config)
        self.assertTrue(result.approved)
        self.assertEqual(len(result.layers), 3)
        self.assertTrue(all(lr.passed for lr in result.layers))
        self.assertEqual(result.final_approved_scope, scope)

    def test_result_always_has_three_layers_when_safety_passes(self) -> None:
        """Three constraint layers are always evaluated when safety gate passes."""
        config = self._make_config()
        result = evaluate_exchange_request(
            self._make_request({"token_amount": 1}), config
        )
        self.assertEqual(len(result.layers), 3)
        layer_names = {lr.layer for lr in result.layers}
        self.assertEqual(
            layer_names,
            {
                ConstraintLayer.SAFETY_SECURITY,
                ConstraintLayer.ETHICS_IRREVERSIBILITY,
                ConstraintLayer.ECONOMIC_STABILITY,
            },
        )

    def test_result_has_one_layer_on_safety_block(self) -> None:
        """Only one layer is recorded when the safety hard gate rejects."""
        config = self._make_config(blocked=frozenset({"root_access"}))
        result = evaluate_exchange_request(
            self._make_request({"root_access": True}), config
        )
        self.assertFalse(result.approved)
        self.assertEqual(len(result.layers), 1)

    def test_exchange_result_has_evaluated_at(self) -> None:
        """ExchangeResult always carries an evaluated_at ISO timestamp."""
        config = self._make_config()
        result = evaluate_exchange_request(
            self._make_request({"token_amount": 1}), config
        )
        self.assertIsNotNone(result.evaluated_at)
        self.assertTrue(
            result.evaluated_at.startswith("2")
        )  # ISO 8601 starts with year


if __name__ == "__main__":
    _ = unittest.main()


class IngestBoolTests(unittest.TestCase):
    """Unit tests for ingest_bool — covers the string and catch-all branches."""

    def test_true_bool_returns_true(self) -> None:
        self.assertTrue(ingest_bool({"k": True}, "k"))

    def test_false_bool_returns_false(self) -> None:
        self.assertFalse(ingest_bool({"k": False}, "k"))

    def test_none_returns_false(self) -> None:
        self.assertFalse(ingest_bool({"k": None}, "k"))

    def test_missing_key_returns_false(self) -> None:
        self.assertFalse(ingest_bool({}, "k"))

    def test_truthy_string_true(self) -> None:  # covers L336
        for s in ("true", "True", "TRUE", "1", "yes", "y", "YES"):
            self.assertTrue(ingest_bool({"k": s}, "k"), f"expected True for {s!r}")

    def test_falsy_string_false(self) -> None:  # covers L336 false branch
        for s in ("false", "0", "no", "n", ""):
            self.assertFalse(ingest_bool({"k": s}, "k"), f"expected False for {s!r}")

    def test_non_string_non_bool_truthy(self) -> None:  # covers L337
        self.assertTrue(ingest_bool({"k": 42}, "k"))
        self.assertTrue(ingest_bool({"k": 1.5}, "k"))
        self.assertTrue(ingest_bool({"k": ["x"]}, "k"))

    def test_non_string_non_bool_falsy(self) -> None:  # covers L337 false branch
        self.assertFalse(ingest_bool({"k": 0}, "k"))
        self.assertFalse(ingest_bool({"k": 0.0}, "k"))
        self.assertFalse(ingest_bool({"k": []}, "k"))


class DomainEvidenceEdgeCaseTests(unittest.TestCase):
    """Cover the remaining branches in next_state_after_glass_evidence."""

    def test_failure_snapshot_always_appends_note(self) -> None:
        """FAILURE_SNAPSHOT evidence records a note regardless of payload (L390)."""
        r = next_state_after_glass_evidence(
            current=RewardState.DRAFTED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.FAILURE_SNAPSHOT,
            ingest_payload={},
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertIn("failure_snapshot recorded", r.notes)

    def test_failure_snapshot_with_contract_satisfied(self) -> None:
        """FAILURE_SNAPSHOT can co-occur with a state transition note."""
        r = next_state_after_glass_evidence(
            current=RewardState.DRAFTED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.FAILURE_SNAPSHOT,
            ingest_payload={"contract_satisfied": True},
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertIn("failure_snapshot recorded", r.notes)
        self.assertIn("contract_satisfied: drafted -> earned", r.notes)

    def test_glass_session_empty_payload_returns_none(self) -> None:
        """GLASS_SESSION_EVENT with no flags set has no notes and returns None (L397)."""
        r = next_state_after_glass_evidence(
            current=RewardState.DRAFTED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.GLASS_SESSION_EVENT,
            ingest_payload={},
        )
        self.assertIsNone(r)

    def test_agent_interpretation_empty_payload_returns_none(self) -> None:
        """AGENT_INTERPRETATION with no flags hits the catch-all return None (L400)."""
        r = next_state_after_glass_evidence(
            current=RewardState.DRAFTED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.AGENT_INTERPRETATION,
            ingest_payload={},
        )
        self.assertIsNone(r)

    def test_return_attempt_empty_payload_returns_none(self) -> None:
        """RETURN_ATTEMPT with no flags is in the ignored group (L397)."""
        r = next_state_after_glass_evidence(
            current=RewardState.DRAFTED,
            outcome=OutcomeState.UNKNOWN,
            evidence_type=EvidenceType.RETURN_ATTEMPT,
            ingest_payload={},
        )
        self.assertIsNone(r)


class StripePaymentEdgeCaseTests(unittest.TestCase):
    """Cover the replay and invalid-prior-state paths in next_state_after_stripe_payment."""

    def test_replay_when_already_payment_confirmed(self) -> None:  # covers L418
        """Payment event arrives after reward is already PAYMENT_CONFIRMED → replay note."""
        r = next_state_after_stripe_payment(
            current=RewardState.PAYMENT_CONFIRMED,
            outcome=OutcomeState.DELIVERED_PENDING_ACK,
            reward_student_id="stu-1",
            payment_student_id="stu-1",
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.PAYMENT_CONFIRMED)
        self.assertTrue(any("replay" in n for n in r.notes))

    def test_replay_when_already_student_acknowledged(self) -> None:  # covers L418
        """Payment event after STUDENT_ACKNOWLEDGED also triggers the replay path."""
        r = next_state_after_stripe_payment(
            current=RewardState.STUDENT_ACKNOWLEDGED,
            outcome=OutcomeState.ACKNOWLEDGED,
            reward_student_id="stu-1",
            payment_student_id="stu-1",
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.STUDENT_ACKNOWLEDGED)

    def test_invalid_prior_state_drafted(self) -> None:  # covers L425
        """Payment on a DRAFTED reward (not yet earned) returns an 'not applied' note."""
        r = next_state_after_stripe_payment(
            current=RewardState.DRAFTED,
            outcome=OutcomeState.UNKNOWN,
            reward_student_id="stu-1",
            payment_student_id="stu-1",
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertEqual(r.new_state, RewardState.DRAFTED)
        self.assertTrue(any("invalid prior state" in n for n in r.notes))

    def test_invalid_prior_state_review_requested(self) -> None:  # covers L425
        """Payment on a REVIEW_REQUESTED reward also returns 'not applied'."""
        r = next_state_after_stripe_payment(
            current=RewardState.REVIEW_REQUESTED,
            outcome=OutcomeState.REVIEW_OPEN,
            reward_student_id="stu-1",
            payment_student_id="stu-1",
        )
        self.assertIsNotNone(r)
        assert r is not None
        self.assertTrue(any("invalid prior state" in n for n in r.notes))
