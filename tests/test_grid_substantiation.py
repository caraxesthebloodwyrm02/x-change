from __future__ import annotations

import json
import os
import unittest

from xchange.grid_substantiation import normalize_grid_substantiation_evidence


class GridSubstantiationTests(unittest.TestCase):
    def _minimal_valid(self) -> dict:
        return {
            "version": "v1",
            "captured_at": "2026-05-07T12:00:00+00:00",
            "source": "grid-lumos-orchestrator",
            "summary": {
                "composite_score": 62.3,
                "verdict_tier": "WATCH",
                "dimensions": {
                    "health": 70.0,
                    "trust": 60.0,
                    "drift": 55.0,
                    "fail": 80.0,
                    "momentum": 50.0,
                },
            },
        }

    def test_normalize_minimal_ok(self) -> None:
        out = normalize_grid_substantiation_evidence(self._minimal_valid())
        self.assertEqual(out["version"], "v1")
        self.assertEqual(out["summary"]["verdict_tier"], "WATCH")
        self.assertAlmostEqual(float(out["summary"]["composite_score"]), 62.3)

    def test_reject_wrong_version(self) -> None:
        raw = self._minimal_valid()
        raw["version"] = "v2"
        with self.assertRaises(ValueError):
            normalize_grid_substantiation_evidence(raw)

    def test_reject_bad_verdict(self) -> None:
        raw = self._minimal_valid()
        raw["summary"]["verdict_tier"] = "FAST CLEAR"
        with self.assertRaises(ValueError):
            normalize_grid_substantiation_evidence(raw)

    def test_reject_oversized_after_normalize(self) -> None:
        saved = os.environ.get("XCHANGE_GRID_SUB_MAX_BYTES")
        os.environ["XCHANGE_GRID_SUB_MAX_BYTES"] = "80"
        try:
            raw = self._minimal_valid()
            raw["workspace_roots"] = ["x" * 60, "y" * 60]
            with self.assertRaises(ValueError) as ctx:
                normalize_grid_substantiation_evidence(raw)
            self.assertIn("exceeds size limit", str(ctx.exception))
        finally:
            if saved is None:
                os.environ.pop("XCHANGE_GRID_SUB_MAX_BYTES", None)
            else:
                os.environ["XCHANGE_GRID_SUB_MAX_BYTES"] = saved

    def test_dimensions_whitelist_drops_unknown(self) -> None:
        raw = self._minimal_valid()
        raw["summary"]["dimensions"] = {"health": 10.0, "noise": 99.9}
        out = normalize_grid_substantiation_evidence(raw)
        self.assertIn("health", out["summary"]["dimensions"])
        self.assertNotIn("noise", out["summary"]["dimensions"])

    def test_fingerprint_bad_item_type_raises(self) -> None:
        raw = self._minimal_valid()
        raw["repo_fingerprints"] = [{"name": "GRID", "health_score": 90}, "bad"]
        with self.assertRaises(ValueError):
            normalize_grid_substantiation_evidence(raw)


class GridSubstantiationStableJsonTests(unittest.TestCase):
    def test_deterministic_serialization_budget(self) -> None:
        spec = {
            "version": "v1",
            "captured_at": "2026-05-07T08:01:02+00:00",
            "source": "grid-lumos-orchestrator",
            "summary": {
                "composite_score": 1.23,
                "verdict_tier": "FAST_CLEAR",
                "dimensions": {
                    "momentum": 10.5,
                    "health": 20.1,
                },
            },
        }
        a = normalize_grid_substantiation_evidence(dict(spec))
        b = normalize_grid_substantiation_evidence(dict(spec))
        self.assertEqual(
            json.dumps(a, sort_keys=True, separators=(",", ":")),
            json.dumps(b, sort_keys=True, separators=(",", ":")),
        )


if __name__ == "__main__":
    unittest.main()
