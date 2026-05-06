#!/usr/bin/env python3
import sqlite3
import json
import os
import argparse
import sys

def get_db_path():
    # If we are in tools/, the DB is likely one level up
    default_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "xchange.sqlite")
    return os.environ.get("XCHANGE_DB_PATH", default_db)

def main():
    parser = argparse.ArgumentParser(description="View x-change inbox entries")
    parser.add_argument("--status", help="Filter by status (e.g. unprocessed)", default=None)
    args = parser.parse_args()

    db_path = get_db_path()
    if not os.path.exists(db_path):
        print(json.dumps({"error": f"Database not found at {db_path}"}, indent=2))
        sys.exit(1)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM inbox_entries"
        params = []
        if args.status:
            query += " WHERE status = ?"
            params.append(args.status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        entries = [dict(row) for row in rows]
        print(json.dumps(entries, indent=2))
        
    except sqlite3.OperationalError as e:
        print(json.dumps({"error": str(e)}, indent=2))
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
