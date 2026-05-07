# MCP Wiring Authority

## Objective

Stop editor and agent wiring drift by defining the canonical MCP server set, client profiles, command path policy, and parity checks. This document is the human-readable authority; `07-registries/mcp-authority.json` is the machine-readable input for tooling.

## Canonical Server Set (25 servers)

All 25 are defined in `~/.claude.json`. The table below reflects the **observed state** as of 2026-05-07.

### Active (4) — explicitly enabled at global level

| Server | Language | Depth | Enabled because |
|---|---|---|---|
| `personal-rag` | Python | Full; federated query | Prince's personal intelligence — memory, rules, skills, audit. Core to every session. |
| `eligibility-server` | TS | Full (15 src, 105 tests) | Structural audit + evolution cases. Lumos fast-lane dependency. |
| `echoes-server` | TS | Full (audit, character, precedent) | Cross-server audit trail. Mandatory for ecosystem observability. |
| `glimpse-server` | TS | Growing | Glimpse cognitive pipeline — session analysis, confidence frames. |

### Intentionally disabled (4) — explicitly denied at global level

| Server | Reason | Re-enable condition |
|---|---|---|
| `grid-server` | Full Mothership orchestration; heavy. Not needed for Glass/x-change focus. | When GRID Mothership (port 8080) is needed. |
| `afloat-server` | Workflow execution engine. Not needed for current focus. | When maintenance workflows are part of active work. |
| `lots-server` | Experiment catalog and execution. Not needed for current focus. | When experiment-driven development is active. |
| `pulse-server` | Morning briefings, journal, focus tracking. Human-facing, not agent-facing. | When operator wants daily digest automation. |

### Dormant (17) — defined but neither enabled nor disabled

These servers exist in `~/.claude.json` with correct paths and env vars. They are not broken — they are simply not loaded. With `enableAllProjectMcpServers: true` at global level, project-level settings could activate them per-directory.

| Server | Language | Depth | Activation trigger |
|---|---|---|---|
| `code-analysis` | Python | Skeleton | When Python code quality/security scanning is needed. |
| `craft-server` | TS | Full (7 tools, gruff toolbelt) | When gruff proportion/pipeline work is active. |
| `glass-server` | TS | Growing | When cwd has `.glass-profile.yaml` and Glass spatial work is active. |
| `grid-enhanced-tools` | Python | Skeleton | When code quality/dependency/test coverage tooling is needed. |
| `grid-intelligence` | Python | Skeleton | When knowledge graph sessions are needed. |
| `grid-rag` | Python | Full | When RAG over codebase/docs is needed. |
| `grid-rag-enhanced` | Python | Full (enhanced fork) | When intelligent RAG with multi-hop reasoning is needed. |
| `harness-server` | TS | Growing (8 src, 16 tests) | When Great League scenario execution is needed. |
| `maintain-server` | TS | Full | When ecosystem cleanup/diagnostics are needed. |
| `mangrove-server` | TS | Growing (4 tools, 7 tests) | When git hygiene scanning across Mangrove is needed. |
| `nexus-server` | TS | Skeleton | When architectural resilience evaluation is needed. |
| `ori-server` | TS | Full (23 src, 112 tests) | When threat model coverage + test orchestration is needed. |
| `overview-server` | TS | Growing (8 src, 36 tests) | When ecosystem checkpoint/trend analysis is needed. |
| `portfolio-safety-lens` | Python | Skeleton | When portfolio risk signals are needed. |
| `school-server` | TS | Skeleton | When knowledge ingestion and study plans are needed. |
| `seeds-server` | TS | Growing | When ecosystem scan + bookmark reference is needed. |
| `test-runner` | Python | Skeleton | When pytest execution from MCP is needed. |

### Plugin servers (10) — installed, require OAuth authentication

These are financial-data vendor plugins in `~/.claude.json`. All require browser-based OAuth before tools become available. None are currently authenticated.

| Plugin | Provider | Status |
|---|---|---|
| `plugin:financial-analysis:aiera` | Aiera (AI transcripts) | Not authenticated |
| `plugin:financial-analysis:chronograph` | Chronograph (PE/VC monitoring) | Not authenticated |
| `plugin:financial-analysis:daloopa` | Daloopa (structured fundamentals) | Not authenticated |
| `plugin:financial-analysis:egnyte` | Egnyte (secure file storage) | Not authenticated |
| `plugin:financial-analysis:factset` | FactSet (terminal data) | Not authenticated |
| `plugin:financial-analysis:lseg` | LSEG/Refinitiv (market data) | Not authenticated |
| `plugin:financial-analysis:moodys` | Moody's (credit ratings) | Not authenticated |
| `plugin:financial-analysis:morningstar` | Morningstar (fund research) | Not authenticated |
| `plugin:financial-analysis:pitchbook` | PitchBook (private markets) | Not authenticated |
| `plugin:financial-analysis:sp-global` | S&P Global (ratings + CIQ) | Not authenticated |

## Client Profiles

| Client | Config path | Profile | Notes |
|---|---|---|---|
| Claude Code (global) | `~/.claude.json` + `~/.claude/settings.local.json` | **active** — 4 enabled, 4 disabled, `enableAllProjectMcpServers: true` | The primary agent client. |
| x-change (project) | `x-change/.claude/settings.local.json` | **minimal** — 0 enabled, 1 disabled (glimpse), `enableAllProjectMcpServers: false` | Overrides global; glimpse is disabled to avoid bridge noise when not in Glass context. |
| Cursor (current home) | `~/.cursor/mcp.json` | full — 25-server set, absolute nvm `npx` | Active editor client. |
| Windsurf (current home) | `~/.codeium/windsurf/mcp_config.json` | full — 25-server set, absolute nvm `npx` | Active editor client. |
| CascadeProjects canonical | `/mnt/arch_data/.../CascadeProjects/mcp_config.json` | full — 25-server set, bare `npx` | Reference config; needs command policy repair (bare `npx` → absolute path). |
| Copilot | `~/.copilot/mcp-config.json` | minimal — 5-server subset | GitHub Copilot agent. |
| Generic MCP | `~/.mcp.json` | minimal — 1-server subset | Fallback config. |
| Antigravity | `~/.gemini/antigravity/mcp_config.json` | disabled — empty config | Gemini/Google agent. |
| Caraxes-side user configs | `/mnt/arch_data/home/caraxes/.config` | archive — 19-21 server sets | Historical; do not treat as active. |

## Command Policy

**Preferred deterministic command for TypeScript MCP servers:**

```
/home/irfankabir/.nvm/versions/node/v24.15.0/bin/npx
```

**Rule:** Do not mix bare `npx` (PATH-dependent) and absolute `npx` (deterministic) without recording the choice in the client profile. CascadeProjects canonical config currently uses bare `npx` — this is a repair candidate (WIRE-P0-001).

## Parity Checks

Every active client profile must validate:

1. Server count matches declared profile (full=25, minimal=4-5, disabled=0)
2. Command path exists and is executable
3. `cwd` resolves after `${env}` expansion
4. No stale `/home/caraxes` active paths (caraxes = historical Arch root)
5. Env key names are listed without values in shared configs

## Parity Report (2026-05-07)

| Check | Status | Detail |
|---|---|---|
| Canonical set declared | PASS | 25 servers in `~/.claude.json` |
| Active set matches profile | PASS | 4 enabled matches "core agent minimum" |
| Intentionally disabled documented | PASS | 4 disabled with re-enable conditions |
| Dormant servers classified | PASS | 17 classified with activation triggers |
| Plugin servers accounted | PASS | 10 financial plugins, none authenticated |
| Command policy declared | PASS | Absolute nvm `npx` preferred |
| CascadeProjects bare-npx drift | **FAIL** | WIRE-P0-001: bare `npx` in canonical config |
| x-change glimpse disabled | PASS | Intentional — avoids bridge noise |
| No stale caraxes active paths | PASS | All active configs use `/home/irfankabir` |
| Client profiles classified | PASS | 9 clients across full/minimal/archive/disabled |

## Fix Candidates

| ID | Priority | Description |
|---|---|---|
| WIRE-P0-001 | P0 | CascadeProjects `mcp_config.json` uses bare `npx` — should use absolute nvm path for determinism |
| WIRE-P1-002 | P1 | 17 dormant servers have no explicit enable/disable decision — classify each as "intentionally dormant," "should enable per project," or "archive candidate" |
| WIRE-P1-003 | P1 | Financial plugin servers are installed but unauthenticated — document authentication procedure per vendor |
| WIRE-P2-004 | P2 | x-change project `settings.local.json` disables glimpse-server but could enable glass-server when Glass rail is active |

## Next Implementation Action

The authority is complete for the current (4-server) operating profile. Repair candidates WIRE-P0-001 through WIRE-P2-004 are documented but intentionally deferred — they require operator decisions about which dormant servers to promote, not agent-side automation. Apply repairs after BATCH-04 (toolchain authority) is complete, since toolchain state affects command path resolution.
