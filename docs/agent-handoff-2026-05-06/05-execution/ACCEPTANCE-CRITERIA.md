# Acceptance Criteria

## Whole Pack

- `README.md` is the clear entrypoint.
- `00-master/` explains goal, surface, inventory, and preparedness.
- `01-source-maps/` contains the seven moved source docs.
- `02-agent-equipment/` contains prompt, rules, acquisition, workflows, and skills.
- `03-batches/` contains eight executable batch scopes.
- `04-schemas/` contains valid JSON schemas.
- `05-execution/` contains order, parallelization, and acceptance criteria.
- `06-authority/` contains seed authority records for the implementation waves.
- `07-registries/` contains machine-readable implementation records.

## Source Integrity

- Source maps are moved, not duplicated.
- Old dated source filenames are not referenced by active docs.
- Moved source maps remain non-empty.
- The fix-candidate JSON remains valid.

## Execution Readiness

- Every batch has source docs, inputs, outputs, allowed actions, forbidden actions, parallel-safe work, acceptance criteria, likely blockers, and an example.
- Every staged objective has a completion gate and verification gate in `IMPLEMENTATION-STRATEGY.md`.
- The final requested outcomes are checked in `FULFILLMENT-MATRIX.md`.
- Machine-readable fulfillment and preparedness records exist in `07-registries/`.
- Future agents can identify the next action without asking for orientation.
- No batch requires secret values.
- No batch requires destructive action as its first step.

## Preparedness

The pack is ready when:

- schema validation passes
- source file count matches expected inventory
- placeholder scan is clean
- `README.md`, `EXECUTION-ORDER.md`, and `PREPAREDNESS-CHECK.md` agree on first move
