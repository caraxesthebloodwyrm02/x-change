# Authority Layer

## Purpose

This directory converts the handoff source maps into seed authority records. These records are not external repairs yet. They define what future agents must build or validate before touching configs, moving directories, or running maintenance automation.

## Files

| File | Role |
|---|---|
| `MEMORY-AUTHORITY.md` | Persistent memory roots, session handoff, stale-context policy. |
| `MCP-WIRING-AUTHORITY.md` | Canonical MCP server set, client profiles, command policy, parity checks. |
| `TOOLCHAIN-MAINTENANCE-AUTHORITY.md` | Development tools, degraded states, timers, maintenance jobs. |
| `CUSTOM-ASSET-REGISTRY-SEED.md` | Agents, hooks, skills, commands, workflows, plugins, rules, and batches. |
| `DIRECTORY-DOMAIN-RESURFACING-AUTHORITY.md` | Directory discipline, domain allocation, and buried asset promotion rules. |

## Rule

Future implementation should update these authority records first, then use them to generate reports or controlled repairs.

