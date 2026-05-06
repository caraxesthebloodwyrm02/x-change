# Agent Handoff Pack - 2026-05-06

## Main Goal

This pack turns the ecosystem inventory from the May 6, 2026 discovery thread into an executable agent handoff. A future agent should be able to start here, acquire context, choose a batch, and move without redoing broad discovery.

The immediate goal is not to reorganize the whole machine. The immediate goal is to preserve momentum by giving future work a clear surface map, rules, inputs, scopes, and acceptance criteria.

## Directory Map

| Path | Purpose |
|---|---|
| `00-master/` | Goal, surface map, handoff inventory, and preparedness gate. |
| `01-source-maps/` | Canonical source docs moved from the discovery thread. |
| `02-agent-equipment/` | Prompt, operating rules, context acquisition, workflows, and skill loadout. |
| `03-batches/` | Digestible implementation scopes with inputs, outputs, safety limits, and examples. |
| `04-schemas/` | JSON schemas for fix candidates, batches, preparedness checks, and asset registry entries. |
| `05-execution/` | Execution order, parallelization matrix, and acceptance criteria. |
| `06-authority/` | Seed authority records for memory, MCP, toolchain, maintenance, custom assets, directory, domain, and resurfacing work. |
| `07-registries/` | Machine-readable implementation records derived from the authority docs. |

## Source Maps

Read these as the factual base:

1. [Portfolio Inventory Benchmark](01-source-maps/portfolio-inventory-benchmark.md)
2. [Directory Structure Consolidation Playbook](01-source-maps/directory-structure-consolidation-playbook.md)
3. [Domain Landscape Allocation](01-source-maps/domain-landscape-local-asset-allocation.md)
4. [Buried Assets Resurfacing Inventory](01-source-maps/buried-assets-resurfacing-inventory.md)
5. [Custom Harness And Agentic Performance Audit](01-source-maps/custom-harness-agentic-performance-audit.md)
6. [Development Toolchain Wiring Maintenance Audit](01-source-maps/development-toolchain-wiring-maintenance-audit.md)
7. [Development Wiring Fix Candidates](01-source-maps/development-wiring-fix-candidates.json)

## First Move For Any Agent

1. Read [MAIN-GOAL.md](00-master/MAIN-GOAL.md).
2. Read [SURFACE-MAP.md](00-master/SURFACE-MAP.md).
3. Read [OPERATING-RULES.md](02-agent-equipment/OPERATING-RULES.md).
4. Run the preparedness gate from [PREPAREDNESS-CHECK.md](00-master/PREPAREDNESS-CHECK.md).
5. Read [IMPLEMENTATION-STRATEGY.md](05-execution/IMPLEMENTATION-STRATEGY.md).
6. Choose the next batch from [EXECUTION-ORDER.md](05-execution/EXECUTION-ORDER.md).

## Do Not Mutate Yet

Until the registry authority files exist, do not:

- move project directories
- delete archives, caches, or duplicate-looking files
- rewrite MCP configs by hand
- run package upgrades
- run cleanup commands that delete data
- change systemd unit files without an explicit batch and validation plan
- expose secret values from `.env`, credentials, OAuth, token, key, or `settings.local.json` files

## Current Highest-Value Batch

Start with [BATCH-00-ORIENTATION.md](03-batches/BATCH-00-ORIENTATION.md), then proceed to [BATCH-01-KNOWLEDGEBASE-MEMORY.md](03-batches/BATCH-01-KNOWLEDGEBASE-MEMORY.md) and [BATCH-03-MCP-WIRING.md](03-batches/BATCH-03-MCP-WIRING.md).

The **authoritative** full sequence (including `BATCH-04` before `BATCH-02`) is [EXECUTION-ORDER.md](05-execution/EXECUTION-ORDER.md). The two bullets above call out the first high-leverage forks after orientation.

## Completion Proof

Use [FULFILLMENT-MATRIX.md](05-execution/FULFILLMENT-MATRIX.md) to verify that the outcomes requested across the discovery thread are reflected in this handoff pack.

Machine-readable records live in [07-registries/](07-registries/README.md).
