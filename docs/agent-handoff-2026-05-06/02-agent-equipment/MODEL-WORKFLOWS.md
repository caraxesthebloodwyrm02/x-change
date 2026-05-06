# Model Workflows

## Broad Audit Workflow

Use when validating the whole handoff or re-running inventory.

1. Read master docs.
2. Read relevant source maps.
3. Run read-only filesystem and config probes.
4. Classify findings as confirmed, stale, or unresolved.
5. Update registry or report artifacts only within the selected batch.

## Focused Repair Workflow

Use for a specific fix candidate.

1. Read the candidate from `development-wiring-fix-candidates.json`.
2. Verify all affected paths.
3. Confirm the target authority file or client profile.
4. Apply the smallest repair.
5. Run candidate-specific validation.
6. Record the result.

## Registry Buildout Workflow

Use for memory, custom assets, MCP, maintenance, dependency policy, and path authority.

1. Choose one registry type.
2. Generate an initial registry from existing source maps and live scans.
3. Mark status as active, archive, fixture, derived, mirror, or unknown.
4. Add validation fields.
5. Generate a human-readable report from the registry.

## MCP Parity Workflow

1. Establish canonical server set.
2. Classify client profiles as full, minimal, archive, or disabled.
3. Compare every client config against its profile.
4. Validate command path and cwd.
5. Regenerate derived configs only after the authority file exists.

## Maintenance Automation Workflow

1. Inventory scripts and timers.
2. Build `maintenance-authority.yaml`.
3. Validate unit files offline.
4. Validate live timer state outside sandbox.
5. Add daily, weekly, and monthly report expectations.

