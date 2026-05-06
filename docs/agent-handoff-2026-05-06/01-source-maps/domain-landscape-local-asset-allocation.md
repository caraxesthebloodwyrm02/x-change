# Domain Landscape and Local Asset Allocation

Date: 2026-05-06  
Scope: `/home/irfankabir` and `/mnt/arch_data/home/caraxes`  
Mode: local inventory synthesis and domain allocation  
Prerequisites:

- `portfolio-inventory-benchmark.md`
- `directory-structure-consolidation-playbook.md`

## Purpose

This document reorganizes the local portfolio by real-world software-use
domains instead of by filesystem layout.

The goal is to help a human or agent understand:

- what social/use-case domains the workspace already covers,
- which local assets belong to each domain,
- where projects overlap across domains,
- which modalities are available for future analysis,
- which visual diagrams should be produced next.

The prior reports answered:

- what exists,
- what is strongest,
- where security and structure risks are,
- which directories need canonical authority.

This report answers:

- what real-world usage areas the assets map to,
- what the current domain landscape looks like,
- how to shift from text inventory into visual data diagrams.

## Executive Summary

The workspace is not only a developer sandbox. It already covers a wide social
software landscape:

- education and learning,
- finance, payments, and reward governance,
- AI agents and automation,
- data, memory, retrieval, and knowledge management,
- security, trust, provenance, and audit,
- productivity and personal operating systems,
- creative/spatial/media interfaces,
- career, marketplace, and professional operations,
- infrastructure, DevOps, and package/tooling layers,
- health, wellness, routines, and cognitive load,
- archives, seeds, and reusable templates.

The strongest cross-domain pattern is:

```text
AI agents + local memory + trust audit + visual workspace + evidence/payment governance
```

That combination places the portfolio in a modern trend area: local-first,
agent-assisted work systems with privacy, explainability, and workflow
instrumentation.

The highest-value domain clusters are:

1. AI agents and automation.
2. Data, memory, and knowledge infrastructure.
3. Education, evidence, and reward governance.
4. Security, trust, and provenance.
5. Productivity and personal operating systems.
6. Creative/spatial interfaces.

The most underdeveloped but visible domain is health and wellness. There are
routine, cognitive-load, and school/learning signals, but no fully separated
wellness product yet.

## Domain Model

The following domains are based on current digital usage trends and practical
software categories.

| Domain | Real-World Meaning | Typical Software Patterns |
|---|---|---|
| Education and Learning | Learning progress, tutoring, practice, assessment, evidence, student outcomes | LMS, tutors, notebooks, assessment tools, skill trackers |
| Finance, Banking, Wallet, and Payments | Money movement, rewards, invoices, payment events, exchange, tokens | Payment processors, ledgers, wallets, banking apps, reward systems |
| AI Agents and Automation | Proactive task execution, routing, workflows, MCP tools, agent orchestration | Agent runtimes, MCP servers, workflow engines, copilots |
| Data, Memory, and Knowledge | Search, retrieval, RAG, summarization, ingestion, indexing, datasets | RAG, data pipelines, personal knowledge bases, document intelligence |
| Security, Trust, and Provenance | Audit, policy, secrets, dependency posture, path authority, safety | Security scanners, provenance registries, trust dashboards |
| Productivity and Personal OS | Daily operations, context gates, routines, dashboards, planning | Productivity assistants, command centers, personal CRMs |
| Creative, Media, and Spatial UX | Visual surfaces, spatial workspaces, artifacts, diagrams, UI systems | Design tools, creative editors, spatial canvases, visual analytics |
| Health, Wellness, and Cognitive Load | Routine, mental load, self-regulation, reflection, habit support | Wellness apps, trackers, routine planners, load balancers |
| Career, Marketplace, and Professional Ops | Work acquisition, proposals, portfolio, consulting, market positioning | Proposal tools, job matching, portfolio sites, CRM |
| Infrastructure, DevOps, and Libraries | Shared packages, CI, package tooling, reusable libraries, local services | CLIs, SDKs, libraries, runners, deploy tooling |
| Governance, Policy, and Legal/Contracts | Rules, service contracts, consent, reward policy, user agreements | Policy engines, contract templates, compliance records |
| Archives, Templates, and Research Seeds | Historical work, reusable scaffolds, experiments, handoffs | Templates, archives, research folders, migration bundles |

## Domain Allocation Matrix

This matrix assigns major local assets to primary and secondary domains.

| Asset | Primary Domain | Secondary Domains | Notes |
|---|---|---|---|
| `GRID-main` | AI Agents and Automation | Data/Knowledge, Security/Trust, Infrastructure | Core intelligence and validation engine. |
| `Glass` | Creative, Media, and Spatial UX | AI Agents, Productivity, Education Evidence | Spatial co-presence surface for agent sessions. |
| `glass-server` | AI Agents and Automation | Infrastructure, Spatial UX | MCP bridge emitter for Glass. |
| `x-change` | Education and Learning | Finance/Payments, Governance, Trust | Reward/evidence/payment lifecycle. |
| `personal-rag` | Data, Memory, and Knowledge | Productivity, AI Agents, Trust | Local memory/index substrate. |
| `workspace-trust-auditor` | Security, Trust, and Provenance | Productivity, Infrastructure, Data | Read-only audit and workspace map surface. |
| `Afloat` | Productivity and Personal OS | AI Agents, Career, Payments, Wellness | Cognitive assistant with SaaS/payment posture. |
| `Echoes` | AI Agents and Automation | Data/Knowledge, Creative/Media, Security | Broad multimodal assistant/orchestration platform. |
| `CascadeProjects` | Infrastructure, DevOps, and Libraries | AI Agents, Creative UX, Security, Data | Multi-domain host for apps, MCP servers, components. |
| `hogsmade` | Infrastructure / Mirror Candidate | Creative UX, AI Agents | Cascade-like overlapping workspace; classify before relying on it. |
| `GRUFF python-prototype` | Education and Learning | Creative/Spatial UX, Data, Productivity | Notebook/geometry runtime and bridge emitter. |
| `APIGuard` | Infrastructure, DevOps, and Libraries | Security, Finance, AI Agents | Rate-limit/retry/circuit-breaker library. |
| `mcp-orchestration-language` | AI Agents and Automation | Infrastructure, Productivity | Workflow DSL for MCP-heavy systems. |
| `portfolio-control` | Security, Trust, and Provenance | Infrastructure, DevOps | Control plane for trusted repo automation. |
| `roots/security` | Security, Trust, and Provenance | Infrastructure | Host guardrails and hardening scripts. |
| `dep-mapper` | Data, Memory, and Knowledge | Security, Infrastructure | Dependency intelligence utility. |
| `python-craft` | Education and Learning | Data/Knowledge, Infrastructure | Python AI template/training substrate. |
| `Vision` | Data, Memory, and Knowledge | Creative/Media, Accessibility/Productivity | Screen-aware summarization utilities. |
| `constrained-signal-pipeline` | Data, Memory, and Knowledge | AI Agents, Productivity | Numeric signal-processing sidecar. |
| `token-type-calculator` | Finance, Banking, Wallet, and Payments | Governance, Creative UX, AI Agents | Token category and value/asymmetry visualization. |
| `upwork-cli` | Career, Marketplace, and Professional Ops | Productivity, Finance | Proposal/profile/job operations CLI. |
| `ai-web-demo` | AI Agents and Automation | Creative UX, Data | Adaptive web demo/control surface. |
| `assistive-agreement-contracts` | Governance, Policy, and Legal/Contracts | Productivity, Trust, Wellness | Agreement/contract-oriented support asset. |
| `grove` | Archives, Templates, and Research Seeds | Creative, Data, Education | Workspace/archive collection; classify carefully. |
| `seed` | Archives, Templates, and Research Seeds | Education, Creative, Infrastructure | Templates and historical seeds. |
| `HANDOFF` | Archives, Templates, and Research Seeds | Data/Knowledge, Productivity | Handoff bundles and transfer artifacts. |
| `.claude` | Productivity and Personal OS | AI Agents, Tool State, Memory | Tool/runtime state and user agent context. |
| `.codex` | Productivity and Personal OS | AI Agents, Tool State, Memory | Codex skills/memories/plugins; tool-owned. |
| `.caraxes` | Security/Trust or Runtime Ops | Registry, Logs, Local Runtime | Local runtime/log/registry area; do not move casually. |
| `.afloat` | Productivity and Personal OS | Workflow History, AI Agents | Afloat local state/history. |

## Domain Sections

## 1. Education and Learning

### Real-World Usage

Education software is shifting from static learning management toward:

- adaptive tutoring,
- skill evidence,
- project-based assessment,
- notebook and artifact workflows,
- measurable student outcomes,
- learning-to-earning or reward-linked systems.

### Local Assets

Primary assets:

- `/home/irfankabir/x-change`
- `/home/irfankabir/gruff/workspace/python-prototype`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main`
- `/mnt/arch_data/home/caraxes/roots/python-craft`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/Vision`

Secondary assets:

- Glass
- personal-rag
- token-type-calculator
- seed/templates
- GRUFF racks/learning

### Current Landscape Read

x-change is the most explicit education-domain project because it models reward
state, evidence, student acknowledgement, and policy boundaries. GRUFF
python-prototype is a learning/workbench runtime. GRID can serve as an
intelligence layer for learning diagnostics. personal-rag can store learning
history. Glass can display evidence and work-session state.

### Missing or Underbuilt Pieces

- learner profile model,
- student-facing dashboard,
- educator/admin review surface,
- rubric/evidence schema,
- course/module organization,
- longitudinal progress graph,
- privacy model for student evidence.

### Visual Diagram Candidates

- learning evidence lifecycle,
- x-change reward-state timeline,
- learner evidence graph,
- Glass session to x-change transition map,
- education-domain architecture stack.

## 2. Finance, Banking, Wallet, and Payments

### Real-World Usage

Modern finance software patterns include:

- wallets and ledgers,
- payment provider webhooks,
- subscription billing,
- reward systems,
- trust and fraud controls,
- transaction audit trails,
- tokenized value representations.

### Local Assets

Primary assets:

- `/home/irfankabir/x-change`
- `/home/irfankabir/canopy/afloat`
- `/home/irfankabir/canopy/token-type-calculator`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/apiguard`

Secondary assets:

- workspace-trust-auditor
- roots/security
- portfolio-control
- assistive-agreement-contracts

### Current Landscape Read

x-change is the main finance-adjacent asset because it uses Stripe webhook
confirmation as part of a reward lifecycle. Afloat has subscription/billing
architecture. APIGuard is relevant because finance-adjacent services require
rate limiting and resilience. token-type-calculator captures value asymmetry
and token classification, which could become part of a wallet/reward
vocabulary.

### Missing or Underbuilt Pieces

- general ledger model,
- reconciliation report,
- payment audit dashboard,
- wallet/account abstraction,
- refund/dispute path,
- webhook replay tooling,
- risk/fraud scoring,
- signed event receipt format.

### Visual Diagram Candidates

- Stripe event boundary map,
- reward-to-payment state diagram,
- payment trust boundary diagram,
- token value taxonomy chart,
- ledger/reconciliation swimlane.

## 3. AI Agents and Automation

### Real-World Usage

The current software trend is moving from passive tools to proactive agents:

- agents call tools,
- workflows span multiple services,
- local context matters,
- MCP servers expose capabilities,
- humans need auditability and rollback.

### Local Assets

Primary assets:

- GRID-main
- CascadeProjects MCP servers
- glass-server
- mcp-orchestration-language
- Afloat
- Echoes
- workspace-trust-auditor
- `.claude`
- `.codex`

Secondary assets:

- personal-rag
- Glass
- APIGuard
- portfolio-control
- dep-mapper

### Current Landscape Read

This is the strongest overall portfolio domain. GRID, MCP servers,
mcp-orchestration-language, Afloat, Glass, and the agent tool state together
form a local agent operating environment. The critical challenge is making
automation auditable, safe, and visually understandable.

### Missing or Underbuilt Pieces

- canonical MCP capability registry,
- workflow execution ledger,
- rollback plans for agent actions,
- cross-tool permission model,
- agent run scorecards,
- visual workflow trace,
- shared event envelope.

### Visual Diagram Candidates

- MCP server capability map,
- agent workflow DAG,
- tool-call trust boundary diagram,
- automation lifecycle swimlane,
- local agent OS layer diagram.

## 4. Data, Memory, and Knowledge

### Real-World Usage

Knowledge software is shifting toward:

- local RAG,
- personal memory,
- source-grounded summaries,
- searchable work history,
- dataset lineage,
- dependency intelligence,
- multimodal indexing.

### Local Assets

Primary assets:

- personal-rag
- constrained-signal-pipeline
- Vision
- dep-mapper
- Echoes
- GRID-main

Secondary assets:

- workspace-trust-auditor
- portfolio reports
- HANDOFF
- session_transcripts
- `.claude/memory`
- `.codex/memories`

### Current Landscape Read

personal-rag is the anchor. The portfolio already produces the exact artifacts
a knowledge system wants: reports, handoffs, session transcripts, code docs,
project inventories, and audit findings. The gap is source taxonomy and
canonical project identity.

### Missing or Underbuilt Pieces

- canonical source taxonomy,
- ingestion priority rules,
- mirror/archive awareness,
- report index,
- diagram extraction,
- stale-context detection,
- knowledge graph export.

### Visual Diagram Candidates

- source ingestion map,
- memory topology graph,
- project-to-report graph,
- dependency map,
- stale versus active source heatmap.

## 5. Security, Trust, and Provenance

### Real-World Usage

Security software is no longer only vulnerability scanning. For agentic
workspaces it also includes:

- provenance,
- trusted command manifests,
- dependency posture,
- secret-risk signals,
- workspace authority,
- safe automation policies.

### Local Assets

Primary assets:

- workspace-trust-auditor
- portfolio-control
- roots/security
- APIGuard
- x-change security boundaries
- Glass bridge security surface

Secondary assets:

- dep-mapper
- CascadeProjects security docs
- `.caraxes/registry`
- AGENTS/CLAUDE instruction files

### Current Landscape Read

This domain is already strongly represented. The next move is to unify security
and structure: path authority, canonical registry, trusted commands, and
cross-repo scorecards should be treated as security controls.

### Missing or Underbuilt Pieces

- canonical registry enforcement,
- per-project trust tier,
- trusted command manifest,
- generated security scorecard,
- path authority checker,
- mirror drift detector,
- signed audit reports.

### Visual Diagram Candidates

- trust tier matrix,
- attack surface by project,
- path authority graph,
- mirror drift graph,
- dependency risk heatmap.

## 6. Productivity and Personal Operating System

### Real-World Usage

Personal productivity has shifted from todo lists to operating systems:

- context gates,
- daily briefs,
- routines,
- local memory,
- work-session visualization,
- workflow automation,
- personal dashboards.

### Local Assets

Primary assets:

- Afloat
- Glass
- personal-rag
- workspace-trust-auditor
- `.claude`
- `.codex`
- `.afloat`
- GRUFF workspace

Secondary assets:

- upwork-cli
- mcp-orchestration-language
- Vision
- session_transcripts
- HANDOFF

### Current Landscape Read

The portfolio has a strong productivity story: Afloat helps with context gates,
Glass visualizes work sessions, personal-rag remembers, and
workspace-trust-auditor inspects the workspace. The missing piece is a unified
daily command surface.

### Missing or Underbuilt Pieces

- daily operator dashboard,
- personal command center,
- task/workflow queue,
- context-switch ledger,
- focus/load state,
- unified notification surface,
- calendar/email integration if desired later.

### Visual Diagram Candidates

- daily workflow map,
- context gate flow,
- personal OS dashboard wireframe,
- agent/human handoff diagram,
- routine and memory loop.

## 7. Creative, Media, and Spatial UX

### Real-World Usage

Creative software increasingly overlaps with productivity and AI:

- spatial canvases,
- visual work maps,
- generated artifacts,
- design systems,
- screen-aware summaries,
- visual analytics,
- multimodal workflows.

### Local Assets

Primary assets:

- Glass
- GRUFF python-prototype
- Vision
- glimpse-engine
- glimpse-artifact
- token-type-calculator
- design-system roots

Secondary assets:

- Echoes
- workspace-trust-auditor dashboard
- CascadeProjects Applications
- ai-web-demo

### Current Landscape Read

Glass is the strongest creative/spatial product. GRUFF and Vision provide
adjacent spatial/screen-aware functionality. The opportunity is to treat visual
diagrams as first-class generated artifacts, not screenshots after the fact.

### Missing or Underbuilt Pieces

- shared diagram schema,
- visual export pipeline,
- dashboard design language,
- canvas-to-data contract,
- diagram versioning,
- artifact gallery,
- visual regression checks.

### Visual Diagram Candidates

- domain landscape map,
- project cluster graph,
- spatial session map,
- UI surface ownership map,
- artifact lifecycle diagram.

## 8. Health, Wellness, and Cognitive Load

### Real-World Usage

Wellness software is moving toward:

- mental load tracking,
- habit loops,
- routines,
- reflection,
- focus management,
- burnout prevention,
- self-regulation support.

### Local Assets

Primary or near-primary assets:

- Afloat
- `.claude/maintenance/routines`
- `.claude/scheduler`
- GRUFF racks/routines
- seed/archive mental-load-balancer

Secondary assets:

- personal-rag
- Glass
- Vision
- Echoes

### Current Landscape Read

This is visible but not fully productized. Afloat's context-gate framing and
routine/scheduler folders suggest a wellness/cognitive-load thread. However,
there is no single canonical wellness app yet.

### Missing or Underbuilt Pieces

- cognitive-load model,
- routine dashboard,
- reflection capture,
- trend graph,
- privacy boundary,
- wellness-specific agent constraints,
- "do not over-automate" policy.

### Visual Diagram Candidates

- cognitive load loop,
- routine adherence timeline,
- context-gate stress map,
- wellness data boundary diagram,
- personal development graph.

## 9. Career, Marketplace, and Professional Operations

### Real-World Usage

Career and marketplace tools include:

- profile management,
- proposal drafting,
- job matching,
- portfolio evidence,
- pricing,
- client communication,
- professional reputation.

### Local Assets

Primary assets:

- upwork-cli
- Afloat
- workspace-trust-auditor
- portfolio reports
- APIGuard as packageable proof
- GRID and Glass as portfolio showcase assets

Secondary assets:

- x-change reward/payment model,
- personal-rag for proposal memory,
- token-type-calculator for value framing,
- assistive-agreement-contracts.

### Current Landscape Read

upwork-cli is the explicit career tool. The broader portfolio can become strong
professional evidence if it is organized into domains, diagrams, and scorecards.

### Missing or Underbuilt Pieces

- portfolio showcase map,
- project one-pagers,
- proposal evidence snippets,
- market-positioning taxonomy,
- case study generator,
- pricing model,
- client-safe demo bundle.

### Visual Diagram Candidates

- portfolio-to-market map,
- project proof matrix,
- client offering tree,
- proposal evidence graph,
- revenue path diagram.

## 10. Infrastructure, DevOps, and Libraries

### Real-World Usage

Infrastructure software supports everything else:

- shared libraries,
- local services,
- CI,
- package workflows,
- runners,
- MCP servers,
- deployment configs,
- resilience utilities.

### Local Assets

Primary assets:

- CascadeProjects
- APIGuard
- roots/*
- Components/shared-*
- MCP servers
- portfolio-control
- workspace-trust-auditor
- actions-runner

Secondary assets:

- GRUFF workspace
- package scripts
- Dockerfiles
- Makefiles
- CI workflows

### Current Landscape Read

Infrastructure is strong but scattered. CascadeProjects and roots are the main
infrastructure spaces. The biggest improvement is canonical ownership and
generated maps.

### Missing or Underbuilt Pieces

- shared service catalog,
- package ownership map,
- CI command registry,
- runner policy,
- dependency update policy,
- generated infrastructure diagram,
- deploy/runtime inventory.

### Visual Diagram Candidates

- service catalog,
- package dependency graph,
- CI workflow map,
- runtime topology,
- canonical root map.

## 11. Governance, Policy, and Legal/Contracts

### Real-World Usage

Governance software covers:

- user agreements,
- consent,
- policy decisions,
- service contracts,
- audit records,
- reward rules,
- automation limits.

### Local Assets

Primary assets:

- x-change policy docs
- assistive-agreement-contracts
- Echoes consent license posture
- portfolio-control
- workspace-trust-auditor

Secondary assets:

- AGENTS/CLAUDE files
- roots/security
- APIGuard
- token-type-calculator

### Current Landscape Read

Governance appears across multiple projects rather than one central repo.
x-change is the best operational policy engine. assistive-agreement-contracts
looks like the most direct contract-domain asset.

### Missing or Underbuilt Pieces

- central policy registry,
- consent/audit event format,
- contract template catalog,
- automation permission tiers,
- human approval workflow,
- machine-readable policy docs.

### Visual Diagram Candidates

- policy decision tree,
- consent flow,
- reward governance map,
- automation approval ladder,
- contract lifecycle diagram.

## 12. Archives, Templates, and Research Seeds

### Real-World Usage

Archives and templates are important when they are searchable without confusing
active work:

- reusable scaffolds,
- historical context,
- handoff records,
- migration traces,
- experimental prototypes.

### Local Assets

Primary assets:

- `/home/irfankabir/archive`
- `/home/irfankabir/seed`
- `/mnt/arch_data/home/caraxes/seed`
- `/home/irfankabir/HANDOFF`
- `/mnt/arch_data/home/caraxes/HANDOFF`
- Grove archive folders
- Cascade Documentation/archive

Secondary assets:

- session_transcripts
- reports
- `.claude` and `.codex` memories

### Current Landscape Read

Archives are useful but visually mixed with active work. They need indexing and
exclusion rules, not deletion.

### Missing or Underbuilt Pieces

- archive index,
- active/archive flag,
- template catalog,
- handoff summary index,
- retention policy,
- search filters,
- import path into personal-rag.

### Visual Diagram Candidates

- archive timeline,
- seed/template taxonomy,
- handoff lineage map,
- active versus archive split,
- historical project evolution diagram.

## Cross-Domain Overlap Map

Some assets are intentionally multi-domain. These should be treated as bridges,
not as classification mistakes.

| Bridge Asset | Domain 1 | Domain 2 | Why It Bridges |
|---|---|---|---|
| x-change | Education | Finance | Learning evidence triggers reward/payment governance. |
| Glass | AI Agents | Creative/Spatial UX | Agent session state becomes a visual field. |
| personal-rag | Data/Memory | Productivity | Work history becomes searchable operational context. |
| workspace-trust-auditor | Security/Trust | Productivity | Workspace safety becomes an operator dashboard. |
| Afloat | Productivity | AI Agents | Context gates are handled through LLM/tool workflows. |
| GRID | AI Agents | Data/Knowledge | Intelligence engine uses scoring, routing, and validation. |
| APIGuard | Infrastructure | Security | Service resilience is also request-safety control. |
| mcp-orchestration-language | AI Agents | Infrastructure | Workflow language compiles tool/service calls. |
| token-type-calculator | Finance | Creative UX | Value/token asymmetry becomes inspectable visually. |
| GRUFF python-prototype | Education | Spatial UX | Notebook/runtime state can be visualized and bridged. |

## Domain Strength Ranking

| Rank | Domain | Current Strength | Why |
|---:|---|---|---|
| 1 | AI Agents and Automation | Very strong | GRID, MCP servers, Glass bridge, Afloat, Echoes, orchestration DSL. |
| 2 | Data, Memory, and Knowledge | Strong | personal-rag, Vision, dep-mapper, constrained-signal-pipeline, reports. |
| 3 | Security, Trust, and Provenance | Strong | workspace-trust-auditor, portfolio-control, roots/security, APIGuard. |
| 4 | Education and Learning | Strong emerging | x-change, GRUFF, python-craft, GRID, evidence model. |
| 5 | Productivity and Personal OS | Strong emerging | Afloat, Glass, personal-rag, workspace-trust-auditor, tool state. |
| 6 | Creative, Media, and Spatial UX | Strong emerging | Glass, GRUFF, Vision, glimpse assets, token visualizer. |
| 7 | Infrastructure, DevOps, and Libraries | Strong but scattered | CascadeProjects, roots, APIGuard, MCP servers. |
| 8 | Finance, Banking, Wallet, and Payments | Medium | x-change and Afloat exist, but ledger/wallet surfaces are early. |
| 9 | Governance, Policy, and Contracts | Medium | x-change and agreement assets exist; central policy registry missing. |
| 10 | Career and Marketplace Ops | Medium-light | upwork-cli exists; portfolio proof system not yet assembled. |
| 11 | Health, Wellness, and Cognitive Load | Light but visible | routines and context-gate assets exist; no canonical app yet. |
| 12 | Archives, Templates, and Research Seeds | Useful but messy | Many assets exist; needs indexing and exclusion discipline. |

## Modality Shift Plan

The next phase should convert this text landscape into visual data artifacts.

### Modality 1: Domain Matrix

Purpose:

Show assets by domain and secondary domain.

Best format:

- table heatmap,
- CSV/JSON source,
- Mermaid quadrant or graph,
- dashboard grid.

Suggested data fields:

```json
{
  "asset": "x-change",
  "canonical_path": "/home/irfankabir/x-change",
  "primary_domain": "Education and Learning",
  "secondary_domains": ["Finance", "Governance", "Trust"],
  "maturity": "emerging",
  "diagram_priority": "high"
}
```

### Modality 2: Network Graph

Purpose:

Show projects as nodes and domains as clusters.

Best format:

- Mermaid graph,
- Graphviz DOT,
- Cytoscape-compatible JSON,
- D3 force graph.

Useful edges:

- `belongs_to_domain`,
- `bridges_domain`,
- `consumes_evidence_from`,
- `indexes`,
- `audits`,
- `orchestrates`,
- `visualizes`.

### Modality 3: Sankey Flow

Purpose:

Show how real-world domains flow into project layers.

Example:

```text
Education -> x-change -> Glass evidence -> personal-rag -> workspace-trust-auditor
AI Agents -> GRID -> MCP servers -> Glass/Afloat
Security -> APIGuard -> x-change/Afloat/MCP servers
```

### Modality 4: Treemap

Purpose:

Show workspace area by domain, project family, and canonical/mirror/archive
status.

Best after:

- registry exists,
- file counts and repo sizes are collected,
- canonical paths are settled.

### Modality 5: Timeline

Purpose:

Show project evolution by commit date, handoff date, and report generation.

Useful for:

- understanding active versus dormant projects,
- seeing domain momentum,
- planning cleanup batches.

### Modality 6: Risk/Gap Heatmap

Purpose:

Show domains by maturity and missing infrastructure.

Axes:

- domain strength,
- security exposure,
- integration complexity,
- organization risk,
- product clarity.

## Diagram Data Seed

This seed can become JSON/YAML for diagram generation.

```yaml
domains:
  education:
    label: Education and Learning
    assets:
      - x-change
      - gruff-python-prototype
      - python-craft
      - GRID-main
      - Vision
  finance:
    label: Finance, Banking, Wallet, and Payments
    assets:
      - x-change
      - Afloat
      - token-type-calculator
      - APIGuard
  ai_agents:
    label: AI Agents and Automation
    assets:
      - GRID-main
      - CascadeProjects-MCPServers
      - glass-server
      - mcp-orchestration-language
      - Afloat
      - Echoes
      - workspace-trust-auditor
  data_memory:
    label: Data, Memory, and Knowledge
    assets:
      - personal-rag
      - constrained-signal-pipeline
      - Vision
      - dep-mapper
      - Echoes
      - GRID-main
  security_trust:
    label: Security, Trust, and Provenance
    assets:
      - workspace-trust-auditor
      - portfolio-control
      - roots-security
      - APIGuard
      - x-change
      - Glass
  productivity:
    label: Productivity and Personal OS
    assets:
      - Afloat
      - Glass
      - personal-rag
      - workspace-trust-auditor
      - GRUFF
  creative_spatial:
    label: Creative, Media, and Spatial UX
    assets:
      - Glass
      - GRUFF
      - Vision
      - glimpse-engine
      - glimpse-artifact
      - token-type-calculator
  wellness:
    label: Health, Wellness, and Cognitive Load
    assets:
      - Afloat
      - claude-routines
      - gruff-routines
      - mental-load-balancer
  career:
    label: Career, Marketplace, and Professional Ops
    assets:
      - upwork-cli
      - Afloat
      - workspace-trust-auditor
      - portfolio-reports
  infrastructure:
    label: Infrastructure, DevOps, and Libraries
    assets:
      - CascadeProjects
      - APIGuard
      - roots
      - shared-components
      - MCPServers
      - portfolio-control
  governance:
    label: Governance, Policy, and Legal/Contracts
    assets:
      - x-change
      - assistive-agreement-contracts
      - Echoes
      - portfolio-control
      - workspace-trust-auditor
  archives:
    label: Archives, Templates, and Research Seeds
    assets:
      - archive
      - seed
      - HANDOFF
      - Grove
      - session-transcripts
```

## Recommended Visual Artifacts to Produce Next

### 1. Domain Cluster Graph

High value because it shows the whole landscape quickly.

Nodes:

- domains,
- assets,
- bridge assets.

Edges:

- primary domain,
- secondary domain,
- integration flow.

### 2. Asset-by-Domain Heatmap

High value because it shows concentration and gaps.

Rows:

- local assets.

Columns:

- domains.

Cell values:

- primary,
- secondary,
- future fit,
- no fit.

### 3. Integration Sankey

High value because it shows how work moves.

Flows:

- AI Agents -> GRID -> MCP -> Glass/Afloat
- Education -> x-change -> Stripe/evidence -> personal-rag
- Security -> workspace-trust-auditor -> portfolio-control

### 4. Domain Maturity Radar

High value for planning.

Axes:

- product clarity,
- engineering maturity,
- integration gravity,
- monetization readiness,
- security readiness,
- visual readiness.

### 5. Canonical Path Treemap

High value after registry work.

Shows:

- active,
- mirror,
- archive,
- generated,
- tool-state.

## Recommended Next Work Order

1. Convert this document's domain allocation into `domain-assets.yaml`.
2. Add canonical paths and mirror status from the consolidation playbook.
3. Generate a Mermaid domain cluster graph.
4. Generate a CSV heatmap source.
5. Generate a Graphviz or Cytoscape network graph.
6. Create a visual report page that embeds the diagrams.
7. Feed the resulting visual artifacts into personal-rag.

## Agent Instructions for Reproduction

An agent reproducing this domain allocation should:

1. Read the portfolio benchmark report.
2. Read the consolidation playbook.
3. Run read-only marker discovery across both homes.
4. Exclude generated/tool-state directories unless the task explicitly includes
   them.
5. Assign each asset one primary domain and zero or more secondary domains.
6. Mark bridge assets that connect multiple domains.
7. Preserve canonical-path uncertainty where mirrors exist.
8. Generate diagram-ready YAML or JSON.
9. Do not move directories as part of this pass.
10. Store generated docs and diagrams in a predictable reports/docs namespace.

## Bottom Line

The local asset landscape is strongest where it combines:

- AI agents,
- local memory,
- visual work surfaces,
- trust/security,
- learning evidence,
- payment/reward governance.

That is the core thesis for the visual analysis phase.

The next deliverable should be a diagram-data file plus rendered diagrams, not
another prose-only report.
