# Batch 03 - MCP, Editor, And Agent Wiring

## Goal

Define a single MCP and client-profile authority so Cursor, Windsurf, VS Code, Copilot, Zed, Opencode, Codex, Claude Code, Devin, Gemini, and Antigravity have intentional wiring.

## Source Docs To Read First

- `../01-source-maps/development-toolchain-wiring-maintenance-audit.md`
- `../01-source-maps/development-wiring-fix-candidates.json`
- `../01-source-maps/custom-harness-agentic-performance-audit.md`

## Inputs

- canonical 25-server MCP set
- current client MCP configs
- command path and cwd validation results
- fix candidates beginning with `WIRE-`

## Outputs

- MCP authority design
- client profiles
- parity report
- stale path repair list

## Allowed Actions

- parse MCP config metadata
- compare server sets
- validate commands and cwd
- write authority docs and schemas

## Forbidden Actions

- hand-edit every MCP config without an authority file
- expose env values
- remove servers from clients without profile policy
- assume archived caraxes configs are active

## Parallel-Safe Work

- client profile classification
- command path validation
- stale path scan
- server set comparison

## Acceptance Criteria

- canonical server set is declared
- each client is classified as full, minimal, archive, or disabled
- command path policy is explicit
- missing servers are either intentional or repair candidates

## Likely Blockers

- `npx` not on PATH
- current-home and caraxes-side configs differ
- some configs are empty or parser-specific

## Schema Input Example

```json
{
  "id": "WIRE-P0-001",
  "priority": "P0",
  "lane": "wiring",
  "type": "mcp_command_mismatch",
  "affected_paths": [
    "/mnt/arch_data/home/caraxes/CascadeProjects/mcp_config.json"
  ],
  "recommended_fix": {
    "strategy": "Use deterministic npx command resolution"
  }
}
```

