# Context Acquisition

## First Read Sequence

1. `README.md`
2. `00-master/MAIN-GOAL.md`
3. `00-master/SURFACE-MAP.md`
4. `00-master/HANDOFF-INVENTORY.md`
5. `02-agent-equipment/OPERATING-RULES.md`
6. `05-execution/EXECUTION-ORDER.md`
7. Selected batch file under `03-batches/`

## Source Map Sequence

For broad context, read in this order:

1. `01-source-maps/portfolio-inventory-benchmark.md`
2. `01-source-maps/domain-landscape-local-asset-allocation.md`
3. `01-source-maps/custom-harness-agentic-performance-audit.md`
4. `01-source-maps/development-toolchain-wiring-maintenance-audit.md`
5. `01-source-maps/development-wiring-fix-candidates.json`
6. `01-source-maps/directory-structure-consolidation-playbook.md`
7. `01-source-maps/buried-assets-resurfacing-inventory.md`

## Workspace Context To Verify

Before implementing, verify:

- current working directory
- git status for the target repo
- whether source docs have moved as expected
- whether `/home/irfankabir/AGENTS.md` and `/home/irfankabir/CLAUDE.md` still match the handoff assumptions
- whether npm/npx PATH mismatch still exists
- whether MCP configs still have the same server set
- whether maintenance unit targets still exist

## Current Known Blockers

- `npm` and `npx` may not be on PATH even though nvm copies exist.
- Some MCP configs use bare `npx`; current-home Cursor/Windsurf use absolute nvm `npx`.
- `hogsmade` timers reference a missing driver path.
- No operational `.rag_db` was found during the audit.
- Snap-backed Go/Rust/Code commands were degraded.

## Evidence Discipline

Use source maps for orientation, then verify with live filesystem or commands before making changes.

