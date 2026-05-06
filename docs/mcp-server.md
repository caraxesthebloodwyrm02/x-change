# x-change MCP server (read-only)

Phase-1 **stdio** MCP surface over the SQLite ledger. Implements the “MCP boundary” read tools described in [`finance-agents-modernization.md`](finance-agents-modernization.md): operators and agents can inspect `support_signals`, outcomes, rewards, exchange requests, and payment rows **without** opening SQL manually.

## Requirements

- Dependency group **`mcp`** in `pyproject.toml` (official MCP Python SDK + FastMCP). The HTTP server remains stdlib-only; MCP is optional tooling.
- Env: **`XCHANGE_DB_PATH`** (default `xchange.sqlite`, cwd-relative).

## Run

```bash
cd /path/to/x-change
export XCHANGE_DB_PATH="$PWD/xchange.sqlite"
PYTHONPATH="$PWD/src" uv run --group mcp python -m xchange.xchange_mcp
```

### Cursor / Claude Code wiring

Register a **stdio** server whose command matches the block above. Trust boundary: whoever launches the process can read the DB file—same as possessing the SQLite path.

Example fragment (`mcpServers`):

```json
"xchange": {
  "command": "uv",
  "args": ["run", "--group", "mcp", "python", "-m", "xchange.xchange_mcp"],
  "cwd": "/absolute/path/to/x-change",
  "env": {
    "PYTHONPATH": "/absolute/path/to/x-change/src",
    "XCHANGE_DB_PATH": "/absolute/path/to/x-change/xchange.sqlite"
  }
}
```

## Tools (prefix `xchange_`)

| Tool | Purpose |
|------|---------|
| `xchange_list_support_signals` | Exception queue with optional `kind`, `resolved`, pagination (`limit` ≤ 100, `offset`). |
| `xchange_get_outcome_summary` | `reward_ledger` counts by state; optional `student_id`. |
| `xchange_get_reward_state` | Bundle: ledger row, evidence list, payment summaries for one `reward_id`. |
| `xchange_list_exchange_requests` | Token exchange requests with filters + pagination. |
| `xchange_list_payment_confirmations` | Payment rows **without** `raw_event_json` (operator-safe). |

Pure-logic helpers live in [`src/xchange/mcp_read.py`](../src/xchange/mcp_read.py) and are covered by unit tests without importing the MCP SDK.

## Inspector

```bash
npx @modelcontextprotocol/inspector --transport stdio -- \
  uv run --directory /path/to/x-change --group mcp python -m xchange.xchange_mcp
```

(Adjust `--directory`, `PYTHONPATH` in env if your inspector invocation differs.)

## Non-goals (v0)

- No write tools (`resolve_support_signal`, ingest, Stripe) over MCP until human-gated design is explicit.
- No replacement for `POST /v0/stripe/webhook` HMAC verification.

## Evaluations

See [`evaluation/xchange-mcp-evaluation.xml`](evaluation/xchange-mcp-evaluation.xml) for read-only scenario questions used to sanity-check agent tool use.
