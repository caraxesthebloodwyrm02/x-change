# Custom Harness And Agentic Performance Audit - 2026-05-06

## Purpose

This document inventories custom agentic assets and configuration surfaces across:

- `/home/irfankabir`
- `/mnt/arch_data/home/caraxes`

The request was to surface custom definitions, settings/configuration, installed OS tools, and the missing performance layers that currently tax autonomous AI coding workflows.

This was a read-only ecosystem audit. No source files, settings, secrets, or repo history were changed. Sensitive-looking config files were counted and classified by path only; their contents were not read or copied.

## Audit Boundary

### Included

- Agent definitions
- Subagent definitions
- Hooks
- Skills
- Workflows
- Commands
- Rules and guardrails
- Named batches
- Plugins
- MCP/tool config surfaces
- AI editor and coding-agent settings
- OS-level command/tool/application availability
- Knowledgebase and persistent-memory scaffolds

### Excluded Or Pruned

The broad scanner pruned heavy runtime/vendor directories where possible:

- `.git`
- `node_modules`
- `.cache`
- `.local`
- `.venv`, `venv`
- `dist`, `build`, `.next`
- `coverage`, `.pytest_cache`, `.ruff_cache`, `.mypy_cache`
- `target`
- extension caches such as `.vscode/extensions`, `.cursor/extensions`, `.windsurf/extensions`
- package caches such as `.cargo/registry`, `.npm`, `.bun/install/cache`

The config inventory still found some generated and vendor-looking config files because the point of that pass was to reveal settings sprawl. Treat those as "present in the ecosystem", not necessarily authored assets.

## Raw Scan Summary

### Broad Custom-Definition Scan

This scan looked for every matching definition-like file under both homes after pruning heavy runtime/vendor directories.

| Category | Files Matched | LOC Counted | Files With LOC | Sensitive-Path Count |
|---|---:|---:|---:|---:|
| MCP/tools | 6,134 | 436,284 | 4,883 | 68 |
| Skills | 3,654 | 771,289 | 3,072 | 10 |
| Agents | 1,816 | 113,226 | 1,029 | 0 |
| Plugins | 1,375 | 243,746 | 1,291 | 4 |
| Workflows/routines | 1,170 | 184,258 | 1,003 | 9 |
| Rules/guardrails | 1,067 | 122,767 | 717 | 5 |
| Commands | 443 | 51,758 | 238 | 0 |
| Hooks | 352 | 32,093 | 270 | 4 |
| Named batches | 104 | 8,421 | 102 | 0 |

Total broad matches: **16,115**.

Interpretation: this number includes local authored files, copied/scaffolded agent assets, installed marketplace/plugin files, caches, generated metadata, MCP server inventories, and repo-local configs that match naming conventions. It is the correct upper-bound discovery count, not a clean ownership count.

### High-Confidence Local Custom Assets

This narrower pass focused on explicit local custom-definition roots such as `.claude/agents`, `.claude/hooks`, `.claude/commands`, `.claude/rules`, `.claude/scheduler`, `.claude/skills`, custom plugins, Cursor/Windsurf local rule/skill roots, and CascadeProjects agent/command roots.

| Category | High-Confidence Files | LOC Counted |
|---|---:|---:|
| Skills | 586 | 55,583 |
| Commands | 89 | 7,188 |
| Workflows/routines | 80 | 7,129 |
| Rules/guardrails | 44 | 1,292 |
| Agents | 35 | 2,126 |
| Hooks | 25 | 2,140 |
| Plugins | 23 | 2,293 |

Total high-confidence custom assets: **882** files.

This is the best current estimate of "custom definitions scaffolded here" from naming and placement alone.

### High-Confidence Root Distribution

| Root | Files |
|---|---:|
| `/home/irfankabir/.claude/skills` | 429 |
| `/mnt/arch_data/home/caraxes/.claude/commands` | 49 |
| `/home/irfankabir/.codex/skills` | 45 |
| `/home/irfankabir/.claude/scheduler` | 44 |
| `/mnt/arch_data/home/caraxes/plugins` | 43 |
| `/mnt/arch_data/home/caraxes/.claude/scheduler` | 33 |
| `/home/irfankabir/.claude/commands` | 31 |
| `/mnt/arch_data/home/caraxes/skills` | 29 |
| `/home/irfankabir/.cursor/skills-cursor` | 26 |
| `/home/irfankabir/.claude/plugins/atlas-echoes` | 25 |
| `/home/irfankabir/.claude/hooks` | 20 |
| `/home/irfankabir/.claude/plugins/caraxes` | 15 |
| `/home/irfankabir/.windsurf/rules` | 15 |
| `/home/irfankabir/.cursor/rules` | 13 |
| `/mnt/arch_data/home/caraxes/.cursor/skills-cursor` | 11 |
| `/mnt/arch_data/home/caraxes/CascadeProjects/commands` | 9 |
| `/mnt/arch_data/home/caraxes/.claude/rules` | 8 |
| `/home/irfankabir/.claude/agents` | 7 |
| `/mnt/arch_data/home/caraxes/.claude/agents` | 5 |
| `/mnt/arch_data/home/caraxes/CascadeProjects/agents` | 5 |

## Custom Definition Families

### 1. Agents And Subagents

High-signal agent definitions:

| Asset | LOC | Role |
|---|---:|---|
| `/home/irfankabir/.claude/agents/workspace-auditor.md` | 172 | Full workspace audit agent with health, architecture, and opportunity passes. |
| `/home/irfankabir/.claude/agents/session-gate.md` | 70 | End-of-day closeout gate for parked work, submodule state, debt triage, and session logs. |
| `/home/irfankabir/.claude/agents/incident-commander.md` | 139 | Incident coordination surface. |
| `/home/irfankabir/.claude/agents/os-engineer.md` | 98 | OS-level engineering agent. |
| `/home/irfankabir/.claude/agents/glass-dev.md` | 82 | Glass-focused development agent. |
| `/mnt/arch_data/home/caraxes/CascadeProjects/agents/software-engineering-pilot.md` | 29 | CascadeProjects software-engineering domain pilot for GRID, Echoes, APIGuard, and MCP server work. |

The agent layer is strong but fragmented. There are clear role definitions, but no single registry that says:

- which agents are active
- which agents are deprecated
- which tools each agent is allowed to use
- which agent owns which project/domain
- which agent definitions are duplicated across homes
- which ones were generated by marketplace/plugin installation

### 2. Hooks

High-signal hooks:

| Asset | LOC | Role |
|---|---:|---|
| `/home/irfankabir/.claude/hooks/pre-bash-guard.sh` | 107 | Bash guard that blocks destructive command patterns and fails closed on parse failure. |
| `/home/irfankabir/.claude/hooks/pre-sensitive-guard.sh` | 59 | Sensitive-file protection boundary. |
| `/home/irfankabir/.claude/hooks/pre-write-mode-guard.sh` | 28 | Write-mode enforcement. |
| `/home/irfankabir/.claude/hooks/post-write-lint.sh` | 67 | Post-write linting hook. |
| `/home/irfankabir/.claude/hooks/session-start.sh` | 90 | Session-start context injector for dynamic context, session goal, Glass bridge, and GRID health. |
| `/home/irfankabir/.claude/hooks/session-end.sh` | 43 | Session-end hook. |
| `/home/irfankabir/.claude/hooks/pre-compact.sh` | 43 | Context compaction boundary. |
| `/home/irfankabir/.claude/hooks/user-prompt-submit.sh` | 95 | Prompt intake hook. |
| `/home/irfankabir/.claude/hooks/glass-seed-signal.sh` | 93 | Glass signal hook. |

The hook layer is one of the most valuable parts of the ecosystem. It already encodes safety, session hydration, context warnings, and integration checks. The gap is operational visibility: there is no central dashboard or health file that tells an agent whether these hooks actually fired, passed, failed, or were bypassed.

### 3. Commands

High-signal command families:

| Family | Representative Files | Role |
|---|---|---|
| Knowledge | `knowledge.md`, `knowledge-simple.md` | Query local knowledge/RAG sources. |
| Lumos | `lumos.md` | Score ecosystem paths using health, trust, drift, failure, and momentum signals. |
| Maintenance | `maintain*.md` | Triage, probe, execute, seal maintenance loops. |
| Safety/security | `safety.md`, `scalpel.md`, `harden.md`, `cybersafety.md` | Review, remediation, and guard workflows. |
| Atlas/Echoes | `atlas-echoes*.md` | Echoes Atlas route commands. |
| Caraxes | `caraxes*.md` | Caraxes route commands. |
| CascadeProjects | `harness-status.md`, `notebook-query.md`, `notebook-summary.md`, `stage6.md`, `grid.md`, `echoes.md` | Domain and MCP-oriented project commands. |

The command layer is mature in concept. It shows repeated effort to encode reusable workflows as named operator surfaces. The main gap is discoverability: there is no generated command index with tags, tool dependencies, expected output contract, and current pass/fail status.

### 4. Skills

Important local skills:

| Asset | LOC | Role |
|---|---:|---|
| `/home/irfankabir/.claude/skills/claude-api/SKILL.md` | 324 | Claude API usage guidance. |
| `/home/irfankabir/.claude/skills/cybersafety/SKILL.md` | 217 | Security-oriented workflow skill. |
| `/home/irfankabir/.claude/skills/gated-execution/SKILL.md` | 162 | Execution gate workflow. |
| `/home/irfankabir/.claude/skills/harden/SKILL.md` | 233 | Hardening workflow. |
| `/home/irfankabir/.claude/skills/iterate/SKILL.md` | 418 | Iterative improvement workflow. |
| `/home/irfankabir/.claude/skills/interview/SKILL.md` | 639 | Interview/workflow skill. |
| `/home/irfankabir/.claude/skills/mcp-builder/SKILL.md` | 245 | MCP builder guidance. |
| `/home/irfankabir/.claude/plugins/caraxes/skills/harness/SKILL.md` | 101 | Harness domain-function constraint layer. |
| `/home/irfankabir/.claude/plugins/atlas-echoes/skills/atlas-echoes/SKILL.md` | 68 | Echoes Atlas umbrella skill. |
| `/mnt/arch_data/home/caraxes/skills/trust-contract-review/SKILL.md` | 279 | Trust/TUV compliance review. |

Skills are the largest high-confidence custom-definition class. The asset value is high, but there is likely duplication across:

- `/home/irfankabir/.claude/skills`
- `/home/irfankabir/.codex/skills`
- `/mnt/arch_data/home/caraxes/skills`
- `/mnt/arch_data/home/caraxes/.claude/skills`
- Cursor and Windsurf skill roots
- plugin-local skill folders

The missing layer is a skill registry that normalizes name, source, owner, version, trigger, intended host, and validation lane.

### 5. Rules And Guardrails

High-signal rules:

| Asset | LOC | Role |
|---|---:|---|
| `/home/irfankabir/AGENTS.md` | 108 | Home-level agent baseline and precedence. |
| `/home/irfankabir/.claude/rules/dev-rules.md` | 25 | Shared development rules. |
| `/home/irfankabir/.claude/rules/prince-agent.md` | 110 | Prince agent behavior rule. |
| `/home/irfankabir/.claude/rules/prince-context.md` | 53 | Context handling rule. |
| `/home/irfankabir/.claude/rules/remote-agents.md` | 64 | Remote-agent behavior. |
| `/home/irfankabir/.windsurf/rules/scope.md` | scanned | Windsurf scope rule. |
| `/home/irfankabir/.windsurf/rules/tuv-governance-pointers.md` | scanned | Governance pointer rule. |
| `/mnt/arch_data/home/caraxes/.claude/rules/dev-rules.md` | scanned | Caraxes dev-rules mirror. |

The rule layer is a strong foundation for safe work. The gap is precedence consistency across tools. Codex, Claude, Cursor, Windsurf, VS Code, and repo-local AGENTS/CLAUDE files do not all share the same rule loader, and no single manifest declares the canonical precedence tree.

### 6. Workflows And Routines

High-signal workflow/routine surfaces:

| Asset | LOC | Role |
|---|---:|---|
| `/home/irfankabir/.claude/scheduler/dispatch.py` | 998 | Scheduler dispatch engine. |
| `/home/irfankabir/.claude/scheduler/knowledge-loop.yaml` | 44 | Daily knowledge refresh and surfacing routine. |
| `/home/irfankabir/.claude/scheduler/session-gate.yaml` | 55 | Session close routine. |
| `/home/irfankabir/.claude/scheduler/dep-warden.yaml` | 142 | Dependency watcher routine. |
| `/home/irfankabir/.claude/scheduler/ecosystem-triage.yaml` | 77 | Ecosystem triage routine. |
| `/home/irfankabir/.claude/scheduler/pipeline-sweep.yaml` | 74 | Pipeline sweep routine. |
| `/home/irfankabir/.windsurf/workflows/deep-work-operational-intelligence.md` | 63 | Windsurf workflow. |

The scheduler layer is important because it already points toward persistent agent operations. The main problem is path drift: `knowledge-loop.yaml` references `/home/caraxes/...`, while this audit confirmed live knowledge assets under `/home/irfankabir/.claude/knowledge` and `/mnt/arch_data/home/caraxes/.claude/knowledge`. No `.rag_db` directory exists at `/home/irfankabir/.rag_db`, `/mnt/arch_data/home/caraxes/.rag_db`, or `/home/caraxes/.rag_db` at audit time.

### 7. Plugins

High-signal local plugin surfaces:

| Asset | LOC | Role |
|---|---:|---|
| `/home/irfankabir/.claude/plugins/atlas-echoes/.codex-plugin/plugin.json` | 44 | Atlas Echoes plugin metadata. |
| `/home/irfankabir/.claude/plugins/atlas-echoes/PLUGIN_INVENTORY.md` | 122 | Plugin inventory. |
| `/home/irfankabir/.claude/plugins/atlas-echoes/hooks.json` | 49 | Plugin hook wiring. |
| `/home/irfankabir/.claude/plugins/caraxes/.codex-plugin/plugin.json` | 41 | Caraxes plugin metadata. |
| `/home/irfankabir/.claude/plugins/caraxes/hooks.json` | 1 | Caraxes hook placeholder. |
| `/mnt/arch_data/home/caraxes/plugins/atlas-echoes/.codex-plugin/plugin.json` | scanned | Mirrored/parallel Atlas Echoes plugin. |
| `/mnt/arch_data/home/caraxes/plugins/caraxes/.codex-plugin/plugin.json` | scanned | Mirrored/parallel Caraxes plugin. |

Plugin structure exists and is valuable. The missing piece is release discipline:

- no authoritative plugin source root
- no generated diff report between `/home/irfankabir/.claude/plugins/*` and `/mnt/arch_data/home/caraxes/plugins/*`
- no plugin compatibility matrix across Claude/Codex/Cursor/Windsurf
- no validation command that proves plugin metadata, skills, hooks, and MCP config agree

### 8. MCP Tools And MCP Config

Important MCP surfaces found:

- `/home/irfankabir/.mcp.json`
- `/home/irfankabir/.cursor/mcp.json`
- `/home/irfankabir/.codeium/windsurf/mcp_config.json`
- `/home/irfankabir/.copilot/mcp-config.json`
- `/mnt/arch_data/home/caraxes/.mcp.json`
- `/mnt/arch_data/home/caraxes/.cursor/mcp.json`
- `/mnt/arch_data/home/caraxes/.vscode/mcp.json`
- `/mnt/arch_data/home/caraxes/CascadeProjects/.mcp.json`
- `/mnt/arch_data/home/caraxes/CascadeProjects/mcp_config.json`
- `/mnt/arch_data/home/caraxes/CascadeProjects/mcp_inventory.manifest.json`
- `/home/irfankabir/CascadeProjects/Tools/MCPServers/*`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Tools/*`

MCP is one of the largest and most consequential surfaces in the environment. The broad scanner found 6,134 MCP/tool-like matches. The ecosystem has enough MCP work to justify a dedicated `mcp-authority.yaml` with canonical server IDs, command paths, health checks, ownership, transport type, scope, and consuming tools.

### 9. Named Batches

Batch-related surfaces include:

- `/home/irfankabir/.hermes/hermes-agent/batch_runner.py` - 1,287 LOC
- `/home/irfankabir/.hermes/hermes-agent/tests/test_batch_runner_checkpoint.py` - 252 LOC
- Echoes batch config fixtures under `canopy/echoes/config/batch*.json`
- GRID safety batch scripts and schemas in prior scans

This is a useful automation layer, but it is currently not unified with the custom command/workflow registry. Batches should become first-class custom assets with owner, inputs, outputs, retry policy, checkpoint policy, and safety classification.

## Interesting Reads And Interpretation

### Workspace Auditor

`/home/irfankabir/.claude/agents/workspace-auditor.md`

This is the closest existing definition to the current audit request. It has explicit autonomy boundaries, read/test/git discovery permissions, three audit passes, ROI labels, evidence requirements, and an output contract. It should be promoted into the canonical agent harness as `workspace.audit.full`.

### Session Gate

`/home/irfankabir/.claude/agents/session-gate.md`

This is a strong session lifecycle asset. It already models a closeout protocol: orient, classify parked work, handle submodule bumps, triage debt, and write a session log. It should become part of the persistent-memory foundation because session close is where durable context should be consolidated.

### Pre-Bash Guard

`/home/irfankabir/.claude/hooks/pre-bash-guard.sh`

This hook is mature enough to be treated as security infrastructure. It documents limitations, parses tool payloads, normalizes command input, denies destructive patterns, and fails closed on parse failure. It needs a test and telemetry loop, not a rewrite.

### Session Start Hook

`/home/irfankabir/.claude/hooks/session-start.sh`

This hook is the existing bridge toward context carryover. It checks dynamic context freshness, points agents at `SESSION_CONTEXT.md`, gates Glass bridge session behavior, and checks GRID health. The problem is upstream: the knowledgebase it depends on is not fully built and not uniformly authoritative.

### Lumos

`/home/irfankabir/.claude/commands/lumos.md`

Lumos is a strong scoring model for ecosystem work. It ranks paths by health, trust, drift, failure rate, and momentum. It should become the scoring component of the custom harness registry rather than living only as an operator command.

### Knowledge Command And Knowledge Loop

`/home/irfankabir/.claude/commands/knowledge.md`

`/home/irfankabir/.claude/scheduler/knowledge-loop.yaml`

These are the closest existing assets to a persistent knowledgebase. The command expects `~/.rag_db`; the scheduled loop expects `/home/caraxes/.rag_db` and `/home/caraxes/.claude/knowledge/...`; the actual discovered paths are under `/home/irfankabir/.claude/knowledge` and `/mnt/arch_data/home/caraxes/.claude/knowledge`. The design exists; the path authority and vector store are broken or incomplete.

### Harness Skill

`/home/irfankabir/.claude/plugins/caraxes/skills/harness/SKILL.md`

This skill is domain-rich and operationally specific. It defines scenario steps, gates, manifest output, cross-reference expectations, and validation requirements. It should be indexed as both a skill and a workflow domain.

### Atlas Echoes Skill

`/home/irfankabir/.claude/plugins/atlas-echoes/skills/atlas-echoes/SKILL.md`

This is a clean umbrella skill. It identifies source-of-truth surfaces, routes modes, and names validation lanes. It is a model for how other custom skills should declare their real code/data surfaces.

### Trust Contract Review

`/mnt/arch_data/home/caraxes/skills/trust-contract-review/SKILL.md`

This is a governance asset. It encodes fidelity, integrity, accountability, and never-rules. It should become part of the baseline evaluation harness for agent outputs.

## Settings And Configuration Inventory

### Config Scan Summary

The settings/config scan found **16,969** config-like files.

| Area | Files |
|---|---:|
| Project/general | 10,845 |
| Cursor | 3,482 |
| CascadeProjects | 1,220 |
| Codex | 728 |
| Claude | 317 |
| VS Code | 182 |
| Windsurf | 111 |
| GRUFF | 76 |
| x-change | 8 |

Most common config/document extensions:

| Extension/Name | Count |
|---|---:|
| `.json` | 13,882 |
| `.md` | 2,186 |
| `.yml` | 347 |
| `.yaml` | 167 |
| `.toml` | 124 |
| `.example` | 46 |
| `.lock` | 39 |
| `Makefile` | 38 |
| `Dockerfile` | 28 |
| `.env` | 19 |
| `.ini` | 19 |

Sensitive-looking config paths were counted but not read. Counts by area:

| Area | Sensitive-Path Count |
|---|---:|
| Project/general | 118 |
| CascadeProjects | 30 |
| Claude | 25 |
| Cursor | 14 |
| Codex | 6 |
| VS Code | 2 |

### Major Config Surfaces

| Tool/Layer | Representative Paths |
|---|---|
| Claude | `/home/irfankabir/.claude/settings.json`, `.claude/settings.local.json`, hooks, commands, agents, scheduler, rules, skills |
| Codex | `/home/irfankabir/.codex/config.toml`, `/home/irfankabir/.codex/AGENTS.md`, system skills |
| Cursor | `/home/irfankabir/.cursor/mcp.json`, `/home/irfankabir/.cursor/hooks.json`, rules, agents, skills |
| Windsurf | `/home/irfankabir/.windsurf/rules/*`, workflows, Codeium MCP config |
| VS Code | `.vscode/settings.json`, `.vscode/mcp.json`, user-level config under `/mnt/arch_data/home/caraxes/.config/Code/User` |
| Gemini | `.gemini/settings.json`, `.gemini/antigravity/mcp_config.json` |
| Opencode | `.opencode/package.json`, command present as `opencode` |
| Ollama | `.ollama/config.json`, `ollama` command present, daemon not running during version check |
| Projects | AGENTS, CLAUDE, pyproject, package, Docker, compose, Makefile, workflows |

### Config Gaps

1. **No canonical settings authority**
   - Same categories of settings exist across Claude, Codex, Cursor, Windsurf, VS Code, Gemini, Codeium, Copilot, and project roots.
   - There is no single map that says which file is authoritative for MCP, hooks, rules, skills, or session context.

2. **Path drift**
   - `knowledge-loop.yaml` references `/home/caraxes/...`.
   - Actual current homes are `/home/irfankabir` and `/mnt/arch_data/home/caraxes`.
   - This is directly relevant to the persistent-memory failure mode.

3. **Sensitive config sprawl**
   - Sensitive-looking config paths exist in multiple tool roots.
   - The audit did not read them, but their count indicates the need for a secret-safe config registry and redaction scanner.

4. **MCP config duplication**
   - MCP config exists in Claude/Cursor/Windsurf/VS Code/Gemini/CascadeProjects/project roots.
   - There is no generated parity report that confirms each client sees the same intended servers.

5. **No config health score**
   - Config files are present, but there is no routine that scores freshness, validity, duplicate IDs, dead paths, or missing commands.

## Installed OS Tools, Apps, And Programs

### Command Universe

Visible shell command universe:

- `compgen -c | sort -u | wc -l` returned **2,441** unique command names.

Executable counts by bin directory:

| Directory | Executables |
|---|---:|
| `/usr/bin` | 1,667 |
| `/usr/local/bin` | 2 |
| `/home/irfankabir/.local/bin` | 24 |
| `/home/irfankabir/.cargo/bin` | 4 |

Desktop application files:

- `.desktop` applications found: **107**

System packages:

- apt/dpkg system detected.
- `apt-mark showmanual` count: **118** manual packages.
- `dpkg-query -W` count: **1,880** installed packages.
- Flatpak installed but no Flatpak apps found.
- Snap command exists, but `snap version` and `snap list` timed out or were blocked during this audit.

### Available Developer/Agent Tools

| Tool | Status / Version Signal |
|---|---|
| `git` | available, `2.51.0` |
| `gh` | available, `2.46.0` |
| `uv` | available, `0.11.7` |
| `python3` | available, `3.13.7` |
| `node` | available, `v24.15.0` |
| `docker` | available, `29.4.2` |
| `flatpak` | available, `1.16.1` |
| `cursor` | available, `3.2.21` |
| `windsurf` | available, `1.110.1` |
| `claude` | available, `2.1.131` |
| `codex` | available, `0.128.0-alpha.1` |
| `opencode` | available, `1.14.39` |
| `ollama` | client available, `0.22.1`; daemon was not running |
| `sqlite3` | available, `3.46.1` |
| `jq` | available, `1.8.1` |
| `rg` | available, `15.1.0` |
| `fd` | available, `10.4.2` |
| `bat` | available, `0.26.1` |
| `eza` | available, `0.23.4` |
| `pytest` | available, `9.0.3` |
| `playwright` | available, `1.58.0` |

### Missing Or Not On PATH

These were checked and not found on PATH:

- `zsh`
- `fish`
- `python`
- `npm`
- `pnpm`
- `yarn`
- `bun`
- `deno`
- `podman`
- `pacman`
- `yay`
- `paru`
- `gemini`
- `qwen`
- `psql`
- `yq`
- `fzf`
- `ripgrep` as a separate binary name
- `just`
- `ruff`
- `mypy`

Note: `rg` is installed and is ripgrep; the binary name `ripgrep` is not present.

### Tool Health Gaps

1. **Snap confinement issue**
   - `cargo`, `rustc`, `go`, and `code` version checks returned a `snap-confine` AppArmor confinement error.
   - This is an environment health issue, not a code issue.

2. **Node without npm on PATH**
   - `node` is available, but `npm` and `npx` were not found on PATH.
   - JavaScript projects may fail unless they use an alternate package manager or the Node installation is repaired.

3. **Python quality tools missing**
   - `ruff` and `mypy` were not found globally.
   - Some projects can still provide them through `uv`, but the OS-level agent preflight should not assume they exist.

4. **Ollama daemon inactive**
   - `ollama --version` worked but warned that no Ollama instance was running.
   - Any local-model workflow should include a daemon health check.

5. **Snap command unreliable**
   - Snap commands timed out or failed in this environment.
   - Agents should classify this as OS/package-manager degraded state and avoid treating Go/Rust/Code failures as project failures.

## Ranked Agentic Performance Gaps

### P0 - Persistent Knowledgebase Is Not Actually Operational

Observed evidence:

- `knowledge.md` expects `~/.rag_db`.
- `knowledge-loop.yaml` expects `/home/caraxes/.rag_db` and `/home/caraxes/.claude/knowledge/...`.
- Audit confirmed no `.rag_db` exists at `/home/irfankabir/.rag_db`, `/mnt/arch_data/home/caraxes/.rag_db`, or `/home/caraxes/.rag_db`.
- Knowledge scripts and state files do exist under both real homes.

Impact:

Agents repeatedly state that they do not carry context across sessions because the knowledge layer is not reliably hydrated, indexed, retrieved, and written back.

Foundation build steps:

1. Create a canonical file: `agent-harness/memory/memory-authority.yaml`.
2. Declare real roots:
   - `/home/irfankabir/.claude/knowledge`
   - `/mnt/arch_data/home/caraxes/.claude/knowledge`
   - `/home/irfankabir/.codex/memories`
3. Pick one vector DB location, for example `/home/irfankabir/.rag_db`.
4. Update every command/scheduler path that points to `/home/caraxes`.
5. Define ingestion sources:
   - decisions
   - session logs
   - project registries
   - AGENTS/CLAUDE files
   - docs generated by these inventory passes
   - MCP health reports
   - resolved bugs and review findings
6. Implement `context-hydrate`:
   - input: current working directory and user prompt
   - output: top 10 relevant memory entries, active project contract, recent decisions, blocked tools
7. Implement `post-session-consolidate`:
   - input: final answer, changed files, commands run, test results
   - output: durable session memory entry and project registry update
8. Add stale-memory detection:
   - every memory result must include timestamp, source path, and freshness label
9. Add a daily validation:
   - can query memory
   - can ingest a new test note
   - can retrieve that note
   - no stale absolute roots remain

### P0 - No Canonical Custom Asset Registry

Observed evidence:

- 882 high-confidence custom assets.
- 16,115 broad definition-like matches.
- Definitions are spread across Claude, Codex, Cursor, Windsurf, plugins, CascadeProjects, and project roots.

Impact:

Agents cannot reliably know which custom assets exist, which to use, which are stale, and which are duplicates.

Foundation build steps:

1. Create `agent-harness/registry/custom-assets.yaml`.
2. Use this schema:

```yaml
assets:
  - id: claude.agent.workspace-auditor
    kind: agent
    path: /home/irfankabir/.claude/agents/workspace-auditor.md
    owner: claude-home
    status: active
    version: unknown
    triggers:
      - workspace audit
      - project inventory
    tools:
      - Read
      - Bash
      - Glob
    risk: read-mostly
    validation:
      command: null
      last_checked: null
```

3. Generate the registry from filesystem scan, then curate it manually.
4. Add duplicate detection by normalized `name`.
5. Add stale detection by path existence and mtime.
6. Add compatibility fields for Claude/Codex/Cursor/Windsurf.
7. Add `status`: active, experimental, archived, vendor, duplicate, broken.
8. Add `last_reviewed` and `reviewer`.
9. Generate a Markdown index from the YAML.

### P0 - Settings Authority Is Fragmented

Observed evidence:

- 16,969 config-like files.
- MCP configs exist across many tool roots.
- Sensitive config paths are spread across project and tool areas.
- No single precedence tree exists across AGENTS, CLAUDE, Codex config, Cursor rules, Windsurf rules, and VS Code settings.

Impact:

Agents cannot safely infer which settings are canonical. This causes repeated path mistakes, missed tools, stale MCP assumptions, and inconsistent rule application.

Foundation build steps:

1. Create `agent-harness/registry/config-sources.yaml`.
2. Register each config file with:
   - tool
   - path
   - kind
   - sensitive boolean
   - read policy
   - canonical/derived/local-only status
   - validation command
3. Create a redaction-safe config scanner.
4. Generate `config-map.md` with no secret values.
5. Add path-drift check:
   - fail if configs reference nonexistent home roots such as `/home/caraxes`.
6. Add MCP parity check:
   - compare declared MCP servers across Claude, Cursor, Windsurf, VS Code, Gemini, and CascadeProjects.
7. Add a weekly config health report.

### P1 - No Tool Capability Registry

Observed evidence:

- Many tools are installed and working.
- Some expected tools are absent.
- Some commands are present but degraded due OS confinement.

Impact:

Agents waste cycles discovering tool availability and misclassify environment failures as code failures.

Foundation build steps:

1. Create `agent-harness/registry/tool-inventory.yaml`.
2. Store:
   - command
   - path
   - version
   - package source
   - health status
   - last checked
   - failure mode
3. Classify tools:
   - core search/read
   - build/test
   - package managers
   - AI CLIs
   - desktop apps
   - MCP hosts
   - containers
4. Add a preflight command:
   - `agent-harness/checks/tool-preflight.sh`
5. Mark snap-confine/AppArmor failures as environment-level.
6. Generate an agent-readable summary at session start.

### P1 - Session Lifecycle Is Partially Built But Not Closed-Loop

Observed evidence:

- `session-start.sh` exists.
- `session-end.sh` exists.
- `session-gate.md` exists.
- `knowledge-loop.yaml` exists.
- `SESSION_CONTEXT.md` is referenced.

Impact:

Session lifecycle assets exist, but they are not wired into one reliable loop: hydrate, execute, validate, summarize, store, retrieve.

Foundation build steps:

1. Define lifecycle stages:
   - pre-session hydrate
   - task intake
   - tool preflight
   - work execution
   - validation
   - summary
   - memory consolidation
   - next-session seed
2. Create `agent-harness/lifecycle/session.schema.json`.
3. Make every stage write a small JSON receipt.
4. Add `session_id`, `workspace`, `project_id`, `task_id`, and timestamps.
5. Teach session start to load the latest valid receipt.
6. Teach session end to write durable memory and unresolved-blocker records.

### P1 - MCP And Integration Surfaces Need A Single Authority

Observed evidence:

- MCP configs exist across many clients.
- Cursor project MCP metadata lists many user servers.
- CascadeProjects has MCP config and inventory manifests.
- Prior ecosystem scans show Glass, GRID, Echoes, Harness, Ori, Lots, Maintain, RAG, and other servers forming an integration mesh.

Impact:

Agents can see pieces of the tool mesh, but no single file explains which MCP server is canonical, which host uses it, what command starts it, and what health check proves it works.

Foundation build steps:

1. Create `agent-harness/registry/mcp-authority.yaml`.
2. For each server, record:
   - id
   - display name
   - command
   - args
   - cwd
   - transport
   - clients
   - health check
   - owner project
   - status
3. Build parity checks against each client config.
4. Add a no-secret render mode.
5. Generate `mcp-map.md` and a graph diagram.

### P1 - Evaluation And Benchmarking Are Not Yet Productized

Observed evidence:

- Lumos defines scoring concepts.
- Trust review defines compliance concepts.
- Workspace auditor defines opportunity ranking.
- There is no unified benchmark harness for agent behavior.

Impact:

Agent quality is judged manually and inconsistently.

Foundation build steps:

1. Create `agent-harness/evals/eval-suite.yaml`.
2. Add evaluation categories:
   - path authority
   - instruction compliance
   - secret safety
   - context retention
   - test discipline
   - config awareness
   - integration mapping
   - final-report usefulness
3. Create fixture tasks from real previous failures.
4. Score 0-100 with explicit evidence.
5. Run evals per agent/tool combination.
6. Generate a trend report.

### P2 - Provenance And Attribution Are Present But Not Universal

Observed evidence:

- Prior workspace memory points to `IDENTITY.md`, `AUTHOR.md`, and `PROJECT_REGISTRY.yaml` as provenance infrastructure.
- Some projects include AGENTS/CLAUDE files and authorship metadata.
- Attribution is not uniformly tied to custom definitions and generated assets.

Impact:

Agents cannot always determine whether a definition is authored, generated, vendor-cached, copied, mirrored, or obsolete.

Foundation build steps:

1. Extend `custom-assets.yaml` with `attribution`.
2. Supported values:
   - built-by-prince
   - generated-local
   - installed-plugin
   - marketplace-cache
   - mirrored
   - archived
   - unknown
3. Add file hash and first-seen timestamp.
4. Add duplicate/mirror relationships.
5. Generate attribution reports per home.

### P2 - Visual Observability Is Missing

Observed evidence:

- User goal includes producing visual data diagrams after reading documentation.
- Current outputs are mostly Markdown and scattered configs.

Impact:

The ecosystem is too large to reason about as flat lists.

Foundation build steps:

1. Generate graph data from:
   - custom assets
   - MCP servers
   - projects
   - configs
   - memory sources
2. Create `agent-harness/graphs/ecosystem.graph.json`.
3. Render:
   - project-domain map
   - tool/client/MCP map
   - memory flow map
   - custom definition dependency map
   - gap priority board
4. Keep diagrams generated from registries, not hand-drawn.

### P2 - Dependency And Package Manager Health Needs Normalization

Observed evidence:

- `uv`, Python, Node, Docker work.
- `npm` is missing despite Node being available.
- Go/Rust tooling appears snap-confine blocked.
- Snap itself is unreliable.

Impact:

Agents need a predictable way to know whether to run `uv`, `npm`, `cargo`, `go`, Docker, or skip with an environment caveat.

Foundation build steps:

1. Add package-manager detection to `tool-preflight.sh`.
2. For each project, detect canonical package manager from lockfiles.
3. Store project-level command policy:
   - x-change: `uv` + `PYTHONPATH="$PWD/src"`
   - GRUFF: Node/npm or project-specific commands
   - Python prototypes: `uv`
4. Distinguish:
   - command missing
   - command present but broken
   - dependency missing
   - test failure
   - sandbox/network failure

## Baseline Scaffold

Create a dedicated harness directory under a workspace root. Suggested initial location:

`/home/irfankabir/x-change/docs/agent-harness-plan/`

For an implementation repo, use:

`/home/irfankabir/agent-harness/`

Suggested structure:

```text
agent-harness/
  README.md
  registry/
    custom-assets.yaml
    config-sources.yaml
    tool-inventory.yaml
    mcp-authority.yaml
    project-authority.yaml
  memory/
    memory-authority.yaml
    session.schema.json
    project-memory.schema.json
    context-pack.schema.json
  checks/
    scan-custom-assets.py
    scan-config-sources.py
    tool-preflight.sh
    mcp-parity-check.py
    path-drift-check.py
    secret-safe-config-check.py
  lifecycle/
    hydrate-session.py
    close-session.py
    write-session-receipt.py
  evals/
    eval-suite.yaml
    fixtures/
    run-evals.py
  reports/
    custom-assets.md
    config-map.md
    tool-health.md
    mcp-map.md
    memory-health.md
  graphs/
    ecosystem.graph.json
    render-mermaid.py
```

## Implementation Batches

### Batch 1 - Registry Foundation

Goal: make custom assets visible.

Steps:

1. Create `agent-harness/registry/custom-assets.yaml`.
2. Convert the high-confidence 882-file manifest into YAML records.
3. Add `kind`, `path`, `owner`, `status`, `loc`, `sensitive`, `host`, and `attribution`.
4. Mark marketplace/vendor/cache assets separately.
5. Generate `reports/custom-assets.md`.
6. Add a duplicate-name report.

Exit criteria:

- Every high-confidence agent/hook/skill/command/rule/workflow/plugin has one registry entry.
- Every registry path exists or is marked missing.
- Duplicate names are visible.

### Batch 2 - Config Authority

Goal: stop path drift and settings ambiguity.

Steps:

1. Create `registry/config-sources.yaml`.
2. Register Claude, Codex, Cursor, Windsurf, VS Code, Gemini, Codeium, Copilot, and project config roots.
3. Add secret-safe classification.
4. Add path-drift check for nonexistent homes.
5. Generate config map with no secret values.

Exit criteria:

- Any `/home/caraxes` references are either fixed or explicitly grandfathered.
- Agents know which config files are canonical and which are local overrides.

### Batch 3 - Knowledgebase Repair

Goal: make context carryover real.

Steps:

1. Choose canonical vector DB location.
2. Update knowledge command and scheduler paths.
3. Bootstrap the vector store.
4. Ingest docs, decisions, session logs, project registries, and generated audit docs.
5. Add retrieval tests.
6. Add session-start hydration and session-end consolidation.

Exit criteria:

- `/knowledge <query>` returns sources.
- New session can retrieve prior-session decisions.
- Stale or missing memory is reported explicitly.

### Batch 4 - Tool And MCP Health

Goal: remove repeated rediscovery.

Steps:

1. Create `tool-inventory.yaml`.
2. Record versions and failures for major tools.
3. Create `mcp-authority.yaml`.
4. Compare MCP configs across clients.
5. Generate health reports.

Exit criteria:

- Agent can know before work whether Python, Node, Docker, MCP, local RAG, and browser tools are healthy.
- Snap/AppArmor failures are not misreported as project failures.

### Batch 5 - Evaluation Harness

Goal: benchmark agent performance with actual rules.

Steps:

1. Convert recurring failures into fixtures.
2. Score agents on instruction compliance, path authority, secret safety, context use, validation, and final report quality.
3. Run the same task across tools where possible.
4. Store results in `reports/evals/`.

Exit criteria:

- Agent performance has measurable baselines.
- Improvements are tied to scored regressions, not vibes.

## Ranked Resurfacing Candidates

1. **Knowledge command + knowledge loop**
   - Highest leverage because it directly addresses context carryover.

2. **Workspace auditor**
   - Already matches ecosystem-scale inventory and ranking.

3. **Session gate**
   - Best candidate for reliable end-of-session memory consolidation.

4. **Pre-bash/pre-sensitive/pre-write guards**
   - Strong safety layer that should become global preflight infrastructure.

5. **Lumos**
   - Existing scoring model should feed the benchmark and prioritization system.

6. **Atlas Echoes plugin**
   - Good example of a plugin with source surfaces, modes, and validation lanes.

7. **Harness skill**
   - Rich domain workflow that should be indexed as both skill and integration pattern.

8. **Trust contract review**
   - Should be part of agent output evaluation and review gates.

9. **MCP inventory manifests**
   - Needed to unify the tool mesh.

10. **CascadeProjects domain pilots**
   - Good seed for domain-based agent routing.

## Practical Next Move

The next work session should not reorganize files yet. It should create the registry foundation first:

1. `agent-harness/registry/custom-assets.yaml`
2. `agent-harness/registry/config-sources.yaml`
3. `agent-harness/registry/tool-inventory.yaml`
4. `agent-harness/memory/memory-authority.yaml`
5. `agent-harness/checks/path-drift-check.py`
6. `agent-harness/reports/custom-assets.md`

That gives every future agent a stable map before anything is moved, renamed, deduplicated, or promoted.

## Reproduction Notes

To reproduce this audit safely:

1. Run filesystem scans only.
2. Prune `.git`, package caches, extension caches, virtual environments, and build outputs.
3. Count sensitive-looking files by path only.
4. Do not read `.env`, `settings.local.json`, credential, key, token, or OAuth files.
5. Separate broad matches from high-confidence custom assets.
6. Persist raw scan outputs as generated artifacts before curating.
7. Build docs from generated manifests, not manual memory.

Temporary scan artifacts produced during this pass:

- `/tmp/custom_harness_scan.json`
- `/tmp/config_inventory_scan.json`
- `/tmp/os_tools_inventory.json`
- `/tmp/os_package_inventory.json`
- `/tmp/os_tool_versions.json`
- `/tmp/interesting_reads_summary.json`
- `/tmp/custom_assets_high_conf_manifest.csv`

These are not durable project files. Promote them into `agent-harness/reports/raw/` only after deciding the canonical harness location.
