"""Validate the session_memory completion gate.

Proves five conditions from MEMORY-AUTHORITY.md Retrieval Validation:
  1. Ingest a new non-secret note
  2. Retrieve by key + scope
  3. Every row has source_path + created_at
  4. Stale entries excluded by default
  5. mark_stale_memory flags entries
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from xchange.storage import (
    get_memory_freshness_report,
    mark_stale_memory,
    open_db,
    retrieve_session_memory,
    store_session_memory,
)


def main() -> int:
    db_path = os.environ.get("XCHANGE_DB_PATH", os.path.join(tempfile.gettempdir(), "xchange_memory_validate.sqlite"))
    # Clean start — remove leftover from prior runs
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass

    failures = 0

    with open_db(db_path) as conn:
        # --- Condition 1: Ingest ---
        mid = store_session_memory(
            conn=conn,
            memory_key="batch-01-test",
            memory_value="BATCH-01 memory authority reference implementation validated",
            source_path="/home/irfankabir/x-change/src/xchange/storage.py",
            scope="x-change",
            session_id="validate-2026-05-07",
        )
        assert mid > 0, "expected non-zero row id after insert"
        print(f"PASS 1: ingested row id={mid}")

        # --- Condition 2: Retrieve by key + scope ---
        rows = retrieve_session_memory(conn=conn, memory_key="batch-01-test", scope="x-change")
        assert len(rows) == 1, f"expected 1 row, got {len(rows)}"
        print("PASS 2: retrieved by key + scope")

        # --- Condition 3: Every row has freshness metadata ---
        row = rows[0]
        assert row["source_path"] == "/home/irfankabir/x-change/src/xchange/storage.py", "source_path missing/mismatch"
        assert row["created_at"] is not None, "created_at missing"
        assert row["is_stale"] == 0, "fresh row should have is_stale=0"
        print(f"PASS 3: freshness metadata present (source_path={row['source_path']}, created_at={row['created_at']})")

        # --- Condition 5 (run before 4 so we can test exclusion): mark stale ---
        ok = mark_stale_memory(conn=conn, memory_id=mid)
        assert ok, "mark_stale_memory should return True"
        # Verify stale flag stuck
        updated = retrieve_session_memory(conn=conn, memory_key="batch-01-test", scope="x-change", include_stale=True)
        assert len(updated) == 1, "include_stale=True should find the stale row"
        assert updated[0]["is_stale"] == 1, "stale flag not set"
        assert updated[0]["stale_checked_at"] is not None, "stale_checked_at not set"
        print(f"PASS 5: mark_stale_memory flagged row (stale_checked_at={updated[0]['stale_checked_at']})")

        # --- Condition 4: Stale excluded by default ---
        fresh_only = retrieve_session_memory(conn=conn, memory_key="batch-01-test", scope="x-change")
        assert len(fresh_only) == 0, "default retrieval should exclude stale rows"
        print("PASS 4: stale entries excluded from default retrieval")

        # --- Freshness report ---
        report = get_memory_freshness_report(conn=conn, scope="x-change")
        assert report["total"] == 1, f"expected 1 total, got {report['total']}"
        assert report["stale"] == 1, f"expected 1 stale, got {report['stale']}"
        assert report["fresh"] == 0, f"expected 0 fresh, got {report['fresh']}"
        print(f"PASS freshness_report: total={report['total']} fresh={report['fresh']} stale={report['stale']}")

    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass

    print(f"\n{'ALL 5 CONDITIONS PASS' if failures == 0 else f'{failures} FAILURES'}")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
