# Development Toolchain, Wiring, And Maintenance Audit - 2026-05-06

## Purpose

This is the final inventory pass for the development operating layer. It maps:

- development programs and package managers
- active project manifests and lockfiles
- editor/agent/MCP wiring
- hooks, scripts, and scheduled maintenance
- gaps, mismatches, overlaps, and routine automation candidates

The goal is not a one-time cleanup. The target state is a maintained system where routine checks fire automatically, report clearly, and narrow the fix surface for future agents.

This pass was read-only. It did not upgrade packages, prune files, start/stop services, edit systemd units, or read secret values.

## Scope

Homes scanned:

- `/home/irfankabir`
- `/mnt/arch_data/home/caraxes`

Active project roots used for development manifest analysis:

- `/home/irfankabir/x-change`
- `/home/irfankabir/gruff/workspace`
- `/home/irfankabir/CascadeProjects`
- `/mnt/arch_data/home/caraxes/CascadeProjects`
- `/home/irfankabir/canopy`
- `/mnt/arch_data/home/caraxes/canopy`
- `/home/irfankabir/roots`
- `/mnt/arch_data/home/caraxes/roots`
- `/home/irfankabir/constrained-signal-pipeline`
- `/home/irfankabir/personal-rag`
- `/home/irfankabir/workspace-trust-auditor`
- `/home/irfankabir/hogsmade`

Secret policy:

- `.env`, `settings.local.json`, token, credential, OAuth, private key, and similar files were not read.
- MCP and settings scans recorded server names, command paths, cwd existence, and env key names only.
- No secret values are included in this report.

## Executive Summary

The ecosystem already has serious maintenance infrastructure: systemd user timers, runtime health scripts, security checks, git hygiene, Node refresh, registry validation, workspace maintenance, MCP probes, and agent bootstrap generation.

The core problem is not absence. The core problem is **wiring authority**.

The strongest blockers found:

1. `node` is available, but `npm`, `npx`, and `corepack` are not on PATH for non-interactive agents.
2. MCP configs disagree on whether to use bare `npx` or an absolute nvm `npx`.
3. Current `/home/irfankabir` Cursor and Windsurf MCP configs are healthy and complete, but several caraxes-side and generic configs are partial or stale.
4. Two systemd user timers point to a missing `hogsmade-driver.sh` path.
5. Snap-backed `go`, `rustc`, `cargo`, and `code` fail with `snap-confine`/AppArmor errors.
6. Active project scan found lockfile policy gaps: 52 Node package dirs without detected lockfiles and 16 Python pyproject dirs without detected lockfiles.
7. A legacy Arch-oriented maintenance script overlaps with Ubuntu 25.10 maintenance scripts.
8. Live systemd timer status could not be checked from the sandbox, so automation presence was verified by unit files, not runtime state.

The fix should be a small maintenance authority layer, not a broad manual rewrite.

## Development Toolchain Surface

### Present And Healthy

| Tool | Path | Version/Status |
|---|---|---|
| `git` | `/usr/bin/git` | 2.51.0 |
| `gh` | `/usr/bin/gh` | 2.46.0 |
| `uv` | `/home/irfankabir/.local/bin/uv` | 0.11.7 |
| `python3` | `/usr/bin/python3` | 3.13.7 |
| `pip`, `pip3` | `/usr/bin/pip`, `/usr/bin/pip3` | 25.1.1 |
| `node` | `/home/irfankabir/.local/bin/node` | v24.15.0 |
| `docker` | `/usr/bin/docker` | 29.4.2 client |
| `docker compose` | Docker CLI plugin | v5.1.3 |
| `make` | `/usr/bin/make` | 4.4.1 |
| `gcc`, `g++` | `/usr/bin/gcc`, `/usr/bin/g++` | 15.2.0 |
| `sqlite3` | `/usr/bin/sqlite3` | 3.46.1 |
| `redis-server`, `redis-cli` | `/usr/bin/*` | 8.0.2 |
| `jq` | `/usr/bin/jq` | 1.8.1 |
| `rg` | `/home/irfankabir/.cargo/bin/rg` | ripgrep 15.1.0 |
| `fd` | `/home/irfankabir/.cargo/bin/fd` | 10.4.2 |
| `bat` | `/home/irfankabir/.cargo/bin/bat` | 0.26.1 |
| `eza` | `/home/irfankabir/.cargo/bin/eza` | 0.23.4 |
| `pytest` | `/home/irfankabir/.local/bin/pytest` | 9.0.3 |
| `playwright` | `/home/irfankabir/.local/bin/playwright` | 1.58.0 |
| `cursor` | `/usr/bin/cursor` | 3.2.21 |
| `windsurf` | `/usr/bin/windsurf` | 1.110.1 |
| `zed` | `/home/irfankabir/.local/bin/zed` | 1.1.5 |
| `opencode` | `/home/irfankabir/.opencode/bin/opencode` | 1.14.39 |
| `codex` | VS Code extension binary | 0.128.0-alpha.1 |
| `claude` | `/home/irfankabir/.local/bin/claude` | 2.1.131 |
| `devin` | `/home/irfankabir/.local/bin/devin` | 2026.5.5-0 |
| `antigravity` | `/usr/bin/antigravity` | 1.107.0 |
| `google-chrome` | `/usr/bin/google-chrome` | 148.0.7778.96 |

### Present But Degraded

| Tool | Path | Failure |
|---|---|---|
| `cargo` | `/snap/bin/cargo` | `snap-confine` AppArmor confinement error |
| `rustc` | `/snap/bin/rustc` | `snap-confine` AppArmor confinement error |
| `go` | `/snap/bin/go` | `snap-confine` AppArmor confinement error |
| `code` | `/snap/bin/code` | `snap-confine` AppArmor confinement error |
| `ollama` | `/usr/local/bin/ollama` | client works; daemon/list access failed in sandbox |
| `docker info` | `/usr/bin/docker` | client visible; daemon health not fully verified from sandbox |
| `snap list` | `/snap/bin/snap` | timed out in sandbox |
| `systemctl --user` | `/usr/bin/systemctl` | user bus unavailable in sandbox |

### Missing From PATH

These were not found on PATH:

- `python`
- `npm`
- `npx`
- `corepack`
- `pnpm`
- `yarn`
- `bun`
- `deno`
- `docker-compose` as a standalone binary
- `just`
- `cmake`
- `clang`
- `psql`
- `yq`
- `fzf`
- `ruff`
- `mypy`
- `chromium`

Important nuance: `docker compose` is available even though standalone `docker-compose` is not.

### Node/NPM Mismatch

`node` resolves to:

`/home/irfankabir/.local/bin/node`

That is a symlink into:

`/home/irfankabir/.nvm/versions/node/v24.15.0/bin/node`

But `npm` and `npx` are not exposed in `/home/irfankabir/.local/bin`.

They do exist here:

- `/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npm`
- `/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npx`

Both report `11.13.0`.

This is the most important development-tooling mismatch because CascadeProjects MCP servers and local project instructions depend on npm/npx.

Recommended repair:

1. Decide whether agents should use PATH normalization or explicit absolute command paths.
2. If PATH normalization: ensure non-interactive shells and systemd services include `/home/irfankabir/.nvm/versions/node/v24.15.0/bin`.
3. If symlink normalization: add user-level symlinks for `npm` and `npx` under `/home/irfankabir/.local/bin`.
4. Re-run:
   - `command -v npm`
   - `command -v npx`
   - `npm --version`
   - `npx --version`
   - MCP parity check

## Active Project Manifest Audit

The active-root scan found:

- 337 manifest records
- 173 project directories

### Manifest Counts

| File | Count |
|---|---:|
| `package.json` | 94 |
| `pyproject.toml` | 45 |
| `package-lock.json` | 42 |
| `uv.lock` | 28 |
| `.pre-commit-config.yaml` | 26 |
| `.github/workflows` | 25 |
| `Makefile` | 24 |
| `requirements.txt` | 21 |
| `Dockerfile` | 10 |
| `docker-compose.yml` | 9 |
| `setup.py` | 4 |
| `requirements-dev.txt` | 4 |
| `Cargo.toml` | 1 |
| `Cargo.lock` | 1 |
| `go.mod` | 1 |
| `go.sum` | 1 |
| `poetry.lock` | 1 |

### Ecosystem Counts

| Ecosystem | Manifest Records |
|---|---:|
| Node | 136 |
| Python | 99 |
| Git/CI/local task files | 75 |
| Docker | 19 |
| Rust | 2 |
| Go | 2 |

### Detected Manifest Gaps

| Gap | Count | Interpretation |
|---|---:|---|
| `node-no-lockfile` | 52 | `package.json` found without detected npm/pnpm/yarn/bun lockfile nearby. |
| `python-no-lockfile` | 16 | `pyproject.toml` found without `uv.lock` or `poetry.lock`. |
| `dockerfile-without-compose` | 5 | `Dockerfile` found without a nearby compose file. |

Do not auto-generate lockfiles blindly. Some package dirs may be workspace packages, examples, archived mirrors, or fixture directories. The fix is a policy registry first:

```yaml
dependency_policy:
  - path: /home/irfankabir/CascadeProjects/Tools/MCPServers/echoes-server
    ecosystem: node
    classification: mcp-server
    install_policy: npm
    lockfile_required: true
    lockfile_owner: local-package
    exception: null
```

Then agents can safely decide which gaps are real and which are intentional.

## Wiring Surface

The wiring scan found 46,464 wiring/config-like records across both homes.

| Tool/Area | Records |
|---|---:|
| Project/general | 20,061 |
| Codex | 5,559 |
| Windsurf | 5,163 |
| VS Code | 5,152 |
| Cursor | 4,767 |
| Claude | 3,299 |
| Antigravity | 1,721 |
| Copilot | 545 |
| Gemini | 71 |
| Zed | 69 |
| Opencode | 53 |
| Devin | 4 |

| Kind | Records |
|---|---:|
| Config | 27,314 |
| Agent | 6,977 |
| Skill | 5,720 |
| MCP | 5,178 |
| Hook | 658 |
| Command | 500 |
| Rule | 117 |

Sensitive-looking wiring records: 312. These were not read.

## MCP Wiring Parity

The canonical current MCP set contains 25 servers:

- `afloat-server`
- `code-analysis`
- `craft-server`
- `echoes-server`
- `eligibility-server`
- `glass-server`
- `glimpse-server`
- `grid-enhanced-tools`
- `grid-intelligence`
- `grid-rag`
- `grid-rag-enhanced`
- `grid-server`
- `harness-server`
- `lots-server`
- `maintain-server`
- `mangrove-server`
- `nexus-server`
- `ori-server`
- `overview-server`
- `personal-rag`
- `portfolio-safety-lens`
- `pulse-server`
- `school-server`
- `seeds-server`
- `test-runner`

### Config Coverage

| Config | Servers | Notes |
|---|---:|---|
| `/mnt/arch_data/home/caraxes/CascadeProjects/mcp_config.json` | 25 | Full set, but TS servers use bare `npx`, which is missing on PATH. |
| `/home/irfankabir/.cursor/mcp.json` | 25 | Full set; uses absolute nvm `npx`; command paths validate. |
| `/home/irfankabir/.codeium/windsurf/mcp_config.json` | 25 | Full set; uses absolute nvm `npx`; command paths validate. |
| `/home/irfankabir/hogsmade/mcp_config.example.json` | 25 | Example full set, but many cwd/command paths do not validate in current location. |
| `/mnt/arch_data/home/caraxes/CascadeProjects/.cursor/mcp.json` | 21 | Missing `craft-server`, `glimpse-server`, `mangrove-server`, `personal-rag`. |
| `/mnt/arch_data/home/caraxes/CascadeProjects/.vscode/mcp.json` | 20 | Missing `craft-server`, `glass-server`, `glimpse-server`, `mangrove-server`, `personal-rag`. |
| `/mnt/arch_data/home/caraxes/.config/Cursor/User/mcp.json` | 21 | Missing `glass-server`, `nexus-server`, `personal-rag`, `school-server`; path/cwd issues. |
| `/mnt/arch_data/home/caraxes/.config/Code/User/mcp.json` | 21 | Same partial coverage pattern. |
| `/mnt/arch_data/home/caraxes/.config/Windsurf/User/mcp.json` | 21 | Same partial coverage pattern. |
| `/mnt/arch_data/home/caraxes/.gemini/antigravity/mcp_config.json` | 19 | Missing several local servers; has extra `github-mcp-server`. |
| `/home/irfankabir/.copilot/mcp-config.json` | 5 | Minimal set; bare `npx` path mismatch. |
| `/home/irfankabir/.mcp.json` | 1 | Only `glimpse-server`; bare `npx` path mismatch. |
| `/home/irfankabir/.gemini/antigravity/mcp_config.json` | 0 bytes | Empty active-home Antigravity MCP config. |

### MCP Interpretation

The full, working current-home MCP wiring appears to be:

- `/home/irfankabir/.cursor/mcp.json`
- `/home/irfankabir/.codeium/windsurf/mcp_config.json`

The canonical source according to root documentation is:

- `/mnt/arch_data/home/caraxes/CascadeProjects/mcp_config.json`

But that source uses bare `npx`, while the working current-home client configs use:

`/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npx`

This is a classic source-of-truth drift:

- canonical config has complete server list
- derived/current configs have better command resolution
- some client configs are partial
- old caraxes-side paths still exist

Recommended repair:

1. Create `agent-harness/registry/mcp-authority.yaml`.
2. Store the canonical 25-server set there.
3. Add per-client profiles:
   - `full`
   - `minimal`
   - `archive`
   - `disabled`
4. Generate all client configs from the authority file.
5. Validate:
   - server set parity
   - command existence
   - cwd existence
   - no stale active `/home/caraxes` paths
   - env key names only, not values

## Editor And Agent Wiring

### Cursor

Current-home Cursor settings exist at:

- `/home/irfankabir/.config/Cursor/User/settings.json`
- `/home/irfankabir/.cursor/mcp.json`
- `/home/irfankabir/.cursor/hooks.json`
- `/home/irfankabir/.cursor/rules`
- `/home/irfankabir/.cursor/agents`
- `/home/irfankabir/.cursor/skills*`

Cursor MCP is currently one of the best-wired surfaces: full 25-server MCP set with absolute npx paths.

### Windsurf

Current-home Windsurf settings exist at:

- `/home/irfankabir/.config/Windsurf/User/settings.json`
- `/home/irfankabir/.codeium/windsurf/mcp_config.json`
- `/home/irfankabir/.windsurf/rules`
- `/home/irfankabir/.windsurf/workflows`

Windsurf MCP is also strong: full 25-server set with absolute npx paths.

### VS Code And Copilot

Relevant settings:

- `/home/irfankabir/.config/Code/User/settings.json`
- `/home/irfankabir/.copilot/mcp-config.json`
- `/mnt/arch_data/home/caraxes/.config/Code/User/mcp.json`

VS Code settings include many Copilot/agent toggles, hook references, and Claude Code preferences. Copilot MCP is intentionally or accidentally minimal: 5 servers only, all using bare `npx` in the audited file.

Decision needed:

- If Copilot is supposed to be minimal, mark that as intentional in `mcp-authority.yaml`.
- If Copilot should be a full agent client, regenerate its MCP config from the 25-server profile.

### Zed

Relevant settings:

- `/home/irfankabir/.config/zed/settings.json`
- `/mnt/arch_data/home/caraxes/.config/zed/settings.json`

Python strict JSON parsing failed on `/home/irfankabir/.config/zed/settings.json`; this may be valid JSONC rather than broken config. Do not classify it as invalid until checked with the correct Zed parser. The registry should record `parser: jsonc`.

### Opencode

Relevant settings:

- `/mnt/arch_data/home/caraxes/.config/opencode/config.json`
- `/mnt/arch_data/home/caraxes/.opencode/config.json`
- `/home/irfankabir/.opencode/bin/opencode`

Opencode is installed and functional. Its config should be included in the cross-agent wiring map, but this audit did not find a current-home `.config/opencode/config.json`.

### Claude Code And Codex

Relevant surfaces:

- `/home/irfankabir/.claude/settings.json`
- `/home/irfankabir/.claude/settings.local.json`
- `/home/irfankabir/.claude/hooks`
- `/home/irfankabir/.claude/commands`
- `/home/irfankabir/.claude/skills`
- `/home/irfankabir/.claude/scheduler`
- `/home/irfankabir/.codex/config.toml`
- `/home/irfankabir/.codex/AGENTS.md`
- `/home/irfankabir/.codex/memories`

These are already rich surfaces. The missing piece is a generated cross-tool map that tells each coding tool which agent assets and MCP servers it owns, derives, mirrors, or ignores.

### Devin, Gemini, Antigravity

Relevant surfaces:

- `/home/irfankabir/.config/devin/config.json`
- `/home/irfankabir/.gemini/settings.json`
- `/home/irfankabir/.gemini/antigravity/mcp_config.json`
- `/home/irfankabir/.config/Antigravity/User/settings.json`
- `/mnt/arch_data/home/caraxes/.gemini/antigravity/mcp_config.json`

Current-home Antigravity MCP config is empty. Caraxes-side Antigravity MCP config has content and 19 server refs. This should be resolved by client profile:

```yaml
client_profiles:
  antigravity:
    status: active
    mcp_profile: full_or_minimal
    config_path: /home/irfankabir/.gemini/antigravity/mcp_config.json
```

## Maintenance Automation Surface

The audit found a substantial existing maintenance department under:

- `/home/irfankabir/scripts`
- `/home/irfankabir/.config/systemd/user`
- `/home/irfankabir/.claude/scheduler`
- `/home/irfankabir/.claude/workspace-maintenance-config.json`

### Existing User Timers And Services

Live `systemctl --user` state could not be queried from this sandbox, but unit files exist.

| Job | Schedule | Exec Target | Status From File Check |
|---|---|---|---|
| `git-hygiene` | daily 04:00 | `/home/irfankabir/scripts/git-hygiene.sh` | target exists |
| `integrity-monitor` | every 30 min | `/home/irfankabir/scripts/integrity-monitor.sh check` | target exists |
| `network-watchdog` | every 5 min | `/home/irfankabir/scripts/network-watchdog.sh` | target exists |
| `node-refresh` | Sunday 03:30 | `/home/irfankabir/.local/bin/node-weekly-refresh.sh` | target exists |
| `prince-toolchain-bootstrap` | weekly | `/home/irfankabir/scripts/toolchain-change-bootstrap.sh` | target exists |
| `runtime-health-pass` | daily 06:15 | `/home/irfankabir/scripts/runtime-health-pass.sh` | target exists |
| `runtime-health-pass-deps` | Monday 07:30 | `/home/irfankabir/scripts/runtime-health-pass.sh --deps --quiet` | target exists |
| `stay-current` | Wednesday 03:00 | `/home/irfankabir/scripts/stay-current.sh --quiet` | target exists |
| `validate-registry` | Friday 05:00 | `/home/irfankabir/scripts/validate-registry.sh` | target exists |
| `weekly-security-check` | Monday 03:00 | `/home/irfankabir/scripts/weekly-security-check.sh --quiet` | target exists |
| `workspace-maintenance-daily` | daily 07:00 | `/home/irfankabir/scripts/workspace-maintenance.sh --daily` | target exists |
| `workspace-maintenance-weekly` | Sunday 07:30 | `/home/irfankabir/scripts/workspace-maintenance.sh --weekly` | target exists |
| `personal-rag-morning-brief` | daily 06:00 Asia/Dhaka | `/home/irfankabir/personal-rag/scripts/morning-brief.py` | target exists |
| `gruff-diagnostic` | Monday 09:00 | `/home/irfankabir/gruff/workspace/scripts/route_config_smoke.mjs` | target exists |
| `gruff-ingester` | every 1 min after boot | `/home/irfankabir/gruff/dist/trust/ingester.cjs` | target exists |
| `hogsmade-harness` | daily 03:00 | `%h/gruff/workspace/CascadeProjects/scripts/hogsmade-driver.sh` | target missing |
| `hogsmade-scan` | daily 02:00 and 14:00 | `%h/gruff/workspace/CascadeProjects/scripts/hogsmade-driver.sh` | target missing |

### Maintenance Scripts Of Interest

| Script | Role |
|---|---|
| `/home/irfankabir/scripts/stay-current.sh` | Ubuntu 25.10 package/toolchain report; non-privileged; emits upgrade commands instead of running them. |
| `/home/irfankabir/scripts/runtime-health-pass.sh` | Runtime config/service/freshness pass; supports `--refresh`, `--deps`, `--json`, `--quiet`. |
| `/home/irfankabir/scripts/mcp-probe.sh` | MCP config health probe: paths, GRID API, transport, manifest drift. |
| `/home/irfankabir/scripts/workspace-maintenance.sh` | Maintenance orchestrator using MCP/headless Claude sessions and audit log output. |
| `/home/irfankabir/scripts/git-hygiene.sh` | Fetch/prune/gc across registered repos; no delete behavior by default. |
| `/home/irfankabir/scripts/weekly-security-check.sh` | apt security and OS posture report. |
| `/home/irfankabir/scripts/integrity-monitor.sh` | Hash drift monitor for critical configs and MCP server entrypoints. |
| `/home/irfankabir/scripts/network-watchdog.sh` | Outbound connection monitor. |
| `/home/irfankabir/scripts/process-sentinel.sh` | Detect unexpected processes against baseline. |
| `/home/irfankabir/scripts/prince-agent-bootstrap.py` | Agent onboarding/profile/context artifacts. |
| `/home/irfankabir/scripts/toolchain-maintain.sh` | Legacy Arch Linux maintenance script; overlaps with Ubuntu-era `stay-current.sh`. |

## Maintenance Authority Target State

Create:

`agent-harness/registry/maintenance-authority.yaml`

Minimum schema:

```yaml
jobs:
  - id: runtime-health-pass
    class: health
    timer: /home/irfankabir/.config/systemd/user/runtime-health-pass.timer
    service: /home/irfankabir/.config/systemd/user/runtime-health-pass.service
    schedule: "*-*-* 06:15:00"
    mode: read-only
    exec: /usr/bin/bash /home/irfankabir/scripts/runtime-health-pass.sh
    report_paths:
      - /home/irfankabir/.echoes
    checks:
      - unit_file_exists
      - execstart_exists
      - live_timer_state
      - last_report_fresh
    repair_policy: report-only
```

Add a generator that outputs:

- `reports/maintenance-schedule.md`
- `reports/toolchain-health.md`
- `reports/mcp-parity.md`
- `reports/stale-paths.md`
- `reports/dependency-policy.md`

## Parallel Work Lanes

This is how a future agent should split the work without collisions.

### Lane A - Toolchain PATH And MCP Command Resolution

Scope:

- npm/npx/corepack path
- MCP command form
- non-interactive PATH for agents and systemd services

Parallel-safe with: B, C, F, G.

Do first because many other repairs depend on reliable `npx`.

### Lane B - Stale Path Drift

Scope:

- `/home/caraxes` active-script cleanup
- archived exception list
- path drift checker

Parallel-safe with: A, C, D, F.

### Lane C - Maintenance Timers And Services

Scope:

- systemd unit file validation
- missing hogsmade driver target
- maintenance authority registry
- live timer verification outside sandbox

Parallel-safe with: A, B, D, F, G.

### Lane D - Editor/Agent Client Profiles

Scope:

- Cursor
- Windsurf
- VS Code/Copilot
- Zed
- Opencode
- Codex
- Claude Code
- Devin
- Gemini/Antigravity

Parallel-safe with: B, C, E, F.

### Lane E - OS Toolchain Degraded State

Scope:

- snap-confine/AppArmor failures
- Go/Rust/Code replacement or repair plan
- Docker daemon health
- Ollama daemon health

Parallel-safe with: D, F, G.

Some actions in this lane require operator privileges. Agents should report copyable commands, not run `sudo`.

### Lane F - Dependency And Lockfile Policy

Scope:

- Node lockfile policy
- Python lockfile policy
- Docker compose policy
- exception registry

Parallel-safe with: A, B, C, D, E.

### Lane G - Legacy Script Classification

Scope:

- Arch-era scripts
- Ubuntu-era replacements
- script registry
- shell syntax validation

Parallel-safe with all other lanes.

## Structured Fix Candidate Schema

A machine-readable fix backlog was created at:

[development-wiring-fix-candidates.json](/home/irfankabir/x-change/docs/agent-handoff-2026-05-06/01-source-maps/development-wiring-fix-candidates.json:1)

Each fix candidate follows this shape:

```json
{
  "id": "WIRE-P0-001",
  "priority": "P0",
  "lane": "wiring",
  "type": "mcp_command_mismatch",
  "title": "Canonical Cascade MCP config uses bare npx while current shell PATH lacks npx",
  "evidence": [],
  "affected_paths": [],
  "recommended_fix": {
    "strategy": "",
    "steps": [],
    "example": {}
  },
  "parallel_group": "A"
}
```

Included candidate IDs:

- `DEVTOOL-P0-001` - npm/npx exist inside nvm but are not on PATH
- `WIRE-P0-001` - canonical MCP config uses bare npx while PATH lacks npx
- `WIRE-P0-002` - stale `/home/caraxes` active path drift
- `MAINT-P0-001` - hogsmade timers point to missing driver path
- `MAINT-P0-002` - maintenance authority registry missing
- `WIRE-P1-001` - MCP coverage differs across clients
- `DEVTOOL-P1-001` - snap-backed Go/Rust/Code degraded
- `DEVTOOL-P1-002` - lockfile policy gaps
- `WIRE-P1-002` - empty/non-strict JSON client config handling
- `MAINT-P1-001` - Arch-era maintenance script overlaps with Ubuntu-era maintenance
- `MAINT-P2-001` - live timer status requires non-sandbox verification

## Recommended Automation Design

### Daily

Run:

1. toolchain PATH health
2. MCP parity health
3. runtime-health-pass
4. stale path drift check
5. maintenance unit offline validation
6. report freshness check

Outputs:

- `~/.echoes/toolchain-health-YYYY-MM-DD.ndjson`
- `~/.echoes/mcp-parity-YYYY-MM-DD.ndjson`
- `agent-harness/reports/daily-maintenance.md`

### Weekly

Run:

1. stay-current package report
2. dependency audit
3. lockfile policy scan
4. git hygiene
5. security check
6. agent bootstrap refresh
7. MCP config regeneration dry-run

Outputs:

- `agent-harness/reports/weekly-maintenance.md`
- `agent-harness/reports/dependency-policy.md`
- `agent-harness/reports/mcp-regeneration-diff.md`

### Monthly

Run:

1. legacy script review
2. archive/active path classification
3. old logs/cache report
4. duplicate config report
5. client profile review

Do not delete automatically. Generate a cleanup plan with exact paths and size estimates, then require operator approval.

## Proposed Files To Add In The Next Implementation Pass

Do not scatter this across every tool. Add one small authority layer:

```text
agent-harness/
  registry/
    toolchain-authority.yaml
    mcp-authority.yaml
    maintenance-authority.yaml
    dependency-policy.yaml
    client-profiles.yaml
    path-authority.yaml
  checks/
    toolchain-health.py
    mcp-parity.py
    unit-file-health.py
    path-drift.py
    dependency-policy.py
    client-config-health.py
  reports/
    daily-maintenance.md
    weekly-maintenance.md
    toolchain-health.md
    mcp-parity.md
    dependency-policy.md
```

Keep current scripts as implementation backends. The new harness should not replace working scripts at first; it should index, validate, and report on them.

## Handoff Order

1. Fix npm/npx availability for non-interactive agents.
2. Build `mcp-authority.yaml` from the working 25-server set.
3. Regenerate or mark client MCP profiles.
4. Repair or disable the two broken hogsmade timers.
5. Create `maintenance-authority.yaml` from existing systemd user units.
6. Add offline unit validator and live-state validator.
7. Add dependency lockfile policy registry.
8. Deprecate or guard Arch-era scripts.
9. Add daily/weekly reports generated from registry state.

## Reproduction Artifacts

Temporary scan artifacts from this pass:

- `/tmp/dev_toolchain_surface.json`
- `/tmp/dev_project_manifests.json`
- `/tmp/active_dev_project_manifests.json`
- `/tmp/wiring_surface_scan.json`
- `/tmp/mcp_wiring_parity.json`
- `/tmp/maintenance_automation_surface.json`

Durable outputs created in this repo:

- [development-toolchain-wiring-maintenance-audit.md](/home/irfankabir/x-change/docs/agent-handoff-2026-05-06/01-source-maps/development-toolchain-wiring-maintenance-audit.md:1)
- [development-wiring-fix-candidates.json](/home/irfankabir/x-change/docs/agent-handoff-2026-05-06/01-source-maps/development-wiring-fix-candidates.json:1)
