# Directory Structure Consolidation Playbook

Date: 2026-05-06  
Scope: `/home/irfankabir` and `/mnt/arch_data/home/caraxes`  
Mode: read-only audit plus reproducible organization plan  
Related report: `portfolio-inventory-benchmark.md`

## Purpose

This document gives an agent-executable plan for bringing structural discipline
to both home directories without breaking active project paths.

The current workspace has valuable projects, but the directory layout mixes:

- active source repositories,
- mirrored repositories,
- umbrella workspaces,
- archives,
- handoff bundles,
- generated build outputs,
- editor/agent state,
- package-manager caches,
- local runtime data,
- one-off experiments,
- historical migrations.

The goal is not to move files immediately. The goal is to create a safe
structure, classify every important directory, define canonical paths, preserve
compatibility, and only then migrate in controlled batches.

## Executive Summary

The main structural problem is competing roots.

Observed high-level roots include:

- `/home/irfankabir/CascadeProjects`
- `/mnt/arch_data/home/caraxes/CascadeProjects`
- `/home/irfankabir/hogsmade`
- `/home/irfankabir/gruff`
- `/home/irfankabir/gruff/workspace`
- `/mnt/arch_data/home/caraxes/workspace`
- `/home/irfankabir/canopy`
- `/mnt/arch_data/home/caraxes/canopy`
- `/home/irfankabir/roots`
- `/mnt/arch_data/home/caraxes/roots`
- `/home/irfankabir/archive`
- `/home/irfankabir/seed`
- `/mnt/arch_data/home/caraxes/seed`
- `/home/irfankabir/HANDOFF`
- `/mnt/arch_data/home/caraxes/HANDOFF`

There are also tool-state roots such as `.claude`, `.codex`, `.caraxes`,
`.afloat`, editor extension directories, package-manager caches, and action
runner directories.

The safest consolidation strategy is:

1. create a canonical registry,
2. classify every root,
3. mark canonical versus mirror versus archive,
4. add compatibility aliases before moves,
5. migrate one domain batch at a time,
6. run path/reference checks after each batch,
7. keep rollback manifests.

The first real implementation target should be a registry and audit script, not
a mass filesystem move.

## Non-Goals

This playbook does not recommend:

- deleting directories,
- force-moving git repositories,
- flattening monorepos,
- rewriting active absolute paths blindly,
- replacing all mirrors with symlinks in one pass,
- moving dot-tool state such as `.claude` or `.codex`,
- changing remote repository history,
- normalizing every historical archive.

## Safety Rules

Any agent following this document must follow these rules.

1. Never move or delete a git repository until it is classified and clean.
2. Never move a directory referenced by active config without adding a
   compatibility alias first.
3. Never assume duplicate names are duplicate content.
4. Never use modification time alone to decide canonicality.
5. Treat `/mnt/arch_data/home/caraxes` as likely high-capacity/project storage.
6. Treat `/home/irfankabir` as the active user home and compatibility surface.
7. Treat dot directories as tool-owned unless explicitly documented otherwise.
8. Treat generated output directories as disposable only after they are confirmed
   ignored, rebuildable, and not manually curated.
9. Record every proposed move in a migration manifest before executing it.
10. Prefer aliases and registry updates before path rewrites.

## Observed Structural Issues

### 1. Competing Project Roots

The same conceptual portfolio appears under multiple top-level roots.

Examples:

- `CascadeProjects` exists under `/mnt/arch_data/home/caraxes` and has related
  views under `/home/irfankabir/hogsmade` and `/home/irfankabir/CascadeProjects`.
- `canopy` exists under both homes.
- `roots` exists under both homes.
- GRUFF-style workspace appears under `/home/irfankabir/gruff`,
  `/home/irfankabir/gruff/workspace`, and `/mnt/arch_data/home/caraxes/workspace`.

Risk:

Agents and scripts may edit a mirror, stale checkout, or archive thinking it is
canonical.

Required discipline:

Every project gets one canonical path and zero or more mirror/archive paths.

### 2. Active Projects Mixed with Archives

Archive-like roots appear beside active roots:

- `/home/irfankabir/archive`
- `/home/irfankabir/seed/archive`
- `/mnt/arch_data/home/caraxes/seed/archive`
- `Documentation/archive` inside Cascade-style trees
- `HANDOFF` roots

Risk:

Search, tooling, and agents pick stale files or historical copies.

Required discipline:

Archive roots should be excluded from default project discovery unless an agent
explicitly asks for history.

### 3. Mirrors Without Source-of-Truth Metadata

Mirrored families include:

- `canopy/afloat`
- `canopy/ai-web-demo`
- `canopy/echoes`
- `canopy/token-type-calculator`
- `canopy/upwork-cli`
- `roots/dep-mapper`
- `roots/glimpse-engine`
- `roots/mcp-orchestration-language`
- `roots/portfolio-control`
- `roots/python-craft`
- `roots/security`
- `CascadeProjects/Projects/apiguard`

Risk:

Two copies may drift. A fix can land in one and be invisible in the other.

Required discipline:

For each mirror family, record:

- canonical path,
- mirror path,
- sync direction,
- last confirmed commit,
- whether edits are allowed in mirrors.

### 4. Umbrella Repos Contain Real Subprojects

CascadeProjects contains:

- `Applications/`
- `Tools/MCPServers/`
- `Projects/`
- `Components/`
- `Documentation/`

GRUFF/workspace-style roots contain:

- `prototype/`
- `python-prototype/`
- `rust-prototype/`
- `racks/`
- `design-system/`
- `schemas/`
- `scripts/`

Risk:

Agents may treat a subproject as independent when it is actually part of an
umbrella repo, or treat an umbrella as a single app.

Required discipline:

Subprojects need registry entries that say:

- git owner root,
- local package root,
- runnable commands,
- whether edits should be made at subproject or umbrella level.

### 5. Generated Artifacts Are Visually Prominent

Observed generated/runtime-style directories include:

- `node_modules`
- `.next`
- `dist`
- `build`
- `coverage`
- `.pytest_cache`
- `.ruff_cache`
- `.vite-cache`
- action runner `_work`
- package-manager caches
- editor extension directories
- session and transcript stores

Risk:

Directory scans are noisy, agents waste context, and generated content is
mistaken for source.

Required discipline:

Default audits should exclude generated directories unless the task is about
build output, package state, or runtime diagnostics.

### 6. Tool State Is Mixed with Project State

Tool-owned roots include:

- `/home/irfankabir/.claude`
- `/home/irfankabir/.codex`
- `/home/irfankabir/.caraxes`
- `/home/irfankabir/.afloat`
- editor extension roots
- `/mnt/arch_data/home/caraxes/actions-runner`

Risk:

Moving or cleaning these can break tools, sessions, skills, plugins, or CI
runners.

Required discipline:

Tool state is classified as runtime/tool-owned. Do not consolidate it into
project source trees.

## Proposed Target Model

The target model uses a small number of conceptual zones.

```text
~/                          compatibility and active user home
  projects-active/           optional future active-source entrypoint
  projects-mirrors/          optional future mirrors only
  projects-archive/          optional future archives only
  reports/                   generated portfolio reports
  .claude/                   tool state, leave in place
  .codex/                    tool state, leave in place
  .caraxes/                  local runtime/registry, leave in place unless defined

/mnt/arch_data/home/caraxes/
  CascadeProjects/           canonical Cascade workspace
  workspace/                 GRUFF-compatible workspace mirror or canonical, to decide
  canopy/                    candidate canonical app/product family, to decide
  roots/                     candidate canonical infrastructure tools, to decide
  seed/                      templates and historical seeds
  HANDOFF/                   handoff bundles
  archives/                  optional future archive consolidation
```

This is a conceptual target. It should be implemented through a registry first,
not by immediately creating every directory.

## Recommended Canonical Root Decisions

These are recommendations based on observed structure and recent activity. Each
one must be confirmed by git status and path-reference checks before movement.

### CascadeProjects

Recommended canonical path:

`/mnt/arch_data/home/caraxes/CascadeProjects`

Reasoning:

- It is a git repo.
- It has active recent commits.
- It contains the current Glass app, MCP servers, shared components, and
  namespaced documentation.
- It already documents itself as a multi-project workspace.

Compatibility paths to classify:

- `/home/irfankabir/hogsmade`
- `/home/irfankabir/CascadeProjects`

Recommendation:

Do not move CascadeProjects. Instead, mark `/mnt/.../CascadeProjects` as
canonical and treat other Cascade-like trees as mirror, local worktree, or
archive after verification.

### GRUFF Workspace

Candidate canonical path:

`/home/irfankabir/gruff/workspace`

Alternative candidate:

`/mnt/arch_data/home/caraxes/workspace`

Reasoning:

Memory and prior work indicate `/home/irfankabir/gruff/workspace` is the active
GRUFF workspace path for many tasks, while `/mnt/.../workspace` appears to be a
parallel or legacy-compatible copy.

Recommendation:

Do not decide by folder name. Decide by:

- latest git commit,
- clean status,
- active remotes,
- user workflow references,
- tests that actually run,
- references in CLAUDE/AGENTS/docs.

Until confirmed, classify both as `active-candidate`.

### GRUFF Python Prototype

Recommended canonical path:

`/home/irfankabir/gruff/workspace/python-prototype`

Reasoning:

Prior implementation work and docs identify this as the canonical notebook
runtime. A second path exists at `/home/irfankabir/gruff/python-prototype`.

Recommendation:

Keep the workspace copy canonical and classify the other as compatibility,
legacy, or alias after checking whether it is a symlink, copy, or stale tree.

### canopy

Candidate canonical path:

`/home/irfankabir/canopy`

Alternative candidate:

`/mnt/arch_data/home/caraxes/canopy`

Reasoning:

Both homes contain mirrored canopy projects. Some `/home` copies have more
recent branch state, such as Echoes on a fix branch, while `/mnt` copies appear
as parallel clean clones.

Recommendation:

Do not consolidate canopy as a whole. Decide per project:

- `afloat`
- `ai-web-demo`
- `echoes`
- `token-type-calculator`
- `upwork-cli`

For each, choose canonical by git remote, commit, branch, and current active
work.

### roots

Candidate canonical path:

`/mnt/arch_data/home/caraxes/roots`

Alternative candidate:

`/home/irfankabir/roots`

Reasoning:

Roots are infrastructure tools. Both homes have near-identical families. The
`/mnt` root is closer to the CascadeProjects storage area and may be better as
the canonical source for portfolio infrastructure, but this needs commit-level
verification.

Recommendation:

Decide per repo:

- `dep-mapper`
- `glimpse-engine`
- `mcp-orchestration-language`
- `portfolio-control`
- `python-craft`
- `security`
- `mistral-test`

### x-change

Recommended canonical path:

`/home/irfankabir/x-change`

Reasoning:

It is active, git-backed, and not observed as a mirrored tree under `/mnt`.

Recommendation:

Keep in place. It can hold reports temporarily, but long-term portfolio reports
should move to a dedicated reports or registry repo once established.

### personal-rag

Recommended canonical path:

`/home/irfankabir/personal-rag`

Reasoning:

It is active, git-backed, local-first, and not simply a mirrored Cascade
subproject.

Recommendation:

Keep in place. Add registry-aware ingestion rather than moving it.

### workspace-trust-auditor

Recommended canonical path:

`/home/irfankabir/workspace-trust-auditor`

Reasoning:

It is active and directly relevant to this consolidation pass.

Recommendation:

Keep in place. It should become the implementation home for inventory and
scorecard automation.

## Target Taxonomy

Every directory that matters should be assigned one of these statuses.

| Status | Meaning | Move Policy |
|---|---|---|
| `canonical-active` | Main source of truth for a project | Do not move without alias and test plan |
| `active-candidate` | May be canonical but needs verification | Read-only until decided |
| `mirror-readonly` | Copy of canonical project | No direct edits except sync metadata |
| `archive-frozen` | Historical content | Exclude from default search |
| `handoff` | Transfer bundle or report bundle | Preserve; index separately |
| `generated` | Build/cache/output | Exclude by default; rebuildable |
| `tool-state` | Owned by editor/agent/package tool | Leave in place |
| `runtime-data` | Logs, DBs, transcripts, session data | Do not move without service shutdown |
| `template` | Reusable scaffold or seed | Keep under template namespace |
| `experiment` | Unpromoted prototype | Keep but mark owner/domain/expiry |

## Proposed Directory Discipline

### Active Source

Active source should live in a small number of places:

- `/mnt/arch_data/home/caraxes/CascadeProjects`
- `/home/irfankabir/gruff/workspace`
- `/home/irfankabir/canopy/<project>` or `/mnt/.../canopy/<project>` after per-project decision
- `/home/irfankabir/roots/<project>` or `/mnt/.../roots/<project>` after per-project decision
- `/home/irfankabir/x-change`
- `/home/irfankabir/personal-rag`
- `/home/irfankabir/workspace-trust-auditor`

### Archives

Archives should be grouped and excluded from normal project search:

- `/home/irfankabir/archive`
- `/home/irfankabir/seed/archive`
- `/mnt/arch_data/home/caraxes/seed/archive`
- `Documentation/archive` inside umbrella repos

Future optional target:

```text
/mnt/arch_data/home/caraxes/archives/
  workspace/
  seeds/
  handoffs/
  legacy-repos/
```

Only migrate archives after active roots are stable.

### Handoffs and Reports

Handoff bundles should not sit visually beside active project roots forever.

Current roots:

- `/home/irfankabir/HANDOFF`
- `/mnt/arch_data/home/caraxes/HANDOFF`
- project-local docs reports such as this one.

Recommended target:

```text
/home/irfankabir/reports/
  portfolio/
  security/
  migration/
  handoff-index/
```

or, if reports should live on mounted storage:

```text
/mnt/arch_data/home/caraxes/reports/
  portfolio/
  security/
  migration/
  handoff-index/
```

### Tool State

Leave in place:

- `.claude`
- `.codex`
- `.caraxes`
- `.afloat`
- editor extension roots
- action runner root
- package-manager roots

Cleanups here require separate tool-specific runbooks.

### Generated Output

Generated output should be ignored by default:

- `node_modules`
- `.next`
- `dist`
- `build`
- `coverage`
- `.pytest_cache`
- `.ruff_cache`
- `.vite-cache`
- action runner `_work`

Do not move generated output. Rebuild or clean it only through project commands.

## Reproducible Audit Procedure

Any agent can reproduce the structural audit with these read-only commands.

### Step 1: List top-level roots

```bash
find /home/irfankabir /mnt/arch_data/home/caraxes \
  -maxdepth 1 -mindepth 1 -type d -printf '%p\n' | sort
```

### Step 2: Find git repositories

```bash
find /home/irfankabir /mnt/arch_data/home/caraxes \
  -maxdepth 5 -type d -name .git -prune -print 2>/dev/null | sort
```

### Step 3: Find project marker directories

```bash
find /home/irfankabir /mnt/arch_data/home/caraxes \
  -maxdepth 5 -type f \
  \( -name README.md -o -name AGENTS.md -o -name CLAUDE.md \
     -o -name package.json -o -name pyproject.toml \
     -o -name go.mod -o -name Cargo.toml \) \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -not -path '*/.cache/*' \
  -not -path '*/.local/*' \
  -not -path '*/.config/*' \
  -printf '%h/%f\n' | sort
```

### Step 4: Collect git state for candidate repos

For each repo found:

```bash
git -C "$repo" rev-parse --show-toplevel
git -C "$repo" branch --show-current
git -C "$repo" rev-parse --short HEAD
git -C "$repo" log -1 --format='%cI|%s'
git -C "$repo" status --porcelain
git -C "$repo" remote -v
```

### Step 5: Detect likely duplicate families

```bash
find /home/irfankabir /mnt/arch_data/home/caraxes \
  -maxdepth 5 -type d \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -printf '%f\t%p\n' | sort
```

Then group by the first column and inspect duplicates manually.

### Step 6: Search for absolute path references before moving anything

For each candidate move:

```bash
rg -n --fixed-strings "/old/absolute/path" \
  /home/irfankabir /mnt/arch_data/home/caraxes \
  -g '!node_modules' -g '!.git' -g '!.cache' -g '!.local' -g '!.config'
```

Also search for project names:

```bash
rg -n "project-name|old-dir-name" \
  /home/irfankabir /mnt/arch_data/home/caraxes \
  -g '!node_modules' -g '!.git' -g '!.cache' -g '!.local' -g '!.config'
```

### Step 7: Build a migration manifest

Before moving anything, create a manifest entry:

```yaml
- id: cascadeprojects-canonicalization
  status: proposed
  old_path: /home/irfankabir/hogsmade
  new_path: /mnt/arch_data/home/caraxes/CascadeProjects
  action: classify-only
  compatibility_alias: pending
  canonical_path: /mnt/arch_data/home/caraxes/CascadeProjects
  validation:
    - git status clean
    - path references checked
    - tests or smoke checks listed
  rollback:
    - remove alias only
    - no content move in this phase
```

## Migration Strategy

### Phase 0: Freeze the Rules

Deliverables:

- this playbook,
- a canonical registry schema,
- an exclusion list for generated/tool-state directories,
- a policy that no move happens without a manifest.

Exit criteria:

- registry schema is accepted,
- every future move has a manifest template.

### Phase 1: Registry-Only Classification

Do not move files.

Tasks:

1. Create `PROJECT_REGISTRY.yaml` or a similar machine-readable registry.
2. Add entries for all top-level project roots.
3. Mark each entry with taxonomy status.
4. Add canonical path recommendations.
5. Add mirror/archive references.
6. Add run/test commands where known.

Exit criteria:

- every active candidate has a status,
- every mirrored family has a proposed canonical path,
- no content has moved.

### Phase 2: Path Reference Audit

Do not move files.

Tasks:

1. Search for absolute references to all active roots.
2. Search config files, docs, scripts, workflows, AGENTS, CLAUDE, package files,
   and pyproject files.
3. Record references per project.
4. Mark references as:
   - must update,
   - compatibility alias required,
   - archive-only,
   - generated/no action.

Exit criteria:

- every proposed move has a reference map,
- no unknown high-risk references remain.

### Phase 3: Compatibility Alias Plan

Do not move files until aliases are designed.

Possible compatibility techniques:

- shell variables in docs and scripts,
- registry lookup command,
- symlink from old path to new path,
- wrapper scripts,
- `.env` path variables,
- MCP server config update,
- editor workspace update.

Preference order:

1. registry lookup,
2. config variable,
3. wrapper script,
4. symlink,
5. hard path rewrite.

Symlinks are useful but should not become the only source of truth. They hide
structure problems if the registry is missing.

Exit criteria:

- every path-sensitive move has a compatibility plan.

### Phase 4: Low-Risk Moves

Only move low-risk, non-active, non-tool-state directories first.

Good candidates:

- clearly archived handoff bundles,
- generated reports,
- historical seeds,
- stale documentation bundles.

Bad candidates:

- active git repos,
- dot-tool directories,
- action runner directories,
- `x-change`,
- `personal-rag`,
- `workspace-trust-auditor`,
- active CascadeProjects,
- active GRUFF workspace.

Exit criteria:

- no broken references,
- registry updated,
- rollback manifest verified.

### Phase 5: Mirror Consolidation

For each mirrored repo family:

1. compare remotes,
2. compare branch names,
3. compare HEAD commits,
4. compare dirty state,
5. compare recent commit timestamps,
6. decide canonical,
7. mark non-canonical as mirror-readonly or archive-frozen,
8. optionally replace mirror with symlink only after confirmation.

Do not consolidate all mirrors in one batch.

Recommended batches:

- `canopy/*`
- `roots/*`
- Cascade/hogsmade family
- GRUFF/workspace family
- seeds/handoff family

### Phase 6: Active Root Simplification

After registry and mirrors are stable, simplify visible top-level layout.

Possible target:

```text
/home/irfankabir/
  active/
    x-change -> /home/irfankabir/x-change
    personal-rag -> /home/irfankabir/personal-rag
    workspace-trust-auditor -> /home/irfankabir/workspace-trust-auditor
    gruff -> /home/irfankabir/gruff/workspace
    cascade -> /mnt/arch_data/home/caraxes/CascadeProjects
  reports/
  archives/
  tools/
```

This can be alias-only. It does not require moving canonical repos.

## Proposed Registry Schema

```yaml
version: 1
generated_at: "2026-05-06"
projects:
  - id: cascadeprojects
    display_name: CascadeProjects
    status: canonical-active
    domain: multi-domain-hosting-platform
    canonical_path: /mnt/arch_data/home/caraxes/CascadeProjects
    git_owner_root: /mnt/arch_data/home/caraxes/CascadeProjects
    mirrors:
      - path: /home/irfankabir/hogsmade
        status: active-candidate
        note: classify as mirror/worktree/archive after commit comparison
      - path: /home/irfankabir/CascadeProjects
        status: active-candidate
        note: contains overlapping Cascade-style projects
    archive_paths: []
    generated_excludes:
      - node_modules
      - dist
      - build
      - coverage
    safe_to_move: false
    compatibility_required: true
    validation_commands:
      - npm test
      - npm run lint

  - id: x-change
    display_name: x-change
    status: canonical-active
    domain: learning-finance-governance
    canonical_path: /home/irfankabir/x-change
    git_owner_root: /home/irfankabir/x-change
    mirrors: []
    safe_to_move: false
    compatibility_required: false
    validation_commands:
      - PYTHONPATH="$PWD/src" uv run python -m unittest discover -s tests -v
```

## Candidate Classification Table

| Path | Proposed Status | Notes |
|---|---|---|
| `/mnt/arch_data/home/caraxes/CascadeProjects` | `canonical-active` | Main Cascade workspace candidate. |
| `/home/irfankabir/hogsmade` | `active-candidate` | Cascade-like overlap; decide mirror/worktree/archive. |
| `/home/irfankabir/CascadeProjects` | `active-candidate` | Contains overlapping Projects/Tools/Grove material. |
| `/home/irfankabir/gruff` | `canonical-active` or umbrella | GRUFF root with nested workspace. |
| `/home/irfankabir/gruff/workspace` | `canonical-active` candidate | Likely active GRUFF workspace. |
| `/mnt/arch_data/home/caraxes/workspace` | `active-candidate` | GRUFF-like workspace mirror/legacy candidate. |
| `/home/irfankabir/gruff/workspace/python-prototype` | `canonical-active` | Canonical GRUFF notebook runtime candidate. |
| `/home/irfankabir/gruff/python-prototype` | `mirror-readonly` candidate | Needs verification. |
| `/home/irfankabir/x-change` | `canonical-active` | Keep in place. |
| `/home/irfankabir/personal-rag` | `canonical-active` | Keep in place. |
| `/home/irfankabir/workspace-trust-auditor` | `canonical-active` | Keep in place. |
| `/home/irfankabir/canopy` | `active-candidate` | Decide per child repo. |
| `/mnt/arch_data/home/caraxes/canopy` | `active-candidate` | Decide per child repo. |
| `/home/irfankabir/roots` | `active-candidate` | Decide per child repo. |
| `/mnt/arch_data/home/caraxes/roots` | `active-candidate` | Decide per child repo. |
| `/home/irfankabir/archive` | `archive-frozen` | Exclude from default scans. |
| `/home/irfankabir/seed` | `template` plus `archive-frozen` | Split template versus archive semantics. |
| `/mnt/arch_data/home/caraxes/seed` | `template` plus `archive-frozen` | Same as above. |
| `/home/irfankabir/HANDOFF` | `handoff` | Preserve; index separately. |
| `/mnt/arch_data/home/caraxes/HANDOFF` | `handoff` | Preserve; index separately. |
| `/home/irfankabir/.claude` | `tool-state` | Do not move in this pass. |
| `/home/irfankabir/.codex` | `tool-state` | Do not move in this pass. |
| `/home/irfankabir/.caraxes` | `runtime-data` or `tool-state` | Registry/runtime area; do not move until documented. |
| `/mnt/arch_data/home/caraxes/actions-runner` | `tool-state` | CI runner; do not move casually. |

## Mirror Families to Resolve

### Cascade Family

Observed:

- `/mnt/arch_data/home/caraxes/CascadeProjects`
- `/home/irfankabir/hogsmade`
- `/home/irfankabir/CascadeProjects`

Recommended process:

1. Compare git roots and remotes.
2. Compare HEAD commits and branches.
3. Check whether `hogsmade` is a fork/worktree, mirror, or active alternate.
4. Mark `/mnt/.../CascadeProjects` canonical unless evidence says otherwise.
5. Convert non-canonical trees to mirror-readonly or archive-frozen.

### GRUFF Family

Observed:

- `/home/irfankabir/gruff`
- `/home/irfankabir/gruff/workspace`
- `/home/irfankabir/gruff/workspace/python-prototype`
- `/home/irfankabir/gruff/python-prototype`
- `/mnt/arch_data/home/caraxes/workspace`
- `/home/irfankabir/archive/caraxes-workspace-legacy`

Recommended process:

1. Keep active GRUFF work under `/home/irfankabir/gruff/workspace` until proven
   otherwise.
2. Treat archive copy as archive-frozen.
3. Compare `/mnt/.../workspace` against active workspace.
4. Make python-prototype canonical under workspace.

### Canopy Family

Observed mirrored projects:

- `afloat`
- `ai-web-demo`
- `echoes`
- `token-type-calculator`
- `upwork-cli`

Recommended process:

1. Resolve one child project at a time.
2. Prefer the checkout with the active branch and latest intentional work.
3. Mark the other as mirror-readonly.
4. Add a registry entry for each child, not just the canopy parent.

### Roots Family

Observed mirrored projects:

- `dep-mapper`
- `glimpse-engine`
- `mcp-orchestration-language`
- `portfolio-control`
- `python-craft`
- `security`
- `mistral-test`

Recommended process:

1. Decide if `roots` should live under `/mnt` as infrastructure storage.
2. Confirm commit parity.
3. Keep active writes to one root only.

### Seeds and Handoffs

Observed:

- `/home/irfankabir/seed`
- `/mnt/arch_data/home/caraxes/seed`
- `/home/irfankabir/HANDOFF`
- `/mnt/arch_data/home/caraxes/HANDOFF`

Recommended process:

1. Split `seed/templates` from `seed/archive`.
2. Keep templates discoverable.
3. Move handoffs only after indexing and preserving timestamps.
4. Exclude archive directories from default search.

## Path Breakage Risks

High-risk path consumers:

- AGENTS and CLAUDE files,
- MCP server config,
- package scripts,
- CI workflow files,
- shell scripts,
- Python config and docs,
- personal-rag ingestion paths,
- Glass bridge paths,
- GRUFF manifest/runtime paths,
- action runner work paths,
- editor workspace files,
- symlinked project aliases.

Before moving any active directory, search for:

- exact absolute path,
- basename,
- package name,
- MCP server name,
- repo ID,
- bridge/env variable references.

## Move Manifest Template

Every move must be represented before execution.

```yaml
id: short-human-readable-id
date: "YYYY-MM-DD"
owner: agent-or-human
status: proposed
risk: low|medium|high

source:
  path: /old/path
  type: git-repo|subproject|archive|handoff|generated|tool-state|runtime-data
  git:
    root: /old/git/root
    branch: main
    head: abc1234
    dirty: false

target:
  path: /new/path
  type: canonical|mirror|archive|alias

reason:
  summary: why this change exists
  expected_benefit:
    - clearer structure
    - fewer duplicate roots

preflight:
  required:
    - git status checked
    - absolute path references searched
    - active services stopped if needed
    - backup or rollback path confirmed
  commands:
    - git -C /old/git/root status --porcelain
    - rg -n --fixed-strings "/old/path" /home/irfankabir /mnt/arch_data/home/caraxes -g '!node_modules' -g '!.git'

compatibility:
  strategy: registry|env-var|wrapper|symlink|none
  old_path_behavior: remains|symlink|removed-after-window
  planned_expiry: null

validation:
  commands:
    - project-specific test command
    - project-specific smoke command
  path_checks:
    - old path behavior checked
    - new path behavior checked

rollback:
  steps:
    - restore old path or remove alias
    - revert registry entry
    - rerun validation
```

## Agent Execution Checklist

Use this checklist for every consolidation batch.

### Before the Batch

- Confirm the requested scope.
- Read root `AGENTS.md` and project-local instructions.
- Run read-only inventory commands.
- Identify git roots.
- Check dirty state.
- Check remotes.
- Search path references.
- Create move/classification manifest.
- Confirm risk level.

### During the Batch

- Touch one family at a time.
- Prefer classification changes before filesystem moves.
- Preserve timestamps when archiving where possible.
- Keep old path compatibility until validation passes.
- Do not cross-edit mirrors.
- Do not clean generated outputs unless explicitly scoped.

### After the Batch

- Re-run git status for touched repos.
- Re-run path-reference checks.
- Run project-specific smoke tests.
- Update registry.
- Update report.
- Record rollback steps.
- Summarize moved, aliased, untouched, and deferred paths.

## Recommended First Implementation

The first practical implementation should be registry-only.

Create a new repo or use `workspace-trust-auditor` for:

```text
portfolio-registry/
  PROJECT_REGISTRY.yaml
  schemas/project-registry.schema.json
  scripts/audit_roots.py
  scripts/check_duplicate_names.py
  scripts/check_path_references.py
  reports/
```

Preferred home:

`/home/irfankabir/workspace-trust-auditor`

Reason:

That project already exists to audit local workspaces. It is the natural owner
for this capability.

Alternative:

`/mnt/arch_data/home/caraxes/roots/portfolio-control`

Reason:

That repo is intended as a control plane, but it is currently smaller and may be
better as the automation consumer rather than inventory owner.

## Recommended Batch Order

### Batch 1: Registry and Classification

Risk: low  
Filesystem moves: none

Deliverables:

- registry schema,
- initial project registry,
- duplicate-family report,
- generated-exclude policy.

### Batch 2: Cascade Family Decision

Risk: medium  
Filesystem moves: none initially

Deliverables:

- canonical Cascade path,
- hogsmade classification,
- `/home/irfankabir/CascadeProjects` classification,
- MCP server source-of-truth map.

### Batch 3: GRUFF Family Decision

Risk: medium

Deliverables:

- canonical GRUFF workspace path,
- python-prototype canonical decision,
- archive/legacy labels,
- compatibility guidance.

### Batch 4: Canopy Per-Project Decisions

Risk: medium

Deliverables:

- canonical path per canopy project,
- mirror-readonly labels,
- branch/commit comparison table.

### Batch 5: Roots Per-Project Decisions

Risk: medium

Deliverables:

- canonical path per infrastructure tool,
- owner domain per tool,
- mirror-readonly labels.

### Batch 6: Handoff, Seed, and Archive Cleanup

Risk: low to medium

Deliverables:

- handoff index,
- template/archive split,
- archive search exclusion policy,
- optional reports root.

### Batch 7: Active Aliases

Risk: medium

Deliverables:

- stable convenience aliases,
- documented environment variables,
- updated agent instructions.

Potential aliases:

```text
/home/irfankabir/active/cascade -> /mnt/arch_data/home/caraxes/CascadeProjects
/home/irfankabir/active/gruff -> /home/irfankabir/gruff/workspace
/home/irfankabir/active/x-change -> /home/irfankabir/x-change
/home/irfankabir/active/personal-rag -> /home/irfankabir/personal-rag
/home/irfankabir/active/workspace-trust-auditor -> /home/irfankabir/workspace-trust-auditor
```

Aliases should be additive. Do not remove old paths until all consumers are
updated.

## Structural Principles Going Forward

1. One canonical path per project.
2. Mirrors are read-only unless explicitly promoted.
3. Archives are searchable only when requested.
4. Generated outputs are excluded from default audits.
5. Tool state is not source code.
6. Umbrella repo subprojects get registry entries.
7. Active project roots must have run/test commands.
8. Every path move needs a manifest.
9. Every consolidation batch needs rollback.
10. Reports should be stored in a predictable reports namespace.

## Final Recommended Shape

The portfolio should eventually feel like this:

```text
Active source:
  /mnt/arch_data/home/caraxes/CascadeProjects
  /home/irfankabir/gruff/workspace
  /home/irfankabir/x-change
  /home/irfankabir/personal-rag
  /home/irfankabir/workspace-trust-auditor
  one canonical canopy root per project
  one canonical roots root per infrastructure project

Compatibility:
  /home/irfankabir/active/*
  old paths retained as aliases during transition

Archives:
  /home/irfankabir/archive
  /mnt/arch_data/home/caraxes/archives or existing seed/archive roots

Reports:
  /home/irfankabir/reports or /mnt/arch_data/home/caraxes/reports

Tool state:
  .claude, .codex, .caraxes, .afloat, editor roots, action runner
```

## Immediate Next Todo List

1. Add a registry schema.
2. Generate initial `PROJECT_REGISTRY.yaml`.
3. Mark `/mnt/.../CascadeProjects` as proposed canonical Cascade root.
4. Mark x-change, personal-rag, and workspace-trust-auditor as canonical-active.
5. Mark archive and handoff roots as excluded from default project search.
6. Compare canopy mirrors per child repo.
7. Compare roots mirrors per child repo.
8. Resolve GRUFF workspace canonical path.
9. Create a path-reference report for any proposed move.
10. Only then consider aliases or moves.

## Bottom Line

The workspace does not need a big-bang rearrangement. It needs authority.

The correct first consolidation artifact is a canonical registry plus a
repeatable audit command. Once agents can answer "which path is canonical?" and
"is this path safe to move?", the actual cleanup becomes much lower risk.
