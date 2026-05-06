# Batch 01 - Knowledgebase And Persistent Memory

## Goal

Build the foundation that lets agents carry usable context across sessions.

## Source Docs To Read First

- `../01-source-maps/custom-harness-agentic-performance-audit.md`
- `../01-source-maps/development-toolchain-wiring-maintenance-audit.md`
- `../01-source-maps/portfolio-inventory-benchmark.md`

## Inputs

- `.claude/knowledge` paths
- `.codex/memories` paths
- session logs and decisions
- project registry references

## Outputs

- memory authority design
- source list
- ingestion policy
- retrieval and stale-context rules
- validation checklist

## Allowed Actions

- inventory memory files
- define registry schemas
- add docs and non-secret manifests
- validate expected paths

## Forbidden Actions

- expose private memory contents if sensitive
- delete old memory
- silently rewrite historical context
- build vector stores before path authority is chosen

## Parallel-Safe Work

- source inventory
- stale path scan
- session handoff format design
- retrieval acceptance criteria

## Acceptance Criteria

- canonical memory roots are named
- stale `/home/caraxes` memory paths are classified
- session-start and session-end expectations are documented
- retrieval validation has an explicit pass/fail shape

## Likely Blockers

- no `.rag_db` found in expected locations during audit
- multiple memory systems with different formats
- stale scheduler paths

## Schema Input Example

```json
{
  "asset_id": "memory.authority.local",
  "kind": "memory-source",
  "path": "/home/irfankabir/.claude/knowledge",
  "status": "active",
  "validation": {
    "exists": true,
    "stale_path_scan": "required"
  }
}
```

