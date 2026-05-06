# Batch 02 - Custom Asset Registry

## Goal

Create a registry for agents, hooks, skills, workflows, commands, rules, named batches, plugins, and MCP tool surfaces.

## Source Docs To Read First

- `../01-source-maps/custom-harness-agentic-performance-audit.md`
- `../01-source-maps/development-toolchain-wiring-maintenance-audit.md`

## Inputs

- high-confidence custom asset counts
- custom definition roots
- plugin roots
- hooks and scheduler directories

## Outputs

- custom asset registry records
- duplicate and mirror classification
- active/archive/vendor status
- validation report

## Allowed Actions

- scan asset paths
- create registry docs or schemas
- classify assets
- add generated reports if scoped to the batch

## Forbidden Actions

- delete duplicate-looking assets
- merge plugins by hand
- rewrite hooks before registry ownership exists
- expose secret-bearing config values

## Parallel-Safe Work

- agent inventory
- skill inventory
- hook inventory
- plugin inventory
- command inventory

## Acceptance Criteria

- every high-confidence asset class has a registry representation
- status values are normalized
- duplicate names are visible
- active vs archive vs vendor is explicit

## Likely Blockers

- duplicated assets across `/home/irfankabir` and `/mnt/arch_data/home/caraxes`
- marketplace and cache assets mixed with authored assets
- missing version metadata

## Schema Input Example

```json
{
  "id": "claude.agent.workspace-auditor",
  "kind": "agent",
  "path": "/home/irfankabir/.claude/agents/workspace-auditor.md",
  "owner": "claude-home",
  "status": "active",
  "attribution": "built-by-prince"
}
```

