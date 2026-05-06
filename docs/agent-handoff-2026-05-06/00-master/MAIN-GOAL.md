# Main Goal

## Goal

Build a durable agent handoff and execution surface for the local ecosystem rooted at:

- `/home/irfankabir`
- `/mnt/arch_data/home/caraxes`
- `/home/irfankabir/x-change`

The handoff must preserve the discovery work, expose the mapped system clearly, and allow future agents to continue in scoped batches without losing momentum.

## Success Criteria

- A future agent can start at `README.md` and understand the mapped ecosystem without this chat.
- Every source map is isolated in `01-source-maps/`.
- Every execution batch has inputs, outputs, allowed actions, forbidden actions, parallel-safe work, blockers, acceptance criteria, and a schema-shaped example.
- The pack clearly separates facts already discovered from future implementation work.
- The pack narrows the error surface for future agents by providing schemas and acceptance checks.

## Operating Thesis

The ecosystem already contains valuable projects, custom agent definitions, MCP servers, scripts, hooks, workflows, and maintenance timers. The bottleneck is authority and wiring:

- no single registry for custom assets
- no complete persistent-memory authority
- MCP/editor configs are duplicated and partially drifted
- maintenance automation exists but needs one governing manifest
- directory structure needs discipline before broad moves happen

## Final Target State

The next implementation wave should produce an `agent-harness` authority layer with:

- project and asset registry
- MCP authority
- toolchain and maintenance authority
- memory authority
- path-drift checks
- generated reports
- batch-specific execution receipts

