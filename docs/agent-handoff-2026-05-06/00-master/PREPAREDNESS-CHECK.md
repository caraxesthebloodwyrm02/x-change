# Preparedness Check

## Purpose

Use this before executing any implementation batch. The goal is to confirm the handoff pack is complete, the agent understands the constraints, and no obvious roadblock will break momentum.

## Required Passes

| Check | Pass Condition |
|---|---|
| Source maps present | All seven files exist under `01-source-maps/`. |
| Source maps linked | `README.md` links to all seven source maps. |
| Batch docs present | All eight batch docs exist under `03-batches/`. |
| Batch references | Every batch references at least one source map. |
| Acceptance criteria | Every batch has explicit acceptance criteria. |
| Parallelization | Every batch has parallel-safe work notes. |
| Schemas valid | All JSON files under `04-schemas/` parse with `python3 -m json.tool`. |
| Fix candidates valid | `01-source-maps/development-wiring-fix-candidates.json` parses with `python3 -m json.tool`. |
| Authority records present | All five authority seed files exist under `06-authority/`. |
| Registry records present | Every `.json` file under `07-registries/` parses with `python3 -m json.tool` (see `07-registries/README.md` for the canonical list; YAML snapshots may coexist as documentation). |
| Fulfillment matrix present | `05-execution/FULFILLMENT-MATRIX.md` exists and marks every requested outcome. |
| Old references cleared | No old dated source-doc filenames remain in `docs/` except git deletion records. |
| No open placeholders | No uppercase placeholder markers appear in the handoff pack. |
| Secret safety | No secret values are quoted; sensitive files are path-only references. |

## Preparedness Record Shape

Use this shape when recording a check:

```json
{
  "check_id": "handoff-pack-preparedness",
  "status": "pass",
  "timestamp": "2026-05-06T00:00:00+06:00",
  "checked_by": "agent",
  "evidence": [
    "all source maps present",
    "schemas parse",
    "batch docs present"
  ],
  "blockers": []
}
```

## Failure Policy

If any check fails, stop before implementation and repair the handoff pack first. Do not start a downstream batch with a broken handoff.
