from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from xchange.grid_substantiation import normalize_grid_substantiation_evidence


DEFAULT_BRIDGE_PATH = Path.home() / ".caraxes" / "field-bridge.json"
DEFAULT_SEEDS_SNAPSHOT_DIR = Path.home() / ".seeds-server" / "snapshots"


class UsebError(RuntimeError):
    """Raised for operator-facing USEB collection/submission failures."""


def stable_bundle_hash(bundle: dict[str, Any]) -> str:
    raw = json.dumps(
        bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise UsebError(f"JSON file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise UsebError(f"Invalid JSON in {path}: {e}") from e
    if not isinstance(data, dict):
        raise UsebError(f"JSON file must contain an object: {path}")
    return data


def _parse_iso8601(value: Any, *, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise UsebError(f"{field} must be an ISO8601 string")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as e:
        raise UsebError(f"{field} must be ISO8601: {value}") from e
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def read_bridge_snapshot(
    path: Path = DEFAULT_BRIDGE_PATH,
    *,
    max_age_seconds: int = 300,
    allow_stale: bool = False,
) -> dict[str, Any]:
    bridge = _read_json_file(path)
    session_id = bridge.get("session_id")
    if not isinstance(session_id, str) or not session_id.strip():
        raise UsebError("Bridge snapshot missing required session_id")

    captured_at = _parse_iso8601(bridge.get("timestamp"), field="bridge.timestamp")
    age = (datetime.now(timezone.utc) - captured_at).total_seconds()
    if age > max_age_seconds and not allow_stale:
        raise UsebError(
            f"Bridge stale: age {int(age)}s > max {max_age_seconds}s. "
            "Refuse submission unless --allow-stale is set."
        )
    return bridge


def _dimension_map_from_lumos(lumos: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    scores = lumos.get("path_scores")
    if isinstance(scores, list):
        for item in scores:
            if not isinstance(item, dict):
                continue
            name = item.get("dimension")
            value = item.get("raw_value")
            if isinstance(name, str) and name in {
                "health",
                "trust",
                "drift",
                "fail",
                "momentum",
            } and isinstance(value, (int, float, str)):
                out[name] = float(value)
    return out


def grid_substantiation_from_lumos(
    lumos: dict[str, Any], *, workspace_roots: list[str] | None = None
) -> dict[str, Any]:
    completed_at = lumos.get("completed_at") or datetime.now(timezone.utc).isoformat()
    grid = {
        "version": "v1",
        "captured_at": str(completed_at),
        "workspace_roots": workspace_roots or [],
        "summary": {
            "composite_score": lumos.get("composite_score"),
            "verdict_tier": lumos.get("verdict"),
            "dimensions": _dimension_map_from_lumos(lumos),
        },
        "repo_fingerprints": _repo_fingerprints_from_lumos(lumos),
        "source": "grid-lumos-orchestrator",
    }
    return normalize_grid_substantiation_evidence(grid)


def _repo_fingerprints_from_lumos(lumos: dict[str, Any]) -> list[dict[str, Any]]:
    fingerprints: list[dict[str, Any]] = []
    state = lumos.get("ecosystem_state")
    ecosystem = state.get("ecosystem") if isinstance(state, dict) else None
    repos = ecosystem.get("repos") if isinstance(ecosystem, dict) else None
    if not isinstance(repos, list):
        return fingerprints
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        fingerprints.append(
            {
                "name": str(repo.get("name", "")),
                "health_score": repo.get("health_score", 0),
                "branch": str(repo.get("branch", "")),
                "last_commit": str(repo.get("last_commit", "")),
                "stack": str(repo.get("stack", "")),
                "uncommitted": repo.get("uncommitted", 0),
            }
        )
    return fingerprints


def latest_seeds_snapshot_path(
    snapshot_dir: Path = DEFAULT_SEEDS_SNAPSHOT_DIR,
) -> Path | None:
    if not snapshot_dir.exists():
        return None
    candidates = sorted(snapshot_dir.glob("snapshot-*.json"))
    return candidates[-1] if candidates else None


def grid_substantiation_from_seeds_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    repos = snapshot.get("repos")
    if not isinstance(repos, list):
        raise UsebError("Seeds snapshot missing repos list")

    overall = snapshot.get("overallScore", 0)
    issue_count = int(snapshot.get("issueCount", 0) or 0)
    active_count = int(snapshot.get("activeCount", 0) or 0)
    total = max(1, len(repos))
    total_uncommitted = sum(
        int(repo.get("uncommittedChanges", 0) or 0)
        for repo in repos
        if isinstance(repo, dict)
    )
    drift_score = max(0.0, 100.0 - min(float(total_uncommitted) * 2.0, 60.0))
    fail_score = max(0.0, 100.0 - min(float(issue_count) * 10.0, 80.0))
    momentum = min(100.0, (active_count / total) * 100.0)
    verdict = _verdict_from_score(float(overall))

    fingerprints: list[dict[str, Any]] = []
    roots: list[str] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        path = repo.get("path")
        if isinstance(path, str) and path:
            roots.append(path)
        fingerprints.append(
            {
                "name": str(repo.get("name", "")),
                "health_score": repo.get("healthScore", 0),
                "branch": str(repo.get("branch", "")),
                "last_commit": str(repo.get("lastCommitAge", "")),
                "stack": str(repo.get("dependencyFile", "")),
                "uncommitted": repo.get("uncommittedChanges", 0),
            }
        )

    grid = {
        "version": "v1",
        "captured_at": str(
            snapshot.get("timestamp") or datetime.now(timezone.utc).isoformat()
        ),
        "workspace_roots": roots,
        "summary": {
            "composite_score": overall,
            "verdict_tier": verdict,
            "dimensions": {
                "health": overall,
                "trust": fail_score,
                "drift": drift_score,
                "fail": fail_score,
                "momentum": momentum,
            },
        },
        "repo_fingerprints": fingerprints,
        "source": "seeds-snapshot-fallback",
    }
    return normalize_grid_substantiation_evidence(grid)


def _verdict_from_score(score: float) -> str:
    if score >= 65:
        return "FAST_CLEAR"
    if score >= 50:
        return "WATCH"
    if score >= 35:
        return "ACT"
    return "URGENT"


def build_useb_bundle(
    *,
    student_id: str,
    reward_id: str | None,
    bridge_path: Path = DEFAULT_BRIDGE_PATH,
    grid_lumos_path: Path | None = None,
    seeds_snapshot_path: Path | None = None,
    max_bridge_age_seconds: int = 300,
    allow_stale_bridge: bool = False,
    contract_satisfied: bool = False,
    ready_for_payment: bool = False,
    request_review: bool = False,
    allow_missing_grid: bool = False,
) -> dict[str, Any]:
    if not student_id.strip():
        raise UsebError("student_id is required")

    bridge = read_bridge_snapshot(
        bridge_path, max_age_seconds=max_bridge_age_seconds, allow_stale=allow_stale_bridge
    )
    grid_substantiation: dict[str, Any] | None = None
    if grid_lumos_path:
        grid_substantiation = grid_substantiation_from_lumos(
            _read_json_file(grid_lumos_path), workspace_roots=[str(grid_lumos_path.parent)]
        )
    else:
        snapshot_path = seeds_snapshot_path or latest_seeds_snapshot_path()
        if snapshot_path:
            grid_substantiation = grid_substantiation_from_seeds_snapshot(
                _read_json_file(snapshot_path)
            )
        elif not allow_missing_grid:
            raise UsebError(
                "GRID substantiation unavailable: pass --grid-lumos-path, "
                "--seeds-snapshot-path, or --allow-missing-grid"
            )

    bundle: dict[str, Any] = {
        "student_id": student_id,
        "contract_satisfied": bool(contract_satisfied),
        "ready_for_payment": bool(ready_for_payment),
        "request_review": bool(request_review),
        "bridge": bridge,
    }
    if reward_id:
        bundle["reward_id"] = reward_id
    if grid_substantiation is not None:
        bundle["grid_substantiation"] = grid_substantiation
    return bundle


def submit_useb_bundle(
    bundle: dict[str, Any],
    *,
    xchange_url: str,
    ingest_token: str,
    timeout_seconds: int = 10,
) -> dict[str, Any]:
    if not ingest_token:
        raise UsebError("XCHANGE_INGEST_TOKEN is required for submission")
    endpoint = xchange_url.rstrip("/") + "/v0/ingest/glass-bridge"
    body = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ingest_token}",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
        except Exception:
            detail = {"error": e.reason}
        raise UsebError(f"x-change submission failed: HTTP {e.code} {detail}") from e
    except urllib.error.URLError as e:
        raise UsebError(f"x-change submission failed: {e.reason}") from e

    if not isinstance(payload, dict):
        raise UsebError("x-change response was not a JSON object")
    payload["client_bundle_preflight_hash"] = stable_bundle_hash(bundle)
    return payload


def token_from_env() -> str:
    return os.environ.get("XCHANGE_INGEST_TOKEN", "")
