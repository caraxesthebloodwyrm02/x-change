# Custom Asset Registry Seed

## Objective

Surface and govern custom agents, hooks, skills, workflows, commands, subagents, rules, named batches, plugins, and MCP/tool definitions.

## Registry Shape

Each custom asset record should include:

- `id`
- `kind`
- `path`
- `owner`
- `status`
- `attribution`
- `domains`
- `validation`
- `source_map`

## Status Values

Use these values consistently:

- `active`
- `experimental`
- `archive`
- `mirror`
- `vendor`
- `derived`
- `broken`
- `unknown`

## Starter Asset Lanes

| Lane | Source |
|---|---|
| Agents and subagents | `.claude/agents`, `.cursor/agents`, CascadeProjects agents |
| Hooks | `.claude/hooks`, plugin hooks, Cursor hooks |
| Skills | `.claude/skills`, `.codex/skills`, plugin skills, Cursor/Windsurf skills |
| Commands | `.claude/commands`, CascadeProjects commands |
| Rules | `.claude/rules`, `.windsurf/rules`, Cursor rules, AGENTS/CLAUDE files |
| Workflows | `.claude/scheduler`, Windsurf workflows, maintenance routines |
| Plugins | `atlas-echoes`, `caraxes`, marketplace/cache-separated plugin roots |
| Named batches | batch runners, batch config fixtures, maintenance batch records |

## Validation

The first implementation pass should prove:

- active paths exist
- duplicate names are visible
- mirrors are linked to their source
- vendor/cache assets are separated from authored assets
- no secret-bearing files are read

## Next Implementation Action

Create `custom-assets.yaml` from the high-confidence source map, then generate a report grouped by kind and status.

