from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from xchange.useb import (
    UsebError,
    build_useb_bundle,
    grid_substantiation_from_lumos,
    grid_substantiation_from_seeds_snapshot,
    stable_bundle_hash,
)


def _bridge(timestamp: str) -> dict[str, object]:
    return {
        "timestamp": timestamp,
        "session_id": "useb-session-1",
        "agent_state": "idle",
        "threshold_state": "ground",
        "progress": 0,
        "blocks": [],
        "conversation": [],
        "voices": [],
        "signals": {
            "git_diff_lines": 0,
            "iteration_count": 0,
            "session_age_minutes": 1,
        },
    }


class UsebTests(unittest.TestCase):
    def test_build_bundle_with_seeds_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bridge_path = root / "bridge.json"
            bridge_path.write_text(
                json.dumps(_bridge(datetime.now(timezone.utc).isoformat())),
                encoding="utf-8",
            )
            seeds_path = root / "seeds.json"
            seeds_path.write_text(
                json.dumps(
                    {
                        "timestamp": "2026-05-06T18:00:00Z",
                        "overallScore": 94,
                        "activeCount": 1,
                        "issueCount": 0,
                        "repos": [
                            {
                                "name": "GRID",
                                "path": "/grid",
                                "healthScore": 94,
                                "branch": "main",
                                "uncommittedChanges": 0,
                                "lastCommitAge": "20 hours ago",
                                "dependencyFile": "pyproject.toml",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            bundle = build_useb_bundle(
                student_id="stu-1",
                reward_id="rwd-1",
                bridge_path=bridge_path,
                seeds_snapshot_path=seeds_path,
            )

        self.assertEqual(bundle["bridge"]["session_id"], "useb-session-1")
        self.assertEqual(bundle["grid_substantiation"]["summary"]["verdict_tier"], "FAST_CLEAR")
        self.assertEqual(stable_bundle_hash(bundle)[:7], "sha256:")

    def test_stale_bridge_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bridge_path = Path(tmp) / "bridge.json"
            stale = datetime.now(timezone.utc) - timedelta(seconds=1480)
            bridge_path.write_text(json.dumps(_bridge(stale.isoformat())), encoding="utf-8")
            with self.assertRaisesRegex(UsebError, "Bridge stale"):
                build_useb_bundle(
                    student_id="stu-1",
                    reward_id=None,
                    bridge_path=bridge_path,
                    allow_missing_grid=True,
                    max_bridge_age_seconds=300,
                )

    def test_lumos_normalization(self) -> None:
        grid = grid_substantiation_from_lumos(
            {
                "completed_at": "2026-05-06T18:00:00+00:00",
                "composite_score": 62.3,
                "verdict": "WATCH",
                "path_scores": [
                    {"dimension": "health", "raw_value": 94},
                    {"dimension": "trust", "raw_value": 85},
                ],
                "ecosystem_state": {
                    "ecosystem": {
                        "repos": [
                            {
                                "name": "GRID",
                                "health_score": 94,
                                "branch": "main",
                                "last_commit": "20 hours ago",
                                "stack": "Python",
                                "uncommitted": 0,
                            }
                        ]
                    }
                },
            }
        )
        self.assertEqual(grid["source"], "grid-lumos-orchestrator")
        self.assertEqual(grid["summary"]["dimensions"]["health"], 94.0)

    def test_seeds_snapshot_normalization(self) -> None:
        grid = grid_substantiation_from_seeds_snapshot(
            {
                "timestamp": "2026-05-06T18:00:00Z",
                "overallScore": 62,
                "activeCount": 1,
                "issueCount": 1,
                "repos": [
                    {
                        "name": "GRID",
                        "path": "/grid",
                        "healthScore": 62,
                        "branch": "main",
                        "uncommittedChanges": 2,
                        "lastCommitAge": "20 hours ago",
                        "dependencyFile": "pyproject.toml",
                    }
                ],
            }
        )
        self.assertEqual(grid["source"], "seeds-snapshot-fallback")
        self.assertEqual(grid["summary"]["verdict_tier"], "WATCH")


if __name__ == "__main__":
    unittest.main()
