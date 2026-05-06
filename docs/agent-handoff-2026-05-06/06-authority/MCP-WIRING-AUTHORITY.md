# MCP Wiring Authority

## Objective

Stop editor and agent wiring drift by defining the canonical MCP server set, client profiles, command path policy, and parity checks.

## Canonical Server Set

The audited canonical set contains 25 servers:

`afloat-server`, `code-analysis`, `craft-server`, `echoes-server`, `eligibility-server`, `glass-server`, `glimpse-server`, `grid-enhanced-tools`, `grid-intelligence`, `grid-rag`, `grid-rag-enhanced`, `grid-server`, `harness-server`, `lots-server`, `maintain-server`, `mangrove-server`, `nexus-server`, `ori-server`, `overview-server`, `personal-rag`, `portfolio-safety-lens`, `pulse-server`, `school-server`, `seeds-server`, `test-runner`.

## Client Profiles

| Client | Current Read | Intended Profile |
|---|---|---|
| Cursor current home | full 25-server set, absolute nvm `npx` | full |
| Windsurf current home | full 25-server set, absolute nvm `npx` | full |
| CascadeProjects canonical config | full 25-server set, bare `npx` | full, needs command policy repair |
| Copilot | 5-server subset | minimal unless explicitly promoted |
| generic `.mcp` | 1-server subset | minimal or disabled |
| Antigravity current home | empty MCP config found | disabled or regenerate from profile |
| caraxes-side user configs | partial 19-21 server sets | archive unless confirmed active |

## Command Policy

Preferred deterministic command for TypeScript MCP servers:

`/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npx`

The alternative is a controlled agent PATH that exposes `npm` and `npx`. Do not mix policies without recording the client profile.

## Parity Validation

Each client profile must validate:

- server count matches profile
- command path exists
- cwd exists after variable expansion
- stale `/home/caraxes` active paths are absent
- env key names are listed without values

## Next Implementation Action

Create `mcp-authority.yaml`, classify each client profile, then regenerate or repair only derived configs.

