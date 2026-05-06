"""stdio MCP server: read-only tools over x-change SQLite.

Run::

    PYTHONPATH=src uv run --group mcp python -m xchange.xchange_mcp

Requires dependency group ``mcp`` (see pyproject.toml). Core HTTP server has zero
third-party runtime deps; this module is optional tooling.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from xchange import mcp_read

_READ = ToolAnnotations(
    title="Read-only x-change",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

mcp = FastMCP(
    "xchange_mcp",
    instructions=(
        "Read-only access to the x-change reward ledger (SQLite). "
        "Evidence payloads are supporting context only; state transitions stay "
        "in domain.py / HTTP surfaces. Set XCHANGE_DB_PATH (default xchange.sqlite)."
    ),
)


def _dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool(
    name="xchange_list_support_signals",
    annotations=_READ,
    description=(
        "List support_signals (operator exception queue). "
        "Filter by kind and/or resolved flag; newest first. "
        "Pagination: limit max 100, offset for skipping rows."
    ),
)
async def xchange_list_support_signals(
    kind: str | None = None,
    resolved: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    path = mcp_read.db_path_from_env()
    data = mcp_read.list_support_signals_page(
        path, kind=kind, resolved=resolved, limit=limit, offset=offset
    )
    return _dump(data)


@mcp.tool(
    name="xchange_get_outcome_summary",
    annotations=_READ,
    description=(
        "Aggregate reward counts by lifecycle state (reward_ledger). "
        "Optional student_id filters to one learner."
    ),
)
async def xchange_get_outcome_summary(student_id: str | None = None) -> str:
    path = mcp_read.db_path_from_env()
    return _dump(mcp_read.read_outcome_summary(path, student_id=student_id))


@mcp.tool(
    name="xchange_get_reward_state",
    annotations=_READ,
    description=(
        "Full reward bundle: ledger row, linked evidence (typed payloads), "
        "payment_confirmation summaries for this reward_id (no raw Stripe JSON)."
    ),
)
async def xchange_get_reward_state(reward_id: str) -> str:
    path = mcp_read.db_path_from_env()
    return _dump(mcp_read.read_reward_state(path, reward_id=reward_id.strip()))


@mcp.tool(
    name="xchange_list_exchange_requests",
    annotations=_READ,
    description=(
        "List token exchange requests with optional filters; newest first. "
        "limit max 100."
    ),
)
async def xchange_list_exchange_requests(
    student_id: str | None = None,
    reward_id: str | None = None,
    approved: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    path = mcp_read.db_path_from_env()
    data = mcp_read.list_exchange_requests_page(
        path,
        student_id=student_id,
        reward_id=reward_id,
        approved=approved,
        limit=limit,
        offset=offset,
    )
    return _dump(data)


@mcp.tool(
    name="xchange_list_payment_confirmations",
    annotations=_READ,
    description=(
        "List payment_confirmations rows without raw_event_json "
        "(stripe_event_id, intent id, reward_id, status, timestamps)."
    ),
)
async def xchange_list_payment_confirmations(
    reward_id: str | None = None,
    student_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> str:
    path = mcp_read.db_path_from_env()
    data = mcp_read.list_payment_confirmations_page(
        path,
        reward_id=reward_id,
        student_id=student_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return _dump(data)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
