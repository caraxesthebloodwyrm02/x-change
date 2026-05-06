from __future__ import annotations

import json
import os
import re
from typing import Any

"""GRID substantiation evidence for USEB - validate, normalize, size-bound.

`_grid_substantiation` is evidence-only. It MUST NOT be read by domain transition
logic (`next_state_after_glass_evidence`); transitions use explicit top-level
ingest booleans only.
"""


_VERDICT_TIERS = frozenset({"FAST_CLEAR", "WATCH", "ACT", "URGENT"})
_DIM_KEYS = frozenset({"health", "trust", "drift", "fail", "momentum"})
_FINGERPRINT_KEYS = frozenset(
    {
        "name",
        "health_score",
        "branch",
        "last_commit",
        "stack",
        "uncommitted",
    }
)
_ISO8601_LOOSE = re.compile(r"^\d{4}-\d{2}-\d{2}T[0-9:.+\-Z]+$")


def _grid_substantiation_max_bytes() -> int:
    try:
        return max(1, int(os.environ.get("XCHANGE_GRID_SUB_MAX_BYTES", "65536")))
    except ValueError:
        return 65536


def _max_workspace_roots() -> int:
    try:
        return max(
            1,
            min(
                64,
                int(os.environ.get("XCHANGE_GRID_SUB_MAX_WORKSPACE_ROOTS", "32")),
            ),
        )
    except ValueError:
        return 32


def _max_fingerprints() -> int:
    try:
        return max(
            1,
            min(
                128,
                int(os.environ.get("XCHANGE_GRID_SUB_MAX_FINGERPRINTS", "50")),
            ),
        )
    except ValueError:
        return 50


def _stable_json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _as_non_empty_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"grid_substantiation.{field} must be a non-empty string")
    return value.strip()


def _as_float_0_100(value: Any, field: str) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"grid_substantiation.summary.{field} must be a number")
    try:
        x = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"grid_substantiation.summary.{field} must be a number") from e

    if x != x:
        raise ValueError(f"grid_substantiation.summary.{field} must be a finite number")
    if x < 0 or x > 100:
        raise ValueError(f"grid_substantiation.summary.{field} must be in [0, 100]")
    return round(x, 4)


def normalize_grid_substantiation_evidence(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a whitelisted, size-bounded evidence dict for `_grid_substantiation`.

    Raises:
        ValueError: on schema or size violations.
    """

    version = _as_non_empty_str(raw.get("version"), "version")
    if version != "v1":
        raise ValueError("grid_substantiation.version must be 'v1'")

    captured_at = _as_non_empty_str(raw.get("captured_at"), "captured_at")
    if not _ISO8601_LOOSE.match(captured_at):
        raise ValueError("grid_substantiation.captured_at must be ISO8601-like")

    source = _as_non_empty_str(raw.get("source"), "source")
    if len(source) > 128:
        raise ValueError("grid_substantiation.source too long")

    summary_in = raw.get("summary")
    if not isinstance(summary_in, dict):
        raise ValueError("grid_substantiation.summary must be an object")

    composite = _as_float_0_100(summary_in.get("composite_score"), "composite_score")
    verdict_tier = _as_non_empty_str(summary_in.get("verdict_tier"), "verdict_tier").upper()
    if verdict_tier not in _VERDICT_TIERS:
        raise ValueError(
            "grid_substantiation.summary.verdict_tier must be one of: "
            + ", ".join(sorted(_VERDICT_TIERS))
        )

    dimensions: dict[str, float] = {}
    dim_in = summary_in.get("dimensions")
    if dim_in is not None:
        if not isinstance(dim_in, dict):
            raise ValueError("grid_substantiation.summary.dimensions must be an object")
        for k, v in dim_in.items():
            if k not in _DIM_KEYS:
                continue
            dimensions[k] = _as_float_0_100(v, f"dimensions.{k}")

    summary_out: dict[str, Any] = {
        "composite_score": composite,
        "verdict_tier": verdict_tier,
    }
    if dimensions:
        summary_out["dimensions"] = {k: dimensions[k] for k in sorted(dimensions.keys())}

    roots_in = raw.get("workspace_roots")
    workspace_roots: list[str] = []
    if roots_in is not None:
        if not isinstance(roots_in, list):
            raise ValueError("grid_substantiation.workspace_roots must be a list")
        cap = _max_workspace_roots()
        for item in roots_in[:cap]:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    "grid_substantiation.workspace_roots entries must be non-empty strings"
                )
            s = item.strip()
            if len(s) > 512:
                raise ValueError("grid_substantiation.workspace_roots entry too long")
            workspace_roots.append(s)

    fps_in = raw.get("repo_fingerprints")
    repo_fingerprints: list[dict[str, Any]] = []
    if fps_in is not None:
        if not isinstance(fps_in, list):
            raise ValueError("grid_substantiation.repo_fingerprints must be a list")
        cap = _max_fingerprints()
        for item in fps_in[:cap]:
            if not isinstance(item, dict):
                raise ValueError("grid_substantiation.repo_fingerprints items must be objects")
            fp: dict[str, Any] = {}
            for key in _FINGERPRINT_KEYS:
                if key not in item:
                    continue
                val = item[key]
                if key in ("health_score", "uncommitted"):
                    if val is None or isinstance(val, bool):
                        raise ValueError(f"repo_fingerprints.{key} must be numeric")
                    try:
                        fp[key] = int(val) if key == "uncommitted" else float(val)
                    except (TypeError, ValueError) as e:
                        raise ValueError(f"repo_fingerprints.{key} must be numeric") from e
                    continue

                if not isinstance(val, str):
                    raise ValueError(f"repo_fingerprints.{key} must be a string")
                s = val.strip()
                if len(s) > 256:
                    raise ValueError(f"repo_fingerprints.{key} too long")
                fp[key] = s

            if not fp:
                continue
            repo_fingerprints.append(fp)

    out: dict[str, Any] = {
        "version": version,
        "captured_at": captured_at,
        "source": source,
        "summary": summary_out,
    }
    if workspace_roots:
        out["workspace_roots"] = workspace_roots
    if repo_fingerprints:
        out["repo_fingerprints"] = repo_fingerprints

    max_b = _grid_substantiation_max_bytes()
    serialized = _stable_json_bytes(out)
    if len(serialized) > max_b:
        raise ValueError(
            f"grid_substantiation exceeds size limit: {len(serialized)} bytes (max {max_b})"
        )

    return out
