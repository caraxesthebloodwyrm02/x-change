# Execution Order

## Recommended Sequence

1. Read `IMPLEMENTATION-STRATEGY.md`.
2. `BATCH-00-ORIENTATION`
3. `BATCH-01-KNOWLEDGEBASE-MEMORY`
4. `BATCH-03-MCP-WIRING`
5. `BATCH-04-TOOLCHAIN-MAINTENANCE`
6. `BATCH-02-CUSTOM-ASSET-REGISTRY`
7. `BATCH-05-DIRECTORY-CONSOLIDATION`
8. `BATCH-06-DOMAIN-DISTRIBUTION`
9. `BATCH-07-BURIED-ASSET-RESURFACING`
10. Review `FULFILLMENT-MATRIX.md`.

## Why This Order

Orientation comes first because a broken handoff creates bad downstream work.

Memory and MCP wiring come next because they directly affect agent continuity and tool access.

Toolchain and maintenance follow because routine automation depends on reliable paths and commands.

Custom asset registry follows once the agent can retrieve context and see tool wiring.

Directory consolidation, domain distribution, and buried asset resurfacing come after authority layers are in place.

## Stop Conditions

Stop and repair the current batch if:

- source maps are missing
- schemas fail to parse
- a batch requires a policy that is not declared
- a proposed operation would expose secrets
- a proposed operation would delete or move data without rollback
