#!/usr/bin/env python3
"""Read-only check: payment_confirmations vs reward_ledger (stored Stripe JSON).

This does NOT call the Stripe API. It parses ``raw_event_json`` as ingested at
webhook time and compares metadata + implied PI status to ledger state.

Usage:
  XCHANGE_DB_PATH=/path/to/xchange.sqlite python3 scripts/stripe_ledger_verify.py
  python3 scripts/stripe_ledger_verify.py /path/to/xchange.sqlite --student prince

Exit 0 always; prints findings to stdout. Non-zero exit only on DB/parse errors.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class Row:
    stripe_event_id: str
    stripe_payment_intent_id: str | None
    reward_id: str
    student_id: str
    status: str
    raw_event_json: str
    ledger_state: str | None


def _parse_event(raw: str) -> dict[str, Any]:
    return json.loads(raw)


def _pi_object(event: dict[str, Any]) -> dict[str, Any] | None:
    data = event.get("data")
    if not isinstance(data, dict):
        return None
    obj = data.get("object")
    return obj if isinstance(obj, dict) else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "db_path",
        nargs="?",
        default=None,
        help="SQLite path (default: env XCHANGE_DB_PATH or ./xchange.sqlite)",
    )
    ap.add_argument("--student", help="Filter payment_confirmations.student_id")
    ap.add_argument("--since", help="Filter pc.created_at >= (ISO prefix match)")
    ap.add_argument("--until", help="Filter pc.created_at < (ISO prefix match)")
    args = ap.parse_args()

    import os

    db_path = args.db_path or os.environ.get("XCHANGE_DB_PATH") or "xchange.sqlite"

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    q = """
    SELECT pc.stripe_event_id, pc.stripe_payment_intent_id, pc.reward_id, pc.student_id,
           pc.status, pc.raw_event_json, rl.state AS ledger_state
    FROM payment_confirmations pc
    LEFT JOIN reward_ledger rl ON rl.reward_id = pc.reward_id
    WHERE 1=1
    """
    params: list[str] = []
    if args.student:
        q += " AND pc.student_id = ?"
        params.append(args.student)
    if args.since:
        q += " AND pc.created_at >= ?"
        params.append(args.since)
    if args.until:
        q += " AND pc.created_at < ?"
        params.append(args.until)
    q += " ORDER BY pc.created_at, pc.id"

    rows = [Row(**dict(r)) for r in conn.execute(q, params)]
    conn.close()

    issues: list[str] = []
    ok = 0

    # Ledger states at or after successful payment application
    post_payment = frozenset(
        {
            "payment_confirmed",
            "student_acknowledged",
            "review_requested",
        }
    )

    for r in rows:
        prefix = f"{r.stripe_event_id} reward_id={r.reward_id}"
        try:
            ev = _parse_event(r.raw_event_json)
        except json.JSONDecodeError as e:
            issues.append(f"{prefix} raw_event_json JSON error: {e}")
            continue

        if ev.get("type") != "payment_intent.succeeded":
            issues.append(f"{prefix} event.type={ev.get('type')!r} (expected payment_intent.succeeded)")

        pi = _pi_object(ev)
        if not pi:
            issues.append(f"{prefix} missing data.object in raw event")
            continue

        pi_id = pi.get("id")
        if r.stripe_payment_intent_id and pi_id and pi_id != r.stripe_payment_intent_id:
            issues.append(
                f"{prefix} PI id mismatch column={r.stripe_payment_intent_id!r} raw={pi_id!r}"
            )

        meta = pi.get("metadata")
        if isinstance(meta, dict):
            mr = meta.get("reward_id")
            ms = meta.get("student_id")
            if mr is not None and str(mr) != str(r.reward_id):
                issues.append(
                    f"{prefix} metadata.reward_id={mr!r} != row.reward_id={r.reward_id!r}"
                )
            if ms is not None and str(ms) != str(r.student_id):
                issues.append(
                    f"{prefix} metadata.student_id={ms!r} != row.student_id={r.student_id!r}"
                )

        if pi.get("status") not in (None, "succeeded"):
            issues.append(f"{prefix} PI status in raw={pi.get('status')!r} (expected succeeded)")

        if r.status == "applied":
            if r.ledger_state is None:
                issues.append(f"{prefix} status=applied but reward_ledger row missing")
            elif r.ledger_state not in post_payment:
                issues.append(
                    f"{prefix} status=applied but ledger.state={r.ledger_state!r} "
                    f"(expected one of {sorted(post_payment)})"
                )
            else:
                ok += 1
        elif r.status in ("not_applied_mismatch", "received"):
            # Mismatch already explicit; optional note
            pass

    print(f"stripe_ledger_verify db={db_path} rows={len(rows)}")
    print(f"  applied+consistent: {ok}")
    if issues:
        print(f"  issues ({len(issues)}):")
        for line in issues:
            print(f"    - {line}")
    else:
        print("  issues: none")

    return 0


if __name__ == "__main__":
    sys.exit(main())
