# Toolchain And Maintenance Authority

## Objective

Make routine maintenance governed, scheduled, and safe.

## Toolchain Records

| Tool Area | Current State | Required Policy |
|---|---|---|
| Python | `python3` and `uv` present | use `uv` for Python project work |
| Node | `node` present, `npm` and `npx` missing from PATH | expose npm/npx through controlled PATH or user symlinks |
| Docker | `docker` and `docker compose` present | use `docker compose`, not standalone `docker-compose` |
| Go/Rust/Code | snap-backed commands degraded | classify as environment degraded until repaired |
| Ollama | client present, daemon not verified | health check before local model workflows |

## Maintenance Jobs

| Job | Status | Policy |
|---|---|---|
| `runtime-health-pass` | target exists | daily read-only health report |
| `stay-current` | target exists | weekly package/toolchain report, no upgrades |
| `weekly-security-check` | target exists | weekly non-privileged security report |
| `git-hygiene` | target exists | fetch/prune/gc only as configured, no branch deletion |
| `integrity-monitor` | target exists | config drift reporting |
| `network-watchdog` | target exists | outbound connection reporting |
| `process-sentinel` | target exists | process drift reporting |
| `hogsmade-harness` | target missing in audit | repair or disable before relying on timer |
| `hogsmade-scan` | target missing in audit | repair or disable before relying on timer |

## Maintenance Safety

- No `sudo` from agents.
- No package upgrades from routine report scripts.
- No destructive cleanup without operator-approved apply step.
- Live systemd checks must be separated from offline unit-file validation.

## Next Implementation Action

Create `maintenance-authority.yaml` and `toolchain-authority.yaml`, then add an offline validation report before changing any unit files.

