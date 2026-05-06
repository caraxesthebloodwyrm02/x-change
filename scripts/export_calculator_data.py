#!/usr/bin/env python3
"""Export x-change SQLite data to data/ CSV files for the reward token calculator.

Usage:
    uv run python3 scripts/export_calculator_data.py
    uv run python3 scripts/export_calculator_data.py --db /path/to/xchange.sqlite
    uv run python3 scripts/export_calculator_data.py --out /path/to/data/

Outputs (written to <out_dir>, default: ./data/):
    token_log_sample.csv       — tokens from reward_ledger (reward_token_json column)
                                  → matches Token_Log sheet column order
    reward_ledger_summary.csv  — per-reward state + token summary
    evidence_ledger_sample.csv — evidence rows (optional reward_id association)

All writes are atomic (temp file + rename). If a table has no rows, an
empty CSV with headers is written — never silently missing files.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import tempfile
from pathlib import Path

# ── Column definitions (must match data/*.csv fixtures exactly) ────────────────

TOKEN_LOG_HEADERS = [
    "token_id",
    "issued_at",
    "insight_tier",
    "base_bank_depth",
    "inferential_richness",
    "trend_position",
    "rarity_score",
    "amount",
    "issuance_trigger",
]

REWARD_SUMMARY_HEADERS = [
    "reward_id",
    "student_id",
    "state",
    "has_token",
    "insight_tier",
    "rarity_score",
    "token_amount",
    "stripe_event_id",
    "stripe_payment_intent_id",
    "created_at",
    "last_updated_at",
]

EVIDENCE_HEADERS = [
    "evidence_id",
    "reward_id",
    "student_id",
    "evidence_type",
    "payload_summary",
    "provenance",
    "created_at",
]


# ── Export helpers ─────────────────────────────────────────────────────────────

def _atomic_write_csv(path: Path, headers: list[str], rows: list[list]) -> int:
    """Write CSV atomically (tmp + rename). Returns row count written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(headers)
            writer.writerows(rows)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return len(rows)


def export_token_log(conn: sqlite3.Connection, out_path: Path) -> int:
    """Export tokens from reward_ledger.reward_token_json."""
    cur = conn.execute(
        """
        SELECT
            r.reward_id,
            r.student_id,
            r.reward_token_json,
            r.created_at
        FROM reward_ledger r
        WHERE r.reward_token_json IS NOT NULL
        ORDER BY r.created_at
        """
    )
    rows: list[list] = []
    for i, row in enumerate(cur.fetchall(), start=1):
        try:
            tok = json.loads(row["reward_token_json"])
        except (json.JSONDecodeError, TypeError):
            continue

        # Derive amount from insight_tier using the same tier→amount map as domain.py
        _tier_amounts = {
            "surface": 1, "pattern": 2, "structural": 3, "causal": 4, "theoretical": 5
        }
        tier = tok.get("insight_tier", "")
        amount = _tier_amounts.get(tier, "")

        rows.append([
            f"TKN-{i:03d}",
            tok.get("issued_at", row["created_at"]),
            tier,
            tok.get("base_bank_depth", ""),
            tok.get("inferential_richness", ""),
            tok.get("trend_position", ""),
            f"{tok.get('rarity_score', 0):.4f}" if tok.get("rarity_score") is not None else "",
            amount,
            tok.get("issuance_trigger", ""),
        ])
    return _atomic_write_csv(out_path, TOKEN_LOG_HEADERS, rows)


def export_reward_summary(conn: sqlite3.Connection, out_path: Path) -> int:
    """Export per-reward state summary."""
    # Join reward_ledger with latest payment_confirmation for stripe fields
    cur = conn.execute(
        """
        SELECT
            r.reward_id,
            r.student_id,
            r.state,
            r.reward_token_json,
            r.reward_token_amount,
            r.created_at,
            r.updated_at,
            pc.stripe_event_id,
            pc.stripe_payment_intent_id
        FROM reward_ledger r
        LEFT JOIN payment_confirmations pc
            ON pc.reward_id = r.reward_id
            AND pc.status = 'confirmed'
        ORDER BY r.created_at
        """
    )
    rows: list[list] = []
    for row in cur.fetchall():
        tok_raw = row["reward_token_json"]
        has_token = tok_raw is not None
        insight_tier = ""
        rarity_score = ""
        token_amount = row["reward_token_amount"] or ""
        if tok_raw:
            try:
                tok = json.loads(tok_raw)
                insight_tier = tok.get("insight_tier", "")
                rs = tok.get("rarity_score")
                rarity_score = f"{rs:.4f}" if rs is not None else ""
            except (json.JSONDecodeError, TypeError):
                pass

        rows.append([
            row["reward_id"],
            row["student_id"],
            row["state"],
            "true" if has_token else "false",
            insight_tier,
            rarity_score,
            token_amount,
            row["stripe_event_id"] or "",
            row["stripe_payment_intent_id"] or "",
            row["created_at"] or "",
            row["updated_at"] or row["created_at"] or "",
        ])
    return _atomic_write_csv(out_path, REWARD_SUMMARY_HEADERS, rows)


def export_evidence(conn: sqlite3.Connection, out_path: Path) -> int:
    """Export evidence_ledger rows."""
    cur = conn.execute(
        """
        SELECT
            id,
            reward_id,
            student_id,
            evidence_type,
            payload_json,
            provenance,
            created_at
        FROM evidence_ledger
        ORDER BY created_at
        """
    )
    rows: list[list] = []
    for row in cur.fetchall():
        # Summarise payload: first 120 chars of key=value pairs, no newlines
        try:
            payload = json.loads(row["payload_json"] or "{}")
            summary = " ".join(f"{k}={v}" for k, v in list(payload.items())[:4])[:120]
        except (json.JSONDecodeError, TypeError):
            summary = str(row["payload_json"] or "")[:120]

        rows.append([
            f"EVD-{row['id']:03d}",
            row["reward_id"] or "",
            row["student_id"] or "",
            row["evidence_type"] or "",
            summary,
            row["provenance"] or "",
            row["created_at"] or "",
        ])
    return _atomic_write_csv(out_path, EVIDENCE_HEADERS, rows)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--db",
        default=os.environ.get("XCHANGE_DB_PATH", "xchange.sqlite"),
        help="Path to the x-change SQLite database (default: $XCHANGE_DB_PATH or xchange.sqlite)",
    )
    parser.add_argument(
        "--out",
        default="data",
        help="Output directory for CSV files (default: ./data/)",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    out_dir = Path(args.out)

    if not db_path.exists():
        print(f"ERROR: database not found: {db_path}")
        print("Set XCHANGE_DB_PATH or pass --db /path/to/xchange.sqlite")
        raise SystemExit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        results = {
            "token_log_sample.csv":      export_token_log(conn,       out_dir / "token_log_sample.csv"),
            "reward_ledger_summary.csv": export_reward_summary(conn,  out_dir / "reward_ledger_summary.csv"),
            "evidence_ledger_sample.csv": export_evidence(conn,       out_dir / "evidence_ledger_sample.csv"),
        }
    finally:
        conn.close()

    print(f"Exported to {out_dir}/")
    for fname, count in results.items():
        print(f"  {fname}: {count} data rows")


if __name__ == "__main__":
    main()
