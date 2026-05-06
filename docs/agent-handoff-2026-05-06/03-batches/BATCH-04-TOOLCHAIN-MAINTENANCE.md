# Batch 04 - Toolchain And Maintenance Automation

## Goal

Turn existing maintenance scripts and timers into a governed routine maintenance surface.

## Source Docs To Read First

- `../01-source-maps/development-toolchain-wiring-maintenance-audit.md`
- `../01-source-maps/development-wiring-fix-candidates.json`

## Inputs

- toolchain scan results
- systemd user unit files
- maintenance scripts
- fix candidates beginning with `DEVTOOL-` and `MAINT-`

## Outputs

- maintenance authority design
- toolchain authority design
- timer health checklist
- repair list for broken targets

## Allowed Actions

- validate unit file targets
- classify maintenance scripts
- document schedules and reports
- add non-secret authority records

## Forbidden Actions

- run package upgrades
- run cleanup that deletes data
- edit systemd units without a scoped repair batch
- run `sudo`

## Parallel-Safe Work

- tool availability validation
- unit target existence checks
- script classification
- maintenance schedule mapping

## Acceptance Criteria

- every known timer has an authority record shape
- broken `hogsmade` timer targets are recorded
- legacy Arch maintenance script is classified
- degraded snap toolchain state is documented

## Likely Blockers

- sandbox cannot query live systemd user bus
- `npm` and `npx` PATH mismatch
- snap confinement errors

## Schema Input Example

```json
{
  "job_id": "runtime-health-pass",
  "timer": "/home/irfankabir/.config/systemd/user/runtime-health-pass.timer",
  "service": "/home/irfankabir/.config/systemd/user/runtime-health-pass.service",
  "mode": "read-only",
  "validation": ["unit_file_exists", "execstart_exists"]
}
```

