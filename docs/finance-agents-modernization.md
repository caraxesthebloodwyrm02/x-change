# x-change: AI Finance Agents Modernization Strategy

## 1. Executive Summary
This document outlines the strategic roadmap to evolve `x-change` from a deterministic, rule-based webhook receiver into an AI-augmented financial operations system. It aligns the existing `x-change` architecture with the **Anthropic Finance Agents** paradigm, specifically focusing on back-office automation (Support Signal Auditing and Ledger Reconciliation) via the Model Context Protocol (MCP).

## 2. The Anthropic Finance Agents Paradigm
Anthropic's Finance Agents framework introduces ready-to-run agent templates for time-consuming financial tasks (e.g., General Ledger Reconciler, KYC Screener, Month-End Closer).

The core architecture of this paradigm consists of three pillars:
1.  **Skills:** Strict instructions and domain knowledge for specific financial tasks.
2.  **Connectors & MCP Apps:** Governed, real-time read/write access to internal data warehouses and external providers (e.g., Stripe, Dun & Bradstreet).
3.  **Subagents:** Specialized Claude models invoked by the main agent for narrow sub-tasks (e.g., a pure policy auditor).

In this paradigm, humans transition from manual data-entry and triage operators into a "human-in-the-loop" approval and oversight role.

---

## 3. Gap Calculation: Current State vs. Future State

`x-change` currently operates as a highly isolated, zero-dependency `http.server` running SQLite ledgers (`reward_ledger`, `payment_confirmations`, `support_signals`).

| Operational Area | Current `x-change` State (Deterministic) | Future State (Anthropic Finance Agents) |
| :--- | :--- | :--- |
| **Exception Handling** | Missing Stripe metadata emits a `support_signal`. A human operator must manually search the Stripe Dashboard, deduce the error, and execute `POST /v0/support-signals/<id>/resolve`. | An **Auditor Agent** detects the signal, queries the Stripe MCP to find the missing intent, deduces the root cause, and drafts the `resolve` payload for human approval. |
| **Ledger Reconciliation** | The `payment_confirmations` table and `reward_ledger` must be manually queried with SQL to verify that delivered rewards match actual settled funds at month-end. | A **General Ledger Reconciler** agent automatically compares the SQLite tables against Stripe settlement reports via MCP to produce a Markdown "Close Report." |
| **System Interoperability** | `x-change` exposes raw HTTP REST endpoints. Claude cannot natively discover or interact with the ledger securely. | `x-change` exposes an **MCP interface** (Model Context Protocol), allowing Claude to natively query ledgers and invoke transitions under strict RBAC constraints. |

---

## 4. Phased Implementation Roadmap

To close this gap, we must systematically upgrade `x-change` by building an MCP perimeter and deploying specialized financial agents.

### Phase 1: Establish the MCP Boundary (x-change MCP Server)
To allow AI agents to interact with the system, `x-change` must become an MCP App.

**Status (partial):** Read-only stdio MCP is implemented as `src/xchange/xchange_mcp.py` with helpers in `src/xchange/mcp_read.py`. See [`mcp-server.md`](mcp-server.md) for tools and Cursor wiring. Governed write tools remain future work.

1.  **Wrap the Storage Layer:** MCP adapter runs alongside (not inside) the HTTP server; optional uv dependency group `mcp`.
2.  **Expose Read Tools:** Implemented tools (prefixed `xchange_`) mirror operator visibility: support signals, outcome summary, reward bundle, exchange requests, payment confirmation summaries (no raw Stripe JSON).
3.  **Expose Governed Write Tools:** Create a tool to resolve anomalies.
    *   `resolve_support_signal(signal_id, resolution_notes)`
    *   *Constraint:* This tool must require human-in-the-loop confirmation before the MCP server executes the database write.

### Phase 2: Implement the External Stripe Connector
The AI needs an omniscient view of both internal state (`x-change`) and external reality (Stripe).
1.  **Stripe MCP Server:** Deploy a secure MCP server with read-only API access to the organization's Stripe account.
2.  **Tool Configuration:** Expose `search_payment_intents()` and `get_charge_metadata()`.

### Phase 3: Build the "Support Signal Auditor" Agent
Package the logic into a Claude Code Plugin or Managed Agent Cookbook.
1.  **Define the Skill (`SKILL.md`):**
    *   Instruct the agent to routinely poll the `x-change` MCP for open support signals.
    *   When a signal indicates a metadata mismatch, extract the provided `payment_intent` ID.
    *   Query the Stripe MCP to retrieve the raw webhook payload that Stripe originally sent.
    *   Identify the discrepancy (e.g., student ID mismatch, missing course ID).
    *   Draft a resolution plan and stage the `resolve_support_signal` tool call for human approval.
2.  **Policy Subagent:** If the anomaly involves a complex state rollback, hand the context to a subagent explicitly instructed to read only `docs/policy-core-v0.md` to guarantee policy compliance.

### Phase 4: Implement the "Month-End Closer" Routine
Automate the month-end reconciliation process.
1.  **Scheduled Trigger:** Configure the agent to run on the 1st of every month.
2.  **Execution Flow:**
    *   Query `x-change` for all `payment_confirmed` rewards in the prior 30 days.
    *   Query the Stripe MCP for actual settled payouts.
    *   Perform a diff on the expected funds vs. settled funds.
3.  **Output Generation:** The agent compiles a "Close Report" artifact summarizing any financial leaks, unacknowledged rewards, or pending payouts, fulfilling the core promise of the Anthropic Finance Agents framework.
