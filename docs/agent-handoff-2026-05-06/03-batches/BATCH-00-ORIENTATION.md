# Batch 00 - Orientation And Preparedness

## Goal

Confirm the handoff pack is structurally complete and ready for downstream execution.

## Source Docs To Read First

- `../00-master/MAIN-GOAL.md`
- `../00-master/SURFACE-MAP.md`
- `../00-master/PREPAREDNESS-CHECK.md`
- `../01-source-maps/portfolio-inventory-benchmark.md` (representative of the seven maps under `../01-source-maps/`; see pack `README.md` for the full list)

## Inputs

- handoff directory
- source maps
- schema files
- current git status

## Outputs

- preparedness result
- list of blocked or ready batches
- recommended next batch

## Allowed Actions

- read files
- run validation commands
- repair broken links inside the handoff pack
- update handoff docs if structural gaps are found

## Forbidden Actions

- project directory moves
- MCP config rewrites
- package upgrades
- cleanup or delete operations

## Parallel-Safe Work

- schema validation
- link checks
- source map presence checks
- old filename reference search

## Acceptance Criteria

- all source maps are present
- all schemas parse
- all batch docs exist
- `README.md` gives a complete entrypoint
- no uppercase placeholder markers remain

## Likely Blockers

- stale links from moved source docs
- schema parse errors
- missing batch acceptance criteria

## Schema Input Example

```json
{
  "batch_id": "BATCH-00",
  "status": "ready",
  "inputs": ["README.md", "00-master/PREPAREDNESS-CHECK.md"],
  "outputs": ["preparedness result"],
  "blockers": []
}
```
