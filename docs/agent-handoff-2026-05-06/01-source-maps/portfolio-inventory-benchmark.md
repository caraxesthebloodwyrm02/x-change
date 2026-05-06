# Portfolio Inventory and Benchmark Report

Date: 2026-05-06  
Scope: `/home/irfankabir` and `/mnt/arch_data/home/caraxes`  
Mode: read-only inventory and analysis, followed by documentation capture  

## Executive Summary

The workspace is converging into a local-first agent ecosystem rather than a set
of unrelated apps. The strongest pattern is a stack made of:

- intelligence engines and routers,
- live agent/session surfaces,
- local memory and retrieval,
- evidence and reward governance,
- trust, security, and portfolio inspection,
- small CLI/library tools that support the larger system.

The highest-leverage projects are not the ones with the most files alone. They
are the projects with a clear role in a broader operating model:

1. `GRID-main` is the strongest engine and intelligence framework.
2. `Glass` is the strongest original product surface.
3. `personal-rag` is the memory/index substrate.
4. `x-change` is the learning, evidence, and finance governance core.
5. `workspace-trust-auditor` is the portfolio inspection and trust surface.

My strongest read: the portfolio is becoming a trust-aware local agent operating
system. GRID is the reasoning/validation engine, Glass is the spatial work
surface, personal-rag is memory, x-change is policy and economics, and
workspace-trust-auditor is the inspection layer. The next unlock is not another
large feature. It is a canonical project registry, integration contracts, and
automated benchmark scorecards across the ecosystem.

## Methodology

The inventory was performed from the filesystem and git metadata only. No files
were modified during the scan.

Signals collected:

- git repositories under both home roots,
- latest commit timestamps and subjects,
- dirty-state counts,
- project marker files such as `README.md`, `AGENTS.md`, `CLAUDE.md`,
  `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `Makefile`,
  `Dockerfile`, lockfiles, and TypeScript/Python config,
- file-count and language-extension signals,
- test, CI, Docker, and Makefile presence,
- README and project-doc snippets,
- umbrella workspace structure under CascadeProjects and GRUFF,
- duplicate or mirrored project paths.

Important limitation: this report is a portfolio benchmark and architecture
read, not a full code-quality proof for every project. Some claims should be
validated by running each repository's test and lint commands before external
publication.

## Benchmark Rules

The ranking uses practical engineering criteria rather than only ambition or
repo size.

### 1. Product Clarity

Can a stranger quickly understand what the project does, who it serves, and what
problem it solves?

Strong signals:

- clear README,
- concrete use case,
- quick start,
- examples,
- named workflows,
- a visible boundary between product behavior and internal architecture.

### 2. Engineering Maturity

Does the project look reproducible, testable, and maintainable?

Strong signals:

- tests,
- CI workflows,
- lockfiles,
- typed config,
- Makefile or documented commands,
- Docker or deployment posture where relevant,
- current commits,
- low dirty-state risk,
- small enough surface to reason about.

### 3. System Leverage

Does the project become infrastructure for other projects?

Strong signals:

- shared contracts,
- CLI/API/MCP interfaces,
- reusable libraries,
- data formats,
- registry entries,
- visible downstream consumers.

### 4. Integration Gravity

How naturally does the project connect to other repos?

Strong signals:

- bridge files,
- MCP servers,
- ingestion APIs,
- evidence payloads,
- audit exports,
- local-first data stores,
- dependency or workflow maps.

### 5. Originality and Usefulness

Is the project more than a standard demo, wrapper, or scaffold?

Strong signals:

- unusual but coherent product idea,
- real operational need,
- specific domain model,
- tangible workflow improvement,
- demonstrated evidence of iteration.

## Top Ranked Projects

### 1. GRID-main

Path: `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main`  
Latest observed commit: `2026-05-06T05:17:28+06:00`  
Observed signal: large Python project, hundreds of tests, CI/Docker/Make/uv,
structured docs, active benchmark/performance work.

GRID is the strongest core-engine project in the portfolio. It has the best
blend of ambition, test density, infrastructure, and system leverage. It reads
as the intelligence and validation layer that other tools want to orbit.

Why it ranks first:

- broad but coherent engine identity,
- strong testing and infrastructure posture,
- clear local-first AI positioning,
- enough maturity to act as a portfolio anchor,
- natural integration points for MCP servers, RAG, Glass, and trust tooling.

Main risk:

- scope is large enough that boundary discipline matters. GRID should expose
  sharply defined contracts to other projects rather than becoming a catch-all.

Best next moves:

- publish a stable integration contract for external callers,
- keep slow/performance tests explicitly marked,
- define which portfolio projects are official GRID consumers,
- generate a compact "GRID in the ecosystem" map.

### 2. Glass and glass-server

Paths:

- `/mnt/arch_data/home/caraxes/CascadeProjects/Applications/glass`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Tools/MCPServers/glass-server`

Latest observed Glass/Cascade commit: `2026-05-06T17:20:24+06:00`  
Latest observed glass-server scoped commit: `2026-05-06T16:49:24+06:00`  
Observed signal: Electron app, bridge schema, MCP emitter, live session surface,
tests, active security hardening.

Glass is the strongest original product surface. It turns agent work into a
spatial, visible, shared field instead of another chat log. The idea is
distinctive and has strong internal fit with the rest of the workspace.

Why it ranks second:

- highly original user experience,
- clear "co-presence surface" identity,
- direct integration with agent sessions,
- bridge-driven architecture that other tools can write to,
- strong visual/product differentiation.

Main risk:

- bridge-file trust and renderer/main boundaries need continued hardening.
  Local file interfaces are powerful but must be treated as security surfaces.

Best next moves:

- harden bridge path ownership, symlink, and mode checks,
- force trusted origins in main-process IPC,
- produce a stable bridge contract fixture suite,
- package Glass with explicit dev/prod security profiles.

### 3. personal-rag

Path: `/home/irfankabir/personal-rag`  
Latest observed commit: `2026-05-06T16:08:02+06:00`  
Observed signal: local-first RAG, Chroma-style local indexing, tests, Docker,
docs, ingestion pipeline, no external telemetry positioning.

personal-rag is the portfolio memory layer. It should become the durable index
for sessions, docs, reports, project inventories, decisions, and integration
contracts.

Why it ranks third:

- clear local-first identity,
- strong fit with the user's workflow,
- natural consumer of generated reports and session output,
- useful across almost every other project.

Main risk:

- without a portfolio registry and source taxonomy, it may ingest useful data
  but struggle to distinguish canonical paths from mirrors, archives, and
  generated artifacts.

Best next moves:

- add source-type taxonomy for repos, mirrors, archives, sessions, docs, and
  generated reports,
- ingest portfolio scorecards,
- integrate constrained-signal-pipeline as a numeric sidecar,
- expose "project memory brief" queries by canonical project ID.

### 4. x-change

Path: `/home/irfankabir/x-change`  
Latest observed commit: `2026-05-06T17:27:28+06:00`  
Observed signal: pure Python service, reward lifecycle, evidence ledger, Stripe
webhook boundary, Glass ingest, tests, policy docs.

x-change is the clearest domain-specific project: learning evidence plus reward
governance plus finance boundaries. It is smaller than GRID and Glass, but its
domain model is sharp.

Why it ranks fourth:

- concrete learning/finance/governance purpose,
- explicit policy lifecycle,
- evidence is separated from payment confirmation,
- Stripe boundary is documented,
- naturally consumes Glass evidence.

Main risk:

- security hardening is essential because this project touches auth, reward
  state, and payment events.

Best next moves:

- add failed-auth rate limiting,
- harden malformed `Content-Length` handling on Stripe webhook requests,
- require current Stripe signature schemes unless legacy compatibility is
  explicitly documented,
- evolve `RewardToken` beyond a stub into epistemic classification fields,
- add end-to-end contract tests for Glass evidence to x-change state changes.

### 5. workspace-trust-auditor

Path: `/home/irfankabir/workspace-trust-auditor`  
Latest observed commit: `2026-05-06T09:52:27+06:00`  
Observed signal: read-only ChatGPT App and MCP server, workspace inventory,
dependency posture, secret-risk signals, provenance reporting, tests.

workspace-trust-auditor is the right meta-tool for this environment. It should
become the inspection lens for the whole portfolio.

Why it ranks fifth:

- directly addresses the scale of the workspace,
- read-only posture matches trust requirements,
- combines local inventory, dependency posture, provenance, and report output,
- can become a front door for portfolio health.

Main risk:

- it needs a canonical registry source. Without one, it can discover many
  projects but cannot confidently resolve duplicates, mirrors, active roots, and
  archives.

Best next moves:

- consume a canonical project registry,
- emit machine-readable benchmark scorecards,
- classify duplicates and mirrors,
- integrate with personal-rag for searchable audit history,
- expose "next best infrastructure fix" per repo.

### 6. Echoes

Path: `/home/irfankabir/canopy/echoes`  
Latest observed commit: `2026-05-06T17:48:01+06:00`  
Observed signal: very large multimodal assistant platform, Docker, CI, uv,
hundreds of Python files, extensive docs and JSON artifacts.

Echoes is ambitious and substantial. It likely contains important work, but it
is harder to benchmark quickly because the stated scope is very broad and the
repo is large.

Why it ranks sixth:

- significant code and docs,
- active maintenance,
- security and orchestration themes,
- likely overlaps with the broader agent platform direction.

Main risk:

- the product claim is much larger than the quick visible boundary. It needs a
  sharper "what works today" map to be externally convincing.

Best next moves:

- create a current-capabilities matrix,
- separate demos, research, generated data, and production modules,
- publish a minimal golden path,
- identify which pieces should feed GRID, Glass, Afloat, or personal-rag.

### 7. CascadeProjects and hogsmade

Paths:

- `/mnt/arch_data/home/caraxes/CascadeProjects`
- `/home/irfankabir/hogsmade`

Latest observed CascadeProjects commit: `2026-05-06T17:20:24+06:00`  
Latest observed hogsmade commit: `2026-05-06T18:23:55+06:00`  
Observed signal: multi-project local workspace with applications, MCP servers,
components, docs, and operational projects.

CascadeProjects is not one product. It is a hosting platform and workspace
organizer for multiple domains. hogsmade appears to overlap heavily with this
tree and should be treated as a mirror/fork/workspace variant until a registry
declares otherwise.

Why it ranks seventh:

- strong ecosystem role,
- many projects and shared packages,
- active CI and dependency work,
- houses Glass and MCP servers.

Main risk:

- without a canonical registry, duplicate trees make it difficult to know which
  path is source-of-truth.

Best next moves:

- define canonical project IDs,
- classify each subdirectory as app, MCP server, library, docs, archive, or
  generated output,
- generate a workspace map from checked-in metadata,
- decide whether hogsmade is canonical, mirror, experiment, or archive.

### 8. Afloat

Path: `/home/irfankabir/canopy/afloat`  
Latest observed commit: `2026-04-29T23:32:25+06:00`  
Observed signal: Next.js app, Ollama-first dynamic routing, optional OpenAI,
Stripe, Upstash Redis, JWT, tests, docs.

Afloat is one of the clearest productized app ideas. It has an understandable
user flow: get past a cognitive/context gate quickly, then stop.

Why it ranks eighth:

- externally understandable product,
- SaaS-style architecture,
- auth, payment, rate-limit, and docs already considered,
- natural consumer of MCP orchestration.

Main risk:

- billing/auth/security flows need production verification before real users.

Best next moves:

- verify Stripe webhook and subscription lifecycle end-to-end,
- define which local tools it can call through MCP,
- connect it to mcp-orchestration-language for workflow generation,
- produce a small public launch checklist.

### 9. GRUFF python-prototype

Path: `/home/irfankabir/gruff/workspace/python-prototype`  
Latest observed commit: `2026-04-29T23:29:40+06:00`  
Observed signal: canonical GRUFF Geometry Box notebook runtime, manifest
persistence, heatmap output, craft-backed compass renders, bridge payloads,
FastAPI-style API surface, tests.

GRUFF python-prototype is a strong local runtime and notebook-state project. It
sits between geometry, notebooks, rendering, and bridge emission.

Why it ranks ninth:

- concrete local runtime role,
- manifest and bridge payload posture,
- tests and packaged runtime direction,
- natural fit with Glass as a visual surface.

Main risk:

- it needs a clearer relationship to GRID, Glass, and CascadeProjects so it is
  not perceived as a separate parallel architecture.

Best next moves:

- define GRUFF as runtime, GRID as intelligence engine, Glass as surface,
- emit bridge payload fixtures that Glass can render,
- add contract tests for manifest to bridge output,
- keep strict mode and inspection mode clearly separated.

### 10. APIGuard

Path: `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/apiguard`  
Latest observed commit: `2026-05-06T16:08:21+06:00`  
Observed signal: Python library for rate limiting, retry, circuit breaking,
structured logging, tests, Docker/Make/uv.

APIGuard is practical infrastructure. It is less original than Glass/x-change,
but it is immediately useful and packageable.

Why it ranks tenth:

- clear library scope,
- useful across multiple services,
- tests and packaging markers,
- strong fit for x-change, Afloat backends, and MCP servers.

Main risk:

- needs clear examples showing adoption inside portfolio services.

Best next moves:

- add integration examples for x-change and Afloat-style routes,
- define async and sync usage recipes,
- expose structured metrics hooks,
- use it to standardize local service resilience.

### 11. mcp-orchestration-language

Path: `/mnt/arch_data/home/caraxes/roots/mcp-orchestration-language`  
Latest observed commit: `2026-05-01T00:41:27+06:00`  
Observed signal: TypeScript DSL, YAML workflow language, registry validation,
tests, package lock.

This project is promising because the portfolio already has many MCP-shaped
surfaces. A DSL can reduce manual orchestration and make workflows auditable.

Why it ranks eleventh:

- clear fit with MCP server ecosystem,
- small and focused,
- natural connection to Afloat and CascadeProjects,
- can become a workflow compiler.

Main risk:

- without real production workflows, it may remain a good idea rather than a
  used control language.

Best next moves:

- define three real workflows: ecosystem health check, Glass evidence emit,
  portfolio audit,
- compile to commands and rollback plans,
- emit audit events into workspace-trust-auditor or personal-rag.

### 12. constrained-signal-pipeline

Path: `/home/irfankabir/constrained-signal-pipeline`  
Latest observed commit: `2026-05-01T15:52:39+06:00`  
Observed signal: small Python project, JSON CLI, numeric signal filter, uv lock,
subprocess integration posture.

This is a small but well-shaped utility. It should not be overexpanded. Its
value is a clean subprocess contract for numeric signal analysis.

Why it ranks twelfth:

- compact,
- clear input/output contract,
- good fit with personal-rag,
- low integration cost.

Main risk:

- too small to stand alone as a major product.

Best next moves:

- keep the API stable,
- add a few golden fixtures,
- integrate into personal-rag reports,
- document when to use it versus GRID scoring.

## Concise Individual Reads

This section is intended as an organization and todo aid.

| Project | Category | Read | Next Todo |
|---|---|---|---|
| GRID-main | Agent intelligence engine | Strongest core system; highest maturity. | Publish stable external contract and consumer map. |
| Glass | Spatial agent UI | Most original product surface. | Harden bridge trust and add contract fixtures. |
| glass-server | MCP bridge emitter | Key adapter between tools and Glass field. | Keep security posture aligned with Glass bridge rules. |
| personal-rag | Local memory | Portfolio memory substrate. | Add canonical source taxonomy and project-ID queries. |
| x-change | Learning + finance governance | Sharpest domain-specific system. | Harden auth/webhook edges and expand RewardToken model. |
| workspace-trust-auditor | Trust inspection | Needed meta-layer for both homes. | Consume canonical registry and emit benchmark scorecards. |
| Echoes | Multimodal assistant platform | Big, active, ambitious, harder to externally verify. | Produce "works today" capability matrix. |
| CascadeProjects | Multi-domain workspace platform | Main host for apps, MCP servers, shared components. | Generate authoritative subproject map. |
| hogsmade | Cascade-like workspace variant | Overlaps with CascadeProjects; likely mirror/fork/workspace variant. | Decide canonical/mirror/archive status. |
| Afloat | Cognitive assistant SaaS | Clear productized app with billing/auth posture. | Verify billing/auth lifecycle and MCP workflow path. |
| GRUFF python-prototype | Notebook/runtime bridge | Strong local geometry/notebook runtime. | Define relationship to GRID and Glass. |
| APIGuard | Resilience library | Practical reusable Python infrastructure. | Add adoption examples in x-change/Afloat-style services. |
| mcp-orchestration-language | Workflow DSL | Natural fit for MCP-heavy ecosystem. | Add real workflows and audit event sink. |
| constrained-signal-pipeline | Numeric signal utility | Small, clean, useful sidecar. | Stabilize fixtures and integrate with personal-rag. |
| python-craft | Python AI templates | Useful training/template substrate. | Clarify whether library, cookbook, or internal reference. |
| dep-mapper | Dependency intelligence | Good support utility. | Feed results into workspace-trust-auditor. |
| Vision | Screen-aware summarization | Useful UI/summary utility with some stubs. | Complete profile-based budget/summarization commands. |
| token-type-calculator | Visual token dashboard | Good small explanatory artifact. | Decide if internal demo or part of x-change/GRID vocabulary. |
| upwork-cli | Personal operations CLI | Useful but narrow. | Keep separate from core ecosystem; package if actively used. |
| ai-web-demo | Adaptive web demo | Mixed demo/control surface. | Decide whether to archive, productize, or absorb patterns. |
| roots/security | Host security tooling | Important but infrastructure-light. | Add runbooks, idempotent checks, and testable validations. |
| portfolio-control | Automation control plane | Correct concept, small current implementation. | Connect to registry, trusted commands, and audit reports. |

## Similarity Segments

### Segment A: Agent-First Orchestration and Distribution

Projects:

- GRID-main
- CascadeProjects
- Glass
- glass-server
- grid-server
- Afloat
- mcp-orchestration-language
- Echoes
- GRUFF python-prototype

Shared theme:

These projects coordinate agents, tools, sessions, workflows, and validation.
They are less about single-purpose apps and more about distributing work across
local services, MCP servers, UI surfaces, and policy engines.

Domain label:

Agent-first wide-stretched distribution and orchestration.

Recommended batch:

- establish shared integration contracts,
- define canonical payload schemas,
- add cross-project contract tests,
- generate a live system map.

### Segment B: Learning, Evidence, Finance, and Governance

Projects:

- x-change
- Glass
- glass-server
- token-type-calculator
- APIGuard
- Afloat

Shared theme:

These projects handle proof, reward, payment, trust, or rate-limited access.
x-change is the center of this segment because it models evidence and reward
state explicitly.

Domain label:

Learning, finance, evidence, and contract governance.

Recommended batch:

- define evidence payload lifecycle,
- connect Glass fixtures to x-change transitions,
- standardize auth/rate-limit handling,
- clarify token vocabulary across token-type-calculator, x-change, and GRID.

### Segment C: Trust, Security, Provenance, and Portfolio Control

Projects:

- workspace-trust-auditor
- portfolio-control
- roots/security
- APIGuard
- dep-mapper
- CascadeProjects docs

Shared theme:

The workspace is large enough that trust must be machine-readable. These
projects should answer: what is canonical, what changed, what is safe to run,
what is stale, what is duplicated, and what needs review?

Domain label:

Security, provenance, trust automation, and operator safety.

Recommended batch:

- create canonical registry,
- add repo status scorecards,
- classify duplicate paths,
- define trusted validation commands,
- export audit reports into personal-rag.

### Segment D: Knowledge, Memory, Signal Processing, and Summarization

Projects:

- personal-rag
- constrained-signal-pipeline
- Vision
- python-craft
- dep-mapper
- Echoes

Shared theme:

These projects ingest, transform, summarize, score, or structure knowledge.
They should form the cognitive substrate for the rest of the portfolio.

Domain label:

Local intelligence, memory, retrieval, summarization, and signal analysis.

Recommended batch:

- standardize source taxonomy,
- connect reports and session output into personal-rag,
- use constrained-signal-pipeline as a sidecar rather than a monolith,
- clarify which summarization work belongs in Vision versus personal-rag.

### Segment E: Spatial UI, Artifacts, and Operator Surfaces

Projects:

- Glass
- GRUFF python-prototype
- Vision
- glimpse-engine
- glimpse-artifact
- token-type-calculator
- workspace-trust-auditor dashboard

Shared theme:

These projects make state visible. They convert hidden state into spatial,
visual, compact, or inspectable forms.

Domain label:

Spatial cognition, visual inspection, artifact rendering, and operator UX.

Recommended batch:

- identify primary surfaces and avoid duplicating dashboards,
- let Glass own live agent-session space,
- let workspace-trust-auditor own portfolio health views,
- let GRUFF own notebook/manifest runtime visualization,
- let Vision own screen-aware summarization.

## Integration Surface

The strongest current integration graph is:

```text
Glass
  -> emits or displays live agent/session evidence
  -> glass-server writes bridge state
  -> x-change consumes evidence for reward-state proposals
  -> personal-rag indexes sessions, docs, and reports
  -> GRID validates, routes, scores, or enriches intelligence flows
  -> workspace-trust-auditor audits project and dependency posture
  -> portfolio-control turns safe checks into repeatable automation
```

Another emerging path:

```text
mcp-orchestration-language
  -> compiles workflow definitions
  -> calls MCP servers in CascadeProjects
  -> Afloat presents short user-facing workflows
  -> Glass visualizes agent/session state
  -> personal-rag stores durable run history
```

And a third support path:

```text
dep-mapper / APIGuard / roots-security
  -> feed workspace-trust-auditor
  -> produce risk and dependency reports
  -> become trusted inputs for portfolio-control
  -> become searchable evidence in personal-rag
```

## Canonical Domain Categorization

### GRID

Suggested domain:

Agent-first intelligence engine, validation framework, and local-first AI
infrastructure.

Reasoning:

GRID has the strongest evidence of being a central engine rather than a leaf
app. It should be categorized as the reasoning, scoring, validation, and
distribution core.

### Glass

Suggested domain:

Spatial agent work surface and co-presence environment.

Reasoning:

Glass is not primarily a chat app or dashboard. It is a visual field for live
agent work, bridge state, artifacts, and ceremony/session signals.

### x-change

Suggested domain:

Learning, evidence, reward governance, and finance boundary.

Reasoning:

x-change connects learning outcomes, evidence ledgers, reward lifecycle, and
Stripe confirmation. It should remain domain-specific and policy-driven.

### CascadeProjects

Suggested domain:

Large multi-domain hosting platform for applications, MCP servers, components,
and operational projects.

Reasoning:

CascadeProjects is a workspace platform, not a single product. Its value is
namespace organization, shared contracts, MCP tools, and cross-project
composition.

### Afloat

Suggested domain:

Productized cognitive assistant and lightweight workflow surface.

Reasoning:

Afloat has a clear user-facing task: help a user get past a context gate quickly.
It should use the ecosystem's backend capabilities without becoming the whole
ecosystem.

### personal-rag

Suggested domain:

Local memory and retrieval substrate.

Reasoning:

It should hold durable context, reports, session logs, project documentation,
and unresolved questions across the portfolio.

### workspace-trust-auditor

Suggested domain:

Portfolio trust, provenance, and security inspection.

Reasoning:

It maps local projects, dependency posture, secret-risk signals, and provenance.
It is the natural operator surface for workspace integrity.

### Echoes

Suggested domain:

Multimodal assistant research and orchestration platform.

Reasoning:

Echoes is broad and active. It should either become a clearly bounded platform
or donate mature pieces to GRID, Afloat, personal-rag, or Cascade MCP servers.

### GRUFF python-prototype

Suggested domain:

Notebook runtime, geometry workbench, and bridge-emitting local app.

Reasoning:

GRUFF owns manifest persistence, notebook events, heatmaps, and craft/bridge
outputs. It should not compete with GRID or Glass; it should connect to them.

### APIGuard

Suggested domain:

Reusable resilience library.

Reasoning:

It provides rate limiting, retries, circuit breaking, and structured logging.
That belongs under shared infrastructure.

## Infrastructure Gaps and Feature Calls

### 1. Canonical Portfolio Registry

Priority: critical  
Affected projects: all, especially CascadeProjects, hogsmade, canopy, roots,
apiguard, workspace-trust-auditor, personal-rag.

Current gap:

The filesystem contains duplicated or mirrored projects across both homes.
Without a canonical registry, tools cannot reliably determine source of truth.

Needed feature:

A machine-readable registry with:

- project ID,
- canonical path,
- mirror paths,
- archive status,
- repo URL,
- owner/domain,
- primary language,
- run/test commands,
- trust tier,
- integration consumers,
- source-of-truth direction.

### 2. Cross-Project Contract Tests

Priority: critical  
Affected projects: Glass, glass-server, x-change, personal-rag, GRID,
workspace-trust-auditor.

Current gap:

The ecosystem has many implicit contracts. The docs describe them, but the
portfolio needs fixture-based tests that fail when contracts drift.

Needed feature:

Small contract fixture suites for:

- Glass bridge payloads,
- glass-server write events,
- x-change evidence ingest,
- reward transition proposals,
- personal-rag report ingestion,
- GRID validation calls,
- workspace-trust-auditor project inventory output.

### 3. Shared Auth, Rate-Limit, and Request Safety Pattern

Priority: high  
Affected projects: x-change, Afloat, APIGuard, MCP servers.

Current gap:

Security posture varies by repo. x-change has concrete hardening needs around
failed-auth rate limiting and malformed webhook request handling.

Needed feature:

Shared request-boundary pattern:

- bounded body parser,
- malformed header handling,
- failed-auth rate limiting,
- constant-time token comparison,
- structured audit events,
- webhook signature validation rules,
- route-level limits.

APIGuard is a good candidate to become the shared implementation source.

### 4. Workspace Map Generator

Priority: high  
Affected projects: CascadeProjects, hogsmade, workspace-trust-auditor,
portfolio-control.

Current gap:

CascadeProjects is namespaced, but a human still has to inspect many paths to
understand apps, MCP servers, projects, components, docs, and generated output.

Needed feature:

A generated map with:

- apps,
- MCP servers,
- libraries,
- operational projects,
- docs,
- generated artifacts,
- nested git repos,
- mirrors,
- stale directories.

### 5. Automated Benchmark Scorecard

Priority: high  
Affected projects: workspace-trust-auditor, portfolio-control, personal-rag.

Current gap:

Benchmarking is currently manual. The same signals can be collected
automatically.

Needed feature:

A `portfolio scorecard` command that reports:

- last commit date,
- dirty state,
- test count,
- CI presence,
- lockfile presence,
- package metadata,
- docs presence,
- Docker/deploy posture,
- security markers,
- duplicate-path warnings,
- integration consumers,
- suggested next infrastructure fix.

### 6. External Capability Matrix for Large Projects

Priority: medium-high  
Affected projects: Echoes, GRID, CascadeProjects.

Current gap:

Large projects can look impressive but hard to evaluate unless they publish
"what works today" boundaries.

Needed feature:

Capability matrix:

- feature,
- command/API,
- status,
- tests,
- dependencies,
- known limits,
- owning module.

### 7. Registry-Backed personal-rag Ingestion

Priority: medium-high  
Affected projects: personal-rag, workspace-trust-auditor, portfolio-control.

Current gap:

personal-rag can ingest useful material, but needs canonical labels to avoid
confusing mirrors, archives, generated files, and live sources.

Needed feature:

Ingest rules based on registry project IDs and source types.

### 8. Domain Ownership Cleanup for Small Tools

Priority: medium  
Affected projects: constrained-signal-pipeline, dep-mapper, python-craft,
upwork-cli, token-type-calculator, ai-web-demo.

Current gap:

Small tools are useful but need explicit placement: internal utility,
packageable library, demo, archive, or product.

Needed feature:

A small-tool classification pass:

- keep and package,
- keep internal,
- merge into another repo,
- archive,
- turn into docs/example.

## Recommended Next Batches

### Batch 1: Portfolio Authority

Goal:

Make the workspace know what is canonical.

Projects:

- workspace-trust-auditor
- portfolio-control
- CascadeProjects
- personal-rag

Tasks:

- define project registry schema,
- record canonical and mirror paths,
- generate workspace map,
- make workspace-trust-auditor read the registry,
- ingest registry and reports into personal-rag.

### Batch 2: Glass to x-change Evidence Loop

Goal:

Prove the learning/evidence/finance loop end to end.

Projects:

- Glass
- glass-server
- x-change
- personal-rag

Tasks:

- define bridge evidence fixtures,
- test glass-server emits valid payloads,
- test x-change consumes payloads and proposes valid transitions,
- store evidence reports in personal-rag,
- document the full circuit.

### Batch 3: Security and Request Boundary Standardization

Goal:

Make local services safer and more consistent.

Projects:

- x-change
- APIGuard
- Afloat
- MCP servers
- roots/security

Tasks:

- harden x-change webhook parsing,
- add failed-auth limits,
- extract reusable request-boundary recipes,
- document shared webhook/auth/rate-limit rules,
- add service-level security checklists.

### Batch 4: MCP Workflow Orchestration

Goal:

Turn separate MCP servers into auditable workflows.

Projects:

- mcp-orchestration-language
- CascadeProjects MCP servers
- Afloat
- Glass
- workspace-trust-auditor

Tasks:

- write real workflow examples,
- validate them against server registries,
- execute dry-run plans,
- emit audit events,
- visualize outputs in Glass or workspace-trust-auditor.

### Batch 5: Productization and External Readiness

Goal:

Separate internal prototypes from externally understandable products.

Projects:

- Afloat
- Glass
- APIGuard
- GRID
- x-change

Tasks:

- publish quick starts,
- verify fresh install paths,
- run tests/lint/type checks,
- write launch checklists,
- identify demo data and real data boundaries.

## Opinionated Architecture Direction

The portfolio should be organized as layers:

```text
Layer 1: Host and registry
  CascadeProjects, portfolio-control, workspace registry

Layer 2: Trust and safety
  workspace-trust-auditor, roots/security, APIGuard

Layer 3: Intelligence and memory
  GRID, personal-rag, constrained-signal-pipeline, Vision

Layer 4: Runtime and orchestration
  MCP servers, mcp-orchestration-language, GRUFF python-prototype

Layer 5: Product surfaces
  Glass, Afloat, workspace-trust-auditor dashboard

Layer 6: Domain governance
  x-change, token/reward/evidence/payment policy
```

This structure prevents projects from competing for the same job. Each one has
a clear responsibility:

- GRID thinks and validates.
- Glass shows live work.
- personal-rag remembers.
- x-change governs rewards and payments.
- workspace-trust-auditor inspects trust.
- CascadeProjects hosts and connects.
- MCP orchestration moves work between tools.

## Immediate Top Todos

1. Create the canonical portfolio registry.
2. Add a generated workspace map.
3. Add Glass to x-change contract fixtures.
4. Harden x-change request boundaries.
5. Make workspace-trust-auditor emit benchmark scorecards.
6. Ingest scorecards and reports into personal-rag.
7. Clarify canonical versus mirror status for duplicated repos.
8. Produce current-capability matrices for GRID, Echoes, and CascadeProjects.
9. Add real workflows to mcp-orchestration-language.
10. Decide fate of small tools: package, internal utility, merge, or archive.

## Final Assessment

The work is strongest where it combines agent operations with visible state,
evidence, memory, and trust. That combination is uncommon and worth organizing
deliberately.

The main weakness is not lack of code. It is boundary pressure: many projects
are adjacent, duplicated, or conceptually overlapping. If those boundaries are
formalized, the portfolio becomes much easier to explain, operate, and extend.

The best next step is to turn the analysis itself into infrastructure:

- registry,
- scorecard,
- contract tests,
- integration map,
- searchable report history.

That would make future evaluation continuous instead of one-off.
