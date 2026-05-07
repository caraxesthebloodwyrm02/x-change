# Toolchain And Maintenance Authority

## Objective

Make routine maintenance governed, scheduled, and safe. This document is the human-readable authority; `07-registries/toolchain-authority.json` and `07-registries/maintenance-authority.json` are the machine-readable inputs for tooling.

## Toolchain Records

Data source: `01-source-maps/development-toolchain-wiring-maintenance-audit.md` (2026-05-06 read-only pass).

### Present And Healthy (24 tools)

| Tool | Path | Version |
|---|---|---|
| `git` | `/usr/bin/git` | 2.51.0 |
| `gh` | `/usr/bin/gh` | 2.46.0 |
| `uv` | `/home/irfankabir/.local/bin/uv` | 0.11.7 |
| `python3` | `/usr/bin/python3` | 3.13.7 |
| `node` | `/home/irfankabir/.local/bin/node` | v24.15.0 (via nvm) |
| `docker` | `/usr/bin/docker` | 29.4.2 |
| `docker compose` | Docker CLI plugin | v5.1.3 |
| `make` | `/usr/bin/make` | 4.4.1 |
| `gcc` / `g++` | `/usr/bin/gcc` | 15.2.0 |
| `sqlite3` | `/usr/bin/sqlite3` | 3.46.1 |
| `redis-server` | `/usr/bin/redis-server` | 8.0.2 |
| `jq` | `/usr/bin/jq` | 1.8.1 |
| `rg` | `/home/irfankabir/.cargo/bin/rg` | 15.1.0 |
| `fd` | `/home/irfankabir/.cargo/bin/fd` | 10.4.2 |
| `bat` | `/home/irfankabir/.cargo/bin/bat` | 0.26.1 |
| `eza` | `/home/irfankabir/.cargo/bin/eza` | 0.23.4 |
| `pytest` | `/home/irfankabir/.local/bin/pytest` | 9.0.3 |
| `playwright` | `/home/irfankabir/.local/bin/playwright` | 1.58.0 |
| `cursor` | `/usr/bin/cursor` | 3.2.21 |
| `windsurf` | `/usr/bin/windsurf` | 1.110.1 |
| `zed` | `/home/irfankabir/.local/bin/zed` | 1.1.5 |
| `opencode` | `/home/irfankabir/.opencode/bin/opencode` | 1.14.39 |
| `claude` | `/home/irfankabir/.local/bin/claude` | 2.1.131 |
| `google-chrome` | `/usr/bin/google-chrome` | 148.0.7778.96 |

### Present But Degraded (5 tools)

| Tool | Path | Failure class | Action |
|---|---|---|---|
| `npm` | `/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npm` (11.13.0) | Missing from PATH for non-interactive agents | DEVTOOL-P0-001 |
| `npx` | `/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npx` (11.13.0) | Missing from PATH for non-interactive agents | DEVTOOL-P0-001 |
| `go` | `/snap/bin/go` | `snap-confine` AppArmor error | DEVTOOL-P1-001 |
| `rustc` / `cargo` | `/snap/bin/rustc`, `/snap/bin/cargo` | `snap-confine` AppArmor error | DEVTOOL-P1-001 |
| `code` (VS Code) | `/snap/bin/code` | `snap-confine` AppArmor error | DEVTOOL-P1-001 |

### Unverified (2 tools)

| Tool | Path | Issue | Action |
|---|---|---|---|
| `ollama` | `/usr/local/bin/ollama` | Client present; daemon health not verified | Check `ollama list` before local model workflows |
| `docker` daemon | `/usr/bin/docker` | Client visible; daemon health not fully verified from sandbox | Check `docker info` outside sandbox |

### Node/NPM Mismatch (DEVTOOL-P0-001)

`node` resolves to `/home/irfankabir/.local/bin/node` (symlink into `/home/irfankabir/.nvm/versions/node/v24.15.0/bin/node`). `npm` and `npx` exist at the nvm path (both report 11.13.0) but are not exposed in `/home/irfankabir/.local/bin` or on non-interactive PATH.

Two repair strategies:
1. **PATH normalization** — add `/home/irfankabir/.nvm/versions/node/v24.15.0/bin` to agent-maintenance PATH used by systemd services, hooks, and MCP configs.
2. **Symlink normalization** — create user-level symlinks `~/.local/bin/npm` and `~/.local/bin/npx` pointing to the nvm binaries.

**Canonical command for TypeScript MCP servers (chosen):**
```
/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npx
```

This is already used by the working Cursor and Windsurf configs. CascadeProjects canonical config still uses bare `npx` (WIRE-P0-001).

## Maintenance Jobs (18 jobs)

Verified 2026-05-07 by reading unit files from `/home/irfankabir/.config/systemd/user/`. Live `systemctl --user` state could not be queried (sandbox restriction); all verification is offline (unit file parsing + ExecStart target existence).

### Healthy (16 jobs — ExecStart target exists)

| ID | Timer | Schedule | ExecStart | Mode |
|---|---|---|---|---|
| `git-hygiene` | `git-hygiene.timer` | Daily 04:00 | `/home/irfankabir/scripts/git-hygiene.sh` | read-only |
| `gruff-diagnostic` | `gruff-diagnostic.timer` | Monday 09:00 | `node ~/gruff/workspace/scripts/route_config_smoke.mjs` | read-only |
| `gruff-ingester` | `gruff-ingester.timer` | Every 1 min | `node ~/gruff/dist/trust/ingester.cjs` | write (trust DB) |
| `integrity-monitor` | `integrity-monitor.timer` | Every 30 min | `/home/irfankabir/scripts/integrity-monitor.sh check` | read-only |
| `network-watchdog` | `network-watchdog.timer` | Every 5 min | `/home/irfankabir/scripts/network-watchdog.sh` | read-only |
| `node-refresh` | `node-refresh.timer` | Sunday 03:30 | `~/.local/bin/node-weekly-refresh.sh` | write (npm cache) |
| `personal-rag-morning-brief` | `personal-rag-morning-brief.timer` | Daily 06:00 Asia/Dhaka | `~/.venv/bin/python ~/personal-rag/scripts/morning-brief.py --no-render` | write (digest) |
| `prince-toolchain-bootstrap` | `prince-toolchain-bootstrap.timer` | Weekly | `/home/irfankabir/scripts/toolchain-change-bootstrap.sh` | write (agent-context) |
| `process-sentinel` | `process-sentinel.timer` | Every 15 min | `/home/irfankabir/scripts/process-sentinel.sh diff` | read-only |
| `runtime-health-pass` | `runtime-health-pass.timer` | Daily 06:15 | `/usr/bin/bash ~/scripts/runtime-health-pass.sh` | read-only |
| `runtime-health-pass-deps` | `runtime-health-pass-deps.timer` | Monday 07:30 | `/usr/bin/bash ~/scripts/runtime-health-pass.sh --deps --quiet` | read-only |
| `stay-current` | `stay-current.timer` | Wednesday 03:00 | `/home/irfankabir/scripts/stay-current.sh --quiet` | read-only |
| `validate-registry` | `validate-registry.timer` | Friday 05:00 | `/home/irfankabir/scripts/validate-registry.sh` | read-only |
| `weekly-security-check` | `weekly-security-check.timer` | Monday 03:00 | `/home/irfankabir/scripts/weekly-security-check.sh --quiet` | read-only |
| `workspace-maintenance-daily` | `workspace-maintenance-daily.timer` | Daily 07:00 | `/home/irfankabir/scripts/workspace-maintenance.sh --daily` | read-only |
| `workspace-maintenance-weekly` | `workspace-maintenance-weekly.timer` | Sunday 07:30 | `/home/irfankabir/scripts/workspace-maintenance.sh --weekly` | read-only |

### Broken (2 jobs — ExecStart target missing)

| ID | Timer | Schedule | ExecStart | Failure |
|---|---|---|---|---|
| `hogsmade-harness` | `hogsmade-harness.timer` | Daily 03:00 | `%h/gruff/workspace/CascadeProjects/scripts/hogsmade-driver.sh` | Target file does not exist (MAINT-P0-001) |
| `hogsmade-scan` | `hogsmade-scan.timer` | Daily 02:00 + 14:00 | `%h/gruff/workspace/CascadeProjects/scripts/hogsmade-driver.sh` | Target file does not exist (MAINT-P0-001) |

### Manual-Only Services (no timer)

| ID | Service | ExecStart | Purpose |
|---|---|---|---|
| `grid-api` | `grid-api.service` | `uv run uvicorn application.mothership.main:app --host 127.0.0.1 --port 8080` | GRID Mothership; started manually or via alias |

## Maintenance Script Classification

| Script | Classification | Replacement | Notes |
|---|---|---|---|
| `stay-current.sh` | **active-ubuntu** | — | Ubuntu 25.10 package/toolchain report; non-privileged |
| `toolchain-maintain.sh` | **legacy-arch** | `stay-current.sh` | Arch Linux maintenance; must not run on Ubuntu without `--force-legacy` (MAINT-P1-001) |
| `runtime-health-pass.sh` | **active** | — | Multi-mode health pass; `--refresh`, `--deps`, `--json`, `--quiet` |
| `workspace-maintenance.sh` | **active** | — | Orchestrator using MCP/headless Claude sessions |
| `git-hygiene.sh` | **active** | — | Fetch/prune/gc only; no branch deletion |
| `weekly-security-check.sh` | **active** | — | apt security + OS posture report |
| `integrity-monitor.sh` | **active** | — | Hash drift monitor for critical configs |
| `network-watchdog.sh` | **active** | — | Outbound connection monitor |
| `process-sentinel.sh` | **active** | — | Process drift detection |
| `mcp-probe.sh` | **active** | — | MCP config health probe |

## Dependency Lockfile Policy

From manifest audit across 173 project directories (337 manifest records):

| Ecosystem | Manifest count | Lockfile gap |
|---|---|---|
| Node | 136 | 52 `package.json` without detected lockfile |
| Python | 99 | 16 `pyproject.toml` without `uv.lock` |
| Docker | 19 | 5 `Dockerfile` without nearby compose file |

**Rule:** Do not auto-generate lockfiles blindly. Classify each package directory first:
- `root-app` / `mcp-server` → lockfile required
- `workspace-package` → lockfile owned by workspace root
- `fixture` / `archive` / `example` → lockfile optional
- `vendored-app` → lockfile policy per upstream

Policy registry target: `DEVTOOL-P1-002`.

## Fix Candidates (11 records)

Source: `01-source-maps/development-wiring-fix-candidates.json`. Sorted by priority.

### P0 (4)

| ID | Lane | Title | Parallel group |
|---|---|---|---|
| `DEVTOOL-P0-001` | toolchain | npm/npx exist in nvm but not on PATH | A |
| `WIRE-P0-001` | wiring | Canonical Cascade MCP config uses bare npx | A |
| `WIRE-P0-002` | wiring | Stale `/home/caraxes` path references in active scripts | B |
| `MAINT-P0-001` | maintenance | hogsmade timers point to missing driver path | C |
| `MAINT-P0-002` | maintenance | No single maintenance authority file governs all timers | C |

### P1 (6)

| ID | Lane | Title | Parallel group |
|---|---|---|---|
| `WIRE-P1-001` | wiring | MCP coverage differs across client configs | D |
| `DEVTOOL-P1-001` | toolchain | snap-backed Go/Rust/Code degraded | E |
| `DEVTOOL-P1-002` | toolchain | Lockfile policy gaps (52 Node + 16 Python) | F |
| `WIRE-P1-002` | wiring | Empty/non-strict JSON client config handling | D |
| `MAINT-P1-001` | maintenance | Arch-era toolchain-maintain.sh overlaps with stay-current.sh | G |
| `MAINT-P2-001` | maintenance | Live timer status requires non-sandbox verification | C |

### P2 (1)

| ID | Lane | Title | Parallel group |
|---|---|---|---|
| `MAINT-P2-001` | maintenance | Live timer status requires non-sandbox verification | C |

## Parallel Work Lanes

| Lane | Scope | Parallel-safe with |
|---|---|---|
| A | Toolchain PATH + MCP command resolution | B, C, F, G |
| B | Stale `/home/caraxes` path drift | A, C, D, F |
| C | Maintenance timers and services | A, B, D, F, G |
| D | Editor/agent client profiles | B, C, E, F |
| E | OS toolchain degraded state (snap) | D, F, G |
| F | Dependency and lockfile policy | A, B, C, D, E |
| G | Legacy script classification | All |

## Recommended Automation Design

### Daily
1. Toolchain PATH health check
2. MCP parity health check
3. `runtime-health-pass`
4. Stale path drift check
5. Maintenance unit offline validation
6. Report freshness check

Outputs: `~/.echoes/toolchain-health-YYYY-MM-DD.ndjson`, `~/.echoes/mcp-parity-YYYY-MM-DD.ndjson`

### Weekly
1. `stay-current` package report
2. Dependency audit
3. Lockfile policy scan
4. `git-hygiene`
5. `weekly-security-check`
6. Agent bootstrap refresh
7. MCP config regeneration dry-run

### Monthly
1. Legacy script review
2. Archive/active path reclassification
3. Old logs/cache report (no auto-delete)
4. Duplicate config report
5. Client profile review

## Maintenance Safety Rules

1. No `sudo` from agents. Collect privileged steps into one copyable block for the operator.
2. No package upgrades from routine report scripts. Report only.
3. No destructive cleanup without operator-approved apply step. Generate cleanup plans with exact paths and size estimates.
4. Separate live systemd checks from offline unit-file validation. Offline validation always safe; live checks require non-sandbox context.
5. Fail closed: if a timer's ExecStart target is missing, mark the job degraded and skip it — do not guess a replacement path.

## Next Implementation Actions

1. Apply MAINT-P0-001: repair or disable the two broken hogsmade timers.
2. Apply DEVTOOL-P0-001: expose npm/npx on agent PATH.
3. Apply WIRE-P0-001: fix bare `npx` in CascadeProjects canonical MCP config.
4. Create `dependency-policy.yaml` from the manifest gap data (DEVTOOL-P1-002).
5. Add offline unit-file validator script.
6. Guard `toolchain-maintain.sh` with OS check (MAINT-P1-001).

The authority is now complete for BATCH-04 acceptance: every timer has a record, broken hogsmade targets are recorded, legacy Arch script is classified, and degraded snap toolchain state is documented.
