#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _ensure_src_path() -> None:
    src = _repo_root() / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _parser() -> argparse.ArgumentParser:
    default_bridge = Path.home() / ".caraxes" / "field-bridge.json"
    p = argparse.ArgumentParser(
        description="Submit a Unified Session Evidence Bundle to x-change."
    )
    p.add_argument("--student-id", required=True)
    p.add_argument("--reward-id")
    p.add_argument("--bridge-path", type=Path, default=default_bridge)
    p.add_argument("--grid-lumos-path", type=Path)
    p.add_argument("--seeds-snapshot-path", type=Path)
    p.add_argument(
        "--grid-json",
        type=Path,
        help="Backward-compatible alias for --grid-lumos-path.",
    )
    p.add_argument("--max-bridge-age-seconds", type=int, default=300)
    p.add_argument("--allow-stale", action="store_true")
    p.add_argument("--allow-missing-grid", action="store_true")
    p.add_argument("--no-grid", action="store_true", help="Alias for --allow-missing-grid.")
    p.add_argument("--contract-satisfied", action="store_true")
    p.add_argument("--ready-for-payment", action="store_true")
    p.add_argument("--request-review", action="store_true")
    p.add_argument("--xchange-url", default="http://127.0.0.1:8788")
    p.add_argument("--timeout-seconds", type=int, default=10)
    p.add_argument("--receipt", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    _ensure_src_path()
    from xchange.useb import (
        UsebError,
        build_useb_bundle,
        stable_bundle_hash,
        submit_useb_bundle,
        token_from_env,
    )

    args = _parser().parse_args(argv)
    try:
        bundle = build_useb_bundle(
            student_id=args.student_id,
            reward_id=args.reward_id,
            bridge_path=args.bridge_path,
            grid_lumos_path=args.grid_lumos_path or args.grid_json,
            seeds_snapshot_path=args.seeds_snapshot_path,
            max_bridge_age_seconds=args.max_bridge_age_seconds,
            allow_stale_bridge=args.allow_stale,
            contract_satisfied=args.contract_satisfied,
            ready_for_payment=args.ready_for_payment,
            request_review=args.request_review,
            allow_missing_grid=args.allow_missing_grid or args.no_grid,
        )
        result = submit_useb_bundle(
            bundle,
            xchange_url=args.xchange_url,
            ingest_token=token_from_env(),
            timeout_seconds=args.timeout_seconds,
        )
        if args.receipt:
            result = {
                "ok": bool(result.get("ok")),
                "session_id": bundle["bridge"]["session_id"],
                "evidence_recorded": bool(result.get("evidence_recorded")),
                "transition": result.get("transition"),
                "bundle_hash": result.get("bundle_hash") or stable_bundle_hash(bundle),
            }

        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except UsebError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
