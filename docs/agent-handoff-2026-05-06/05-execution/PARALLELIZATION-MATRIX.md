# Parallelization Matrix

## Parallel Groups

| Group | Batches | Safe Parallel Work |
|---|---|---|
| A | 00 | schema validation, source presence, link checks |
| B | 01, 02 | memory source inventory and custom asset inventory |
| C | 03, 04 | MCP parity and toolchain health, if no files are edited in the same config set |
| D | 05, 06 | directory classification and domain allocation |
| E | 06, 07 | domain mapping and buried asset candidate verification |

## Avoid Parallel Edits

Do not edit these at the same time from multiple agents:

- MCP configs
- systemd unit files
- root `AGENTS.md` or `CLAUDE.md`
- registry authority files once created
- source map files

## Recommended Multi-Agent Split

If using multiple agents:

- Agent 1: orientation and schemas
- Agent 2: memory and custom asset registries
- Agent 3: MCP and toolchain wiring
- Agent 4: domain and buried asset mapping

Each agent must report changed files and validation output before integration.

