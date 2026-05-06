# Batch 05 - Directory Consolidation

## Goal

Move from scattered roots and mixed archives toward structural discipline without breaking paths.

## Source Docs To Read First

- `../01-source-maps/directory-structure-consolidation-playbook.md`
- `../01-source-maps/portfolio-inventory-benchmark.md`
- `../01-source-maps/development-toolchain-wiring-maintenance-audit.md`

## Inputs

- target taxonomy
- current root map
- symlink and archive status
- path authority assumptions

## Outputs

- directory authority plan
- move candidates
- archive policy
- no-break validation checklist

## Allowed Actions

- inventory paths
- classify roots
- propose move plans
- add registry records

## Forbidden Actions

- move directories before path authority exists
- rewrite symlinks without validation
- delete archives
- mutate project structure without explicit migration steps

## Parallel-Safe Work

- archive classification
- symlink validation
- root map updates
- project authority records

## Acceptance Criteria

- active roots and archived roots are separated in documentation
- every proposed move has source, destination, references, and rollback note
- no move is recommended without path-impact analysis

## Likely Blockers

- duplicated roots across current and preserved homes
- symlink assumptions
- stale scripts referencing older paths

## Schema Input Example

```json
{
  "path": "/home/irfankabir/CascadeProjects",
  "classification": "active-root",
  "authority": "workspace",
  "move_allowed": false,
  "reason": "requires path registry first"
}
```

