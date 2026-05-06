# Anthropic Financial Services — integration with x-change

This note connects the **[anthropics/financial-services](https://github.com/anthropics/financial-services)** distribution to the x-change codebase. The bundle’s **marketplace id** (used after `@` when installing plugins) is **`claude-for-financial-services`**, declared in upstream `.claude-plugin/marketplace.json` — but you must **add the Git repo `anthropics/financial-services`**, not a repo named `claude-for-financial-services` (that URL 404s on GitHub).

## What it is (and is not)

| Fact | Detail |
| --- | --- |
| **Not** a PyPI / `uv` dependency | x-change stays zero third-party runtime deps; there is nothing to add in `pyproject.toml`. |
| **Is** a file-based toolkit | Markdown skills, slash commands, optional **MCP HTTP connector URLs**, and **Managed Agent** cookbooks under `managed-agent-cookbooks/`. |
| **Runs in** Claude Cowork, Claude Code (plugins), or your own orchestrator calling the [Claude Managed Agents API](https://docs.claude.com/en/api/managed-agents). |

Upstream disclaimer (summary): templates produce **draft** work product for human review; they do not execute trades, bind risk, or post to your ledger. See the repository README for the full notice.

## Official documentation

| Topic | URL |
| --- | --- |
| Repository root (layout, agents, verticals) | [github.com/anthropics/financial-services](https://github.com/anthropics/financial-services) |
| Managed Agents API | [docs.claude.com — Managed Agents](https://docs.claude.com/en/api/managed-agents) |
| MCP protocol | [modelcontextprotocol.io](https://modelcontextprotocol.io/) |

Cookbooks and deploy automation live under `managed-agent-cookbooks/` and `scripts/` in that repository (`deploy-managed-agent.sh`, `orchestrate.py`).

## Local reference copy (this workspace)

To pull a **read-only** tree for inspection (skills, `.mcp.json`, cookbooks), run from the repo root:

```bash
./scripts/bootstrap-financial-services-ref.sh
```

That clones into `third_party/anthropic-financial-services/`, which is **gitignored** so the large tree is not committed. Re-run after deleting the folder to refresh.

## Claude Code — install plugins from the marketplace

**Add** the marketplace using the **real GitHub repo** (this is what `claude plugin marketplace add` clones):

```bash
claude plugin marketplace add anthropics/financial-services
```

On success, the CLI registers it under the **declared** name `claude-for-financial-services`. Then install with that suffix:

```bash
claude plugin install financial-analysis@claude-for-financial-services
# Optional agents aligned with ops / close themes:
claude plugin install gl-reconciler@claude-for-financial-services
claude plugin install month-end-closer@claude-for-financial-services
```

If you previously ran `claude plugin marketplace add anthropics/claude-for-financial-services` and saw `Repository not found`, remove the broken entry and re-add:

```bash
claude plugin marketplace rm claude-for-financial-services   # ignore errors if it never registered
claude plugin marketplace add anthropics/financial-services
```

Install additional verticals or agents from `.claude-plugin/marketplace.json` in the upstream repo if you need IB, equity research, PE, wealth, fund-admin, or partner bundles.

**Note:** Upstream’s README sometimes shows `anthropics/claude-for-financial-services` as the marketplace add target; that path does not exist on GitHub. Use **`anthropics/financial-services`** for `marketplace add` only.

## MCP data connectors (financial-analysis)

The core vertical **`financial-analysis`** ships HTTP MCP endpoints in:

`plugins/vertical-plugins/financial-analysis/.mcp.json`

Each entry points at a **vendor-hosted** MCP URL (Daloopa, Morningstar, FactSet, LSEG, etc.). Enabling them in Cursor or another host requires your editor’s MCP config plus **provider credentials** where the vendor requires them; x-change does not inject secrets.

To reuse the same server list in Cursor, merge the `mcpServers` object from that file into your user or workspace MCP JSON (see Cursor docs for MCP configuration).

## How this relates to x-change

x-change is a principled **reward ledger + Stripe webhook + Glass evidence** service. Anthropic’s bundle is **analyst / ops agent** tooling. Meaningful integration is at the **workflow boundary**, not inside `http.server`:

1. **Policy and API contract** — agents that touch rewards or support signals should follow [`policy-core-v0.md`](policy-core-v0.md) and [`stripe-boundary.md`](stripe-boundary.md).
2. **Roadmap** — [`finance-agents-modernization.md`](finance-agents-modernization.md) describes a phased approach (x-change MCP read tools, governed writes, Stripe read connector, auditor / month-end agents). Financial-services plugins are **reference implementations** for those agent and skill patterns.
3. **Stripe** — financial-services does not replace x-change’s webhook verification; keep using `POST /v0/stripe/webhook` and idempotent `payment_confirmations` as today.

## Managed Agents (headless)

From the cloned reference:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
scripts/deploy-managed-agent.sh <agent-name>
```

Use upstream `managed-agent-cookbooks/<agent>/` for `agent.yaml`, subagent layout, and security notes before deploying in your environment.

## See also

- [`evaluation/README.md`](evaluation/README.md) — dual audits (x-change + FSI), complement matrix, combo trial scores, `fsi-asset-index.json`
- [`glass-xchange-fsi-release-audit.md`](glass-xchange-fsi-release-audit.md) — Glass on the ingest pipeline, audit vs installed FSI agents, relevancy scoring with Glass included
