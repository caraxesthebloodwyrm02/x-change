# Buried Assets Resurfacing Inventory

Date: 2026-05-06  
Scope: `/home/irfankabir` and `/mnt/arch_data/home/caraxes`  
Mode: filesystem/name/marker discovery only  
Explicitly out of scope: git navigation, git ranking, branch analysis, commit history

## Purpose

This pass inventories deeply buried local assets that may have high standalone
value but are currently overshadowed by placement inside archives, nested
workspaces, dot-tool state, old handoff bundles, or larger umbrella systems.

The goal is to identify candidates worth resurfacing into the current top-level
infrastructure as:

- standalone projects,
- reusable modules,
- tools,
- templates,
- visual analysis inputs,
- contract/governance assets,
- personal OS routines,
- security guardrails,
- domain-specific libraries.

This is not a migration plan. It is a candidate catalog for resurfacing review.

## Method

This pass intentionally did not use git history or git status as ranking
signals. Discovery was based on:

- names of directories and files,
- README and package marker presence,
- nested placement,
- executable-looking scripts,
- docs that describe product value,
- reusable template or skill structure,
- domain relevance to current top-level systems,
- signs of tests, demos, APIs, or structured configs.

Excluded by default:

- `node_modules`,
- `.git`,
- `.cache`,
- `.config`,
- `.local`,
- `.venv`,
- `__pycache__`,
- `dist`,
- `build`,
- `.next`,
- package-manager module caches,
- editor extension vendor content,
- action runner internals.

## Executive Summary

The strongest buried assets are not random scraps. Several are coherent systems
that got hidden under archive or seed paths:

1. `Atmosphere/Arcade` is a full AI terminal/product prototype with safety,
   multilingual interaction, terminal tooling, TUI work, learning companion
   pieces, and deployment docs.
2. `Atmosphere/Reverb`, `Delay`, and `Routing` form a spatial/audio/emotion
   stack that maps well to Glass, GRUFF, Vision, and future visual analytics.
3. `network-visualizer-python` is directly relevant to the requested visual
   diagram phase.
4. `Coinbase_from_zip` is a surprisingly complete finance/portfolio/security
   system that could inform x-change, portfolio-safety-lens, or finance-domain
   tooling.
5. `mental-load-balancer` is the strongest buried wellness/productivity asset.
6. `claude-cursor-integration-bridge` and `development-contract.md` are
   high-value governance/integration templates.
7. Old audit/consolidation docs already contain reusable inventory logic and
   cross-tool matrices.
8. Root-level scripts contain many useful operations that should be curated into
   a command catalog instead of staying as an unindexed scripts pile.

The main recommendation: create a `resurfacing-candidates.yaml` registry and
promote selected candidates into current infrastructure through documentation
and adapters first, not moves.

## Resurfacing Tiers

| Tier | Meaning | Action |
|---|---|---|
| Tier 1 | High-value, coherent, relevant now | Create review card and promotion plan |
| Tier 2 | Strong component, needs extraction | Extract pattern/module after inspection |
| Tier 3 | Useful reference/template | Index and link from current docs |
| Tier 4 | Historical/contextual | Archive-index only |
| Hold | Risky or unclear | Do not promote until reviewed |

## Tier 1 Candidates

### 1. Atmosphere Arcade

Path:

`/home/irfankabir/seed/archive/Atmosphere/Arcade`

Also mirrored under:

`/mnt/arch_data/home/caraxes/seed/archive/Atmosphere/Arcade`

Observed signals:

- extensive README,
- API docs,
- deployment docs,
- security implementation docs,
- TUI docs,
- tests,
- Docker compose,
- safety monitor,
- sandbox config,
- terminal/TUI components,
- learning companion modules,
- multilingual AI terminal positioning.

Why it is a buried gem:

This is not just a loose demo. It reads like a full product prototype: AI
terminal, natural language commands, multilingual interaction, real file access,
sandboxing, moderation, human review, performance testing, and deployment
paths. It overlaps with Glass, Afloat, workspace-trust-auditor, and the MCP
server ecosystem.

Resurfacing value:

- could become a historical predecessor or component source for Afloat/Glass,
- terminal/TUI ideas could support local agent operating system work,
- safety/sandbox patterns can feed security guardrails,
- learning companion pieces can feed x-change education flows.

Risks:

- archive placement suggests possible staleness,
- likely contains obsolete assumptions,
- needs security review before any runtime use,
- may include placeholder or old API patterns.

Recommended action:

Create an `Arcade resurfacing review` with four extraction tracks:

1. terminal/TUI interaction patterns,
2. safety/sandbox design,
3. learning companion modules,
4. deployment and monitoring docs.

Do not run it as-is before a security and dependency pass.

### 2. Atmosphere Reverb

Path:

`/home/irfankabir/seed/archive/Atmosphere/Reverb`

Also mirrored under:

`/mnt/arch_data/home/caraxes/seed/archive/Atmosphere/Reverb`

Observed signals:

- spatial audio platform README,
- HRTF/binaural rendering concepts,
- Doppler and distance attenuation,
- visualization tools,
- emotional spatial positioning,
- services and model structure,
- demos and tests.

Why it is a buried gem:

This project connects audio, emotion, spatial positioning, and visualization.
That is highly relevant to Glass-style spatial interfaces and future visual
analysis. It also has a conceptual bridge to the "resonance" vocabulary already
present in GRID and other systems.

Resurfacing value:

- visual/spatial metaphor source for Glass,
- audio/emotion model for wellness and focus tools,
- diagram/visualization component ideas,
- possible inspiration for signal-space views in GRID.

Risks:

- README contains visible merge-conflict markers, so the archive needs cleanup,
- current runtime quality is unknown,
- may depend on old audio libraries.

Recommended action:

Promote as a concept/reference first. Extract vocabulary, visual diagrams, and
model ideas before code.

### 3. Atmosphere Delay

Path:

`/home/irfankabir/seed/archive/Atmosphere/Delay`

Also mirrored under:

`/mnt/arch_data/home/caraxes/seed/archive/Atmosphere/Delay`

Observed signals:

- README describing tempo-synced delay,
- emotion-based processing,
- tactile feedback,
- tests and demos,
- knowledge graph file.

Why it is a buried gem:

Delay is a compact audio/emotion primitive. It may be more extractable than the
larger Reverb/Arcade systems.

Resurfacing value:

- small model for "signal delay" visualizations,
- emotional/tactile mapping concepts for wellness tooling,
- reference module for future creative media experiments.

Risks:

- likely prototype-level implementation,
- not directly aligned to current core infrastructure unless framed as a
  visualization/signal metaphor.

Recommended action:

Index under creative/spatial and wellness. Extract the emotion-to-parameter
table for future visual data diagrams.

### 4. Atmosphere Routing

Path:

`/home/irfankabir/seed/archive/Atmosphere/Routing`

Also mirrored under:

`/mnt/arch_data/home/caraxes/seed/archive/Atmosphere/Routing`

Observed signals:

- acoustic routing system README,
- 3D visualization,
- route optimization,
- REST API service,
- pulse propagation,
- emotional path optimization,
- Arcade integration references.

Why it is a buried gem:

The routing idea maps directly onto current needs: graph routing, agent
workflow routing, visual flow, and path optimization. It may be conceptually
useful for mcp-orchestration-language, GRID, and visual graph generation.

Resurfacing value:

- graph routing metaphors for agent workflows,
- route scoring for domain maps,
- pulse propagation diagrams,
- spatial path optimization concepts.

Risks:

- README contains visible merge-conflict markers,
- may mix metaphor and implementation heavily,
- needs cleanup before promotion.

Recommended action:

Promote as a model library candidate only after conflict-marker cleanup and
small smoke review.

### 5. Network Visualizer Python

Path:

`/mnt/arch_data/home/caraxes/seed/archive/Atmosphere/network-visualizer-python`

Likely related path:

`/home/irfankabir/seed/archive/Atmosphere/network-visualizer-python`

Observed signals:

- package-style structure,
- NetworkX-style feature set,
- multiple layouts,
- centrality/community/path metrics,
- export formats,
- CLI and web interface claims,
- plugin architecture.

Why it is a buried gem:

This directly supports the next planned stage: visual data diagrams for local
asset/domain analysis. Even if incomplete, it provides a natural place to look
for graph rendering patterns.

Resurfacing value:

- domain cluster graph generator,
- project integration map renderer,
- dependency graph visualizer,
- canonical path treemap support after adaptation.

Risks:

- README may describe intended architecture more than implemented code,
- dependency freshness unknown.

Recommended action:

Create a focused review: can it render the domain allocation graph from
`domain-landscape-local-asset-allocation.md`? If yes, promote into
visual-analysis tooling.

### 6. Coinbase_from_zip

Path:

`/mnt/arch_data/home/caraxes/seed/archive/Coinbase_from_zip`

Observed signals:

- large structured Python system,
- README with privacy/security/revenue principles,
- Databricks pipeline docs,
- portfolio analysis,
- trading signals,
- fact checking,
- portfolio safety lens docs,
- tests and benchmarks,
- diagrams,
- examples.

Why it is a buried gem:

This is a deep finance/security/data system hidden under `seed/archive`. It has
clear overlap with x-change's finance/payment boundary, portfolio safety
thinking, and data-pipeline needs.

Resurfacing value:

- finance-domain reference for x-change expansion,
- portfolio safety lens extraction,
- data pipeline and Databricks docs,
- trading/portfolio model reference,
- security/privacy policy reference.

Risks:

- finance code is high-stakes,
- environment variables and external integrations require careful handling,
- archive path and generated-from-zip name suggest import baggage,
- should not be run against real accounts without full review.

Recommended action:

Promote documentation and model patterns first, especially:

- portfolio safety lens,
- privacy vault concepts,
- audit logger,
- transaction/portfolio schema,
- diagrams.

### 7. Mental Load Balancer

Path:

`/mnt/arch_data/home/caraxes/seed/archive/Atmosphere/mental-load-balancer`

Observed signals:

- README,
- API and architecture docs,
- VS Code extension structure,
- Python helper process,
- TypeScript source,
- tests,
- local-only privacy posture.

Why it is a buried gem:

This is the most concrete health/wellness/productivity candidate found in the
buried inventory. It complements Afloat, routines, and personal OS work.

Resurfacing value:

- cognitive load model for Afloat,
- routine/focus signals for Pulse-style workflows,
- local dashboard concept,
- personal OS wellness axis.

Risks:

- editor extension integration may be stale,
- monitoring keystrokes/context switching requires privacy clarity,
- should be opt-in only.

Recommended action:

Resurface as a wellness-domain project card. Extract the pressure score model
and intervention timing strategy before touching extension code.

### 8. Claude-Cursor Integration Bridge

Path:

`/mnt/arch_data/home/caraxes/seed/templates/claude-cursor-integration-bridge`

Observed signals:

- README,
- crosswalk JSON files,
- skill mapping,
- hook mapping,
- rule canonical pointers,
- install/refresh instructions.

Why it is a buried gem:

This is a concrete answer to cross-tool drift. It maps Claude and Cursor
integration surfaces and should be part of the top-level trust/structure story.

Resurfacing value:

- feed workspace-trust-auditor,
- support canonical project registry,
- reduce cross-agent instruction drift,
- generate visual crosswalk diagrams.

Risks:

- contains absolute paths that must be checked before reuse,
- should be treated as machine-readable config with schema validation.

Recommended action:

Promote to top-level `integration-bridge` registry or link it from
workspace-trust-auditor.

### 9. Development Contract Template

Path:

`/mnt/arch_data/home/caraxes/seed/templates/development-contract.md`

Observed signals:

- explicit contract model,
- references TUV-001,
- fidelity/integrity/accountability clauses,
- violation protocols,
- links to assistive-agreement-contracts and GRID boundary patterns.

Why it is a buried gem:

This is a strong governance primitive. It belongs in the trust/provenance
surface and should not be hidden in seed templates.

Resurfacing value:

- agent behavior contract,
- review/checklist material,
- policy registry seed,
- workspace-trust-auditor governance input.

Risks:

- contains stylized language and metaphor; operational version should be
  distilled into machine-readable rules.

Recommended action:

Promote as a governance template and derive a concise `contract-rules.yaml`
from it.

### 10. Code Modernization Workflow Example

Path:

`/mnt/arch_data/home/caraxes/roots/mistral-test/vibe/src/examples/code_modernization`

Observed signals:

- README,
- parent/child workflow design,
- structured-output LLM,
- sandboxed syntax validation,
- retry policy,
- human-in-the-loop review,
- PR proposal output.

Why it is a buried gem:

It is a clean workflow pattern for safe AI-assisted refactoring. The design is
immediately relevant to portfolio-control and trusted automation.

Resurfacing value:

- portfolio-control workflow template,
- mcp-orchestration-language example,
- safe modernization policy,
- human approval gate model.

Risks:

- may be tied to a specific workflow runtime,
- should be adapted conceptually before integration.

Recommended action:

Promote as a trusted automation pattern. Convert the architecture to a
portfolio-control workflow example.

## Tier 2 Candidates

### 11. Thread Diagram Simulator

Path:

`/mnt/arch_data/home/caraxes/seed/archive/thread-simulator`

Observed signals:

- `package.json`,
- D3,
- Express,
- Socket.IO,
- simulator for thread diagrams with radius and directional flow.

Resurfacing value:

- visual diagram phase,
- thread drift analysis,
- agent workflow visualization,
- Glass or workspace-trust-auditor diagram widgets.

Recommended action:

Review for a reusable thread-flow visualization component.

### 12. Mangrove Ecosystem Demo

Path:

`/mnt/arch_data/home/caraxes/seed/archive/demo/mangrove-ecosystem-demo.md`

Observed signals:

- live demo documentation,
- MCP server capabilities,
- morning briefing,
- ecosystem health scores,
- audit trails,
- focus sessions,
- local RAG,
- governance verification.

Resurfacing value:

- onboarding document,
- portfolio showcase,
- capability map seed,
- visual architecture storyboard.

Recommended action:

Promote into the portfolio report set as a historical capability snapshot.

### 13. Thread Drift Inventory

Path:

`/mnt/arch_data/home/caraxes/seed/archive/notes/thread-drift/thread_drift_inventory.md`

Observed signals:

- drift point analysis,
- MCP server inventory,
- enhanced RAG/intelligence server notes,
- dependency and component descriptions.

Resurfacing value:

- drift detection methodology,
- source material for timeline diagrams,
- governance and path-authority documentation.

Recommended action:

Index into personal-rag and link from future structural integrity docs.

### 14. Cascade Tool Consolidation Matrix

Path:

`/home/irfankabir/cascade-tool-consolidation/matrix.md`

Observed signals:

- topic/tool matrix,
- canonical/pointer distinction,
- cross-tool guidance for AGENTS, Windsurf, VS Code, Cursor, Zed, Claude Code,
  Copilot.

Resurfacing value:

- direct input for the canonical registry,
- instruction-authority visual diagram,
- cross-agent governance.

Recommended action:

Promote into workspace-trust-auditor or the directory consolidation docs.

### 15. Gap Calculation Protocol

Path:

`/home/irfankabir/docs/gap-calculation-protocol.md`

Observed signals:

- clear protocol,
- reference-track analogy,
- orient/query/synthesize/wardrobe/doors process,
- maps DevOps gap discovery into actionable next steps.

Resurfacing value:

- benchmark methodology,
- portfolio scorecard framing,
- next-action recommender,
- personal OS workflow.

Recommended action:

Promote into the benchmark methodology section and convert to checklist.

### 16. Extension Guardrails

Path:

`/home/irfankabir/scripts/EXT_GUARDRAILS.md`

Related script:

`/home/irfankabir/scripts/ext-guardrails.sh`

Observed signals:

- extension audit report,
- backup/audit/apply/restore/status workflow,
- JSON validation,
- proposal drift handling.

Resurfacing value:

- editor security hardening,
- tool-state audit,
- workspace-trust-auditor plugin,
- repeatable remediation pattern.

Recommended action:

Promote to `roots/security` or workspace-trust-auditor as an editor-extension
guardrail module.

### 17. Scheduler Routines

Path:

`/home/irfankabir/.claude/scheduler`

Observed signals:

- `dispatch.py`,
- routines for dep scan, dep warden, ecosystem triage, guard report,
  knowledge loop, ORI health/recommend/remediate, pipeline sweep, remote sweep,
  session gate,
- state files and tests.

Resurfacing value:

- personal OS automation,
- pulse/morning briefing,
- workflow scheduler,
- guardrail automation.

Risks:

- tool-state path, should not be moved casually,
- may contain live state.

Recommended action:

Do not move. Document as live tool-state and expose through registry/alias.

### 18. Root Scripts Collection

Path:

`/home/irfankabir/scripts`

Observed signals:

- workspace audit scripts,
- hardening scripts,
- memory guardrails,
- MCP probes,
- maintenance scripts,
- x-change bridge scripts,
- registry validation,
- setup scripts,
- health checks.

Resurfacing value:

- many scripts are standalone operational assets,
- should become a command catalog,
- can feed workspace-trust-auditor and roots/security.

Recommended action:

Create `scripts/catalog.yaml` with command name, purpose, risk level, inputs,
outputs, and owner domain.

## Tier 3 Candidates

### 19. Cascade System Audit Bundle

Path:

`/home/irfankabir/cascade-system-audit`

Observed signals:

- phase raw JSON files,
- architectural answers,
- discrepancies,
- inventory.

Resurfacing value:

- prior system audit data,
- comparison baseline,
- source for current structural inventory.

Recommended action:

Index into personal-rag and link from consolidation docs.

### 20. Home Docs Security and Architecture Reports

Path:

`/home/irfankabir/docs`

Observed signals:

- security audit reports,
- Chrome hardening,
- system diagnostic report,
- workspace architecture HTML,
- cursor config audit,
- gap calculation protocol.

Resurfacing value:

- security/trust baseline,
- local system hardening history,
- visual architecture artifacts.

Recommended action:

Create a docs index and classify by security, architecture, visual, session,
and protocol.

### 21. Preference Selection QA Template

Path:

`/mnt/arch_data/home/caraxes/seed/templates/preference-selection-qa`

Observed signals:

- package marker,
- TypeScript config,
- no README found in sampled path.

Resurfacing value:

- possible QA/preference evaluation template,
- may support benchmarking or product feedback workflows.

Recommended action:

Inspect source files before promotion. Candidate only.

### 22. Assistive Agreement Contracts

Path:

`/home/irfankabir/canopy/assistive-agreement-contracts`

Mirror:

`/mnt/arch_data/home/caraxes/canopy/assistive-agreement-contracts`

Observed signals:

- AGENTS/CLAUDE/README/package markers,
- directly referenced by development contract template.

Resurfacing value:

- governance/contracts domain,
- policy engine patterns,
- consent/provenance model.

Recommended action:

Add to top-level domain inventory and compare against x-change governance
needs.

### 23. Echoes Misc Accounting Tab

Path:

`/mnt/arch_data/home/caraxes/canopy/echoes/misc/Accounting/tab`

Observed signals:

- audit trail,
- payment gateway,
- payout engine,
- sync engine,
- user portal,
- work tracking modules.

Resurfacing value:

- finance/work-tracking reference,
- x-change expansion seed,
- payout/accounting model ideas.

Recommended action:

Inspect as a finance-domain candidate. Do not promote until code quality and
security are reviewed.

### 24. ROI Analysis Demo Assets

Path:

`/mnt/arch_data/home/caraxes/canopy/echoes/misc/roi_analysis`

Observed signals:

- demo/test bank corp configs,
- executive summary reports.

Resurfacing value:

- business case generation,
- professional operations,
- portfolio showcase.

Recommended action:

Index as career/marketplace/business-analysis material.

### 25. GRID Research and Visualizer Subtrees

Paths:

- `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main/research/experiments/hogwarts-visualizer`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main/docs/visualizations`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main/src/application/canvas`
- `/mnt/arch_data/home/caraxes/CascadeProjects/Projects/GRID-main/src/mycelium`

Observed signals:

- visualizer/canvas/mycelium naming,
- likely overshadowed inside the large GRID tree.

Resurfacing value:

- visual data diagrams,
- Graph/canvas surface,
- integration with Glass.

Recommended action:

Add to visual-analysis candidate list for a dedicated follow-up.

## High-Value Script Candidates

These scripts should not remain an uncategorized pile.

| Script | Resurfacing Category | Why |
|---|---|---|
| `/home/irfankabir/scripts/audit_workspace.py` | workspace-trust-auditor | Existing workspace inventory logic. |
| `/home/irfankabir/scripts/validate_project_registry.py` | registry/provenance | Validates machine-readable project authority. |
| `/home/irfankabir/scripts/propagate_signature_layer.py` | provenance | Authorship/signature propagation. |
| `/home/irfankabir/scripts/install_signature_layer_hooks.py` | provenance/hooks | Hook installation for identity layer. |
| `/home/irfankabir/scripts/mcp-probe.py` | MCP diagnostics | Directly useful for MCP server inventory. |
| `/home/irfankabir/scripts/mcp-probe.sh` | MCP diagnostics | Shell wrapper for probe flow. |
| `/home/irfankabir/scripts/runtime-health-pass.sh` | system health | Health pass candidate for scheduler. |
| `/home/irfankabir/scripts/weekly-security-check.sh` | security | Scheduled security routine. |
| `/home/irfankabir/scripts/xchange-ingest-bridge.py` | x-change/Glass integration | Existing bridge ingest helper. |
| `/home/irfankabir/scripts/xchange-circuit-close-proof.py` | x-change proofing | Evidence/proof helper. |
| `/home/irfankabir/scripts/grid-api-preflight.sh` | GRID ops | Preflight candidate for command catalog. |
| `/home/irfankabir/scripts/run-vision.sh` | Vision ops | Useful if Vision is resurfaced into diagram pipeline. |
| `/home/irfankabir/scripts/ext-guardrails.sh` | editor security | Repeatable editor-extension guardrail flow. |

Recommended action:

Create `/home/irfankabir/scripts/catalog.yaml` or a catalog under
workspace-trust-auditor. Classify each script by:

- purpose,
- owner domain,
- risk level,
- reads/writes paths,
- requires network,
- requires credentials,
- safe dry-run mode,
- validation command.

## Recommended Top-Level Resurfacing Targets

### Immediate

1. `network-visualizer-python` -> visual-analysis tooling candidate.
2. `claude-cursor-integration-bridge` -> cross-agent integration registry.
3. `development-contract.md` -> governance/policy registry seed.
4. `Gap Calculation Protocol` -> benchmark/next-action method.
5. scripts catalog -> workspace-trust-auditor command inventory.

### Near-Term

1. `mental-load-balancer` -> wellness/productivity candidate.
2. `Atmosphere Arcade` -> AI terminal/safety/TUI review.
3. `Coinbase_from_zip` -> finance/portfolio-safety review.
4. `Thread Diagram Simulator` -> diagram rendering candidate.
5. `Code Modernization Workflow` -> safe automation workflow template.

### Later

1. Reverb/Delay/Routing -> creative/spatial/audio concept extraction.
2. Echoes Accounting Tab -> finance/work tracking model review.
3. ROI Analysis demos -> business reporting material.
4. Cascade system audit bundle -> historical baseline ingestion.
5. GRID visualizer/canvas/mycelium subtrees -> visual surface follow-up.

## Proposed Resurfacing Registry Schema

```yaml
version: 1
generated_at: "2026-05-06"
candidates:
  - id: atmosphere-arcade
    title: Atmosphere Arcade
    source_paths:
      - /home/irfankabir/seed/archive/Atmosphere/Arcade
      - /mnt/arch_data/home/caraxes/seed/archive/Atmosphere/Arcade
    tier: 1
    primary_domain: ai-agents-and-automation
    secondary_domains:
      - productivity
      - security-trust
      - education
      - creative-spatial
    reason: Full AI terminal prototype with safety, TUI, deployment, and learning companion assets.
    promotion_mode: review-first
    immediate_action: create review card and inspect security/dependencies
    do_not:
      - run against real credentials
      - move before mirror/canonical decision
```

## Review Card Template

Use this for each candidate before promotion.

```yaml
id: candidate-id
title: Human title
source_path: /absolute/path
mirror_paths: []
tier: 1|2|3|4|hold
domain:
  primary: domain
  secondary: []
why_resurface: short reason
evidence:
  markers:
    - README
    - tests
    - package
  notable_files: []
risks:
  - stale dependencies
  - secrets/config risk
  - unresolved merge markers
promotion_target:
  type: docs|module|project|template|script-catalog|visual-tool
  path: proposed target or owner repo
preflight:
  - inspect README
  - inspect package/dependency files
  - scan for secrets before running
  - identify generated files
  - define smoke test
decision: pending|promote|index-only|archive|discard
```

## Important Risks Found During Sampling

1. Some archived READMEs contain unresolved merge-conflict markers. Reverb and
   Routing showed visible conflict marker fragments in sampled docs.
2. Finance-related archive code must not be run against real accounts or real
   tokens without a full security review.
3. Tool-state candidates under `.claude` should be documented and exposed, not
   moved.
4. Archive mirrors exist in both homes; do not promote one copy without checking
   whether the other is newer or cleaner.
5. Some READMEs may describe intended architecture more than implemented code.
   Every promotion needs code-level verification.

## Suggested Next Step

Create a machine-readable `resurfacing-candidates.yaml` from this document and
then pick the first three candidates for focused review:

1. `network-visualizer-python`
2. `claude-cursor-integration-bridge`
3. `mental-load-balancer`

Those three have the best ratio of relevance, low migration risk, and immediate
usefulness for the current direction:

- visual analysis,
- cross-agent integration authority,
- personal OS and wellness signal.

## Bottom Line

There are real buried assets in both homes. The highest-value ones should not be
treated as stale archives by default. They should be reviewed as resurfacing
candidates and either:

- promoted into current infrastructure,
- extracted as patterns,
- indexed into personal-rag,
- or explicitly frozen as archive-only.

The next useful artifact is not another broad inventory. It is a
`resurfacing-candidates.yaml` registry plus review cards for Tier 1 candidates.
