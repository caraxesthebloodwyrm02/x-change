# Implementation Strategy

## Goal

Execute the handoff as a staged authority-building program. Each step must pass its own objective gate before the next step starts. The whole goal is achieved when a future agent can move from orientation through memory, wiring, maintenance, registry, structure, domain allocation, and resurfacing without redoing broad discovery or hitting avoidable roadblocks.

## Step Gates

| Step | Objective | Completion Gate | Verification Gate |
|---|---|---|---|
| 1 | Orientation | Handoff pack is complete and executable. | Preparedness checks pass with no missing source maps, invalid JSON, old links, or placeholder markers. |
| 2 | Memory authority | Persistent context carryover has a canonical source map and session protocol. | `06-authority/MEMORY-AUTHORITY.md` names roots, stale rules, retrieval checks, and session handoff format. |
| 3 | MCP wiring authority | Editor and agent clients have intentional MCP profiles. | `06-authority/MCP-WIRING-AUTHORITY.md` declares canonical server set, client profiles, command policy, and parity checks. |
| 4 | Toolchain and maintenance authority | Routine maintenance is governed by schedules, targets, safety modes, and reports. | `06-authority/TOOLCHAIN-MAINTENANCE-AUTHORITY.md` covers npm/npx, degraded tools, timers, scripts, and broken-target handling. |
| 5 | Custom asset registry | Custom agents, hooks, skills, commands, workflows, plugins, rules, and batches have structured registry coverage. | `06-authority/CUSTOM-ASSET-REGISTRY-SEED.md` defines record shape, status values, and starter inventory lanes. |
| 6 | Directory consolidation | Structural discipline is planned without breaking paths. | `06-authority/DIRECTORY-DOMAIN-RESURFACING-AUTHORITY.md` classifies roots, move constraints, no-break checks, and rollback expectations. |
| 7 | Domain distribution | Local assets are allocated into real-world usage domains with multi-domain tags. | Domain records preserve primary and secondary tags plus diagram-ready graph expectations. |
| 8 | Buried asset resurfacing | Hidden high-value assets have promotion paths. | Resurfacing records include value, path, target surface, owner/status, and validation. |
| 9 | Fulfillment review | The thread outcomes are checked against final artifacts. | `FULFILLMENT-MATRIX.md` marks each prompt outcome as satisfied, partial with blocker, or intentionally deferred. |
| 10 | Registry handoff | Authority docs have machine-readable implementation inputs. | `07-registries/` contains preparedness, memory, MCP, toolchain, maintenance, custom asset, directory/domain/resurfacing, and fulfillment records. |

## Execution Rules

- Build authority records before external repairs.
- Do not move project directories until path authority exists.
- Do not rewrite MCP configs until MCP authority and client profiles exist.
- Do not run destructive cleanup, package upgrades, or privileged commands from this handoff pass.
- Every batch completion must record changed files, validation, blockers, and next recommended step.
- Future implementation should prefer `07-registries/` for structured inputs and `06-authority/` for human-readable policy.

## Momentum Rule

If a step fails verification, repair that step in place before continuing. Do not skip forward with a broken authority layer.
