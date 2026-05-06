"""Read-only helpers for MCP tools over x-change SQLite.

Pure stdlib + storage — safe to test without the ``mcp`` package installed.
"""

from __future__ import annotations

import os
from typing import Any

from xchange.storage import (
    get_outcome_summary,
    get_reward_state,
    list_exchange_requests,
    list_payment_confirmations,
    list_support_signals,
    open_db,
)

MAX_PAGE: int = 100


def db_path_from_env() -> str:
    return os.environ.get("XCHANGE_DB_PATH", "xchange.sqlite")


def clamp_limit(limit: int) -> int:
    return max(1, min(limit, MAX_PAGE))


def clamp_offset(offset: int) -> int:
    return max(0, offset)


def list_support_signals_page(
    db_path: str,
    *,
    kind: str | None = None,
    resolved: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    lim = clamp_limit(limit)
    off = clamp_offset(offset)
    with open_db(db_path) as conn:
        rows = list_support_signals(
            conn=conn,
            kind=kind,
            resolved=resolved,
            limit=lim + 1,
            offset=off,
        )
    has_more = len(rows) > lim
    return {
        "items": rows[:lim],
        "has_more": has_more,
        "limit": lim,
        "offset": off,
    }


def read_outcome_summary(db_path: str, *, student_id: str | None = None) -> dict[str, Any]:
    with open_db(db_path) as conn:
        return get_outcome_summary(conn, student_id=student_id)


def read_reward_state(db_path: str, *, reward_id: str) -> dict[str, Any]:
    with open_db(db_path) as conn:
        row = get_reward_state(conn, reward_id=reward_id)
    if row is None:
        return {"error": "reward_not_found", "reward_id": reward_id}
    return row


def list_exchange_requests_page(
    db_path: str,
    *,
    student_id: str | None = None,
    reward_id: str | None = None,
    approved: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    lim = clamp_limit(limit)
    off = clamp_offset(offset)
    with open_db(db_path) as conn:
        rows = list_exchange_requests(
            conn=conn,
            student_id=student_id,
            reward_id=reward_id,
            approved=approved,
            limit=lim + 1,
            offset=off,
        )
    has_more = len(rows) > lim
    return {
        "items": rows[:lim],
        "has_more": has_more,
        "limit": lim,
        "offset": off,
    }


def list_payment_confirmations_page(
    db_path: str,
    *,
    reward_id: str | None = None,
    student_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    lim = clamp_limit(limit)
    off = clamp_offset(offset)
    with open_db(db_path) as conn:
        rows = list_payment_confirmations(
            conn=conn,
            reward_id=reward_id,
            student_id=student_id,
            status=status,
            limit=lim + 1,
            offset=off,
        )
    has_more = len(rows) > lim
    return {
        "items": rows[:lim],
        "has_more": has_more,
        "limit": lim,
        "offset": off,
        "note": "raw_event_json omitted; use HTTP reward state or DB export if required",
    }
