# Registry Records

This directory contains machine-readable seed records derived from the handoff source maps and authority docs. These records are implementation inputs, not external repairs.

Use them to build the future `agent-harness` authority layer without redoing discovery.

## Records

| File | Purpose |
|---|---|
| `preparedness-record.json` | Records the current handoff preparedness status. |
| `memory-authority.json` | Canonical memory sources and session protocol. |
| `mcp-authority.json` | MCP server set, client profiles, command policy, parity checks. |
| `toolchain-authority.json` | Development tool availability and degraded tool states. |
| `maintenance-authority.json` | Routine maintenance jobs and safety policy. |
| `custom-assets-seed.json` | Custom asset registry lanes and starter entries. |
| `directory-domain-resurfacing-authority.json` | Directory, domain, and resurfacing authority records. |
| `fulfillment-record.json` | Prompt outcome fulfillment status. |
| `batch-execution-tracker.json` | Per-batch execution status, changed files, validation, blockers, and next step. |
| `fix-candidate-routing.json` | Maps each fix candidate to its owning batch, authority doc, registry file, and parallel group. |
| `crosswalk.json` | Maps each batch to its source maps, authority docs, registry files, and fix candidates. |

## Safety

These records do not include secret values. They reference sensitive files only by path class or policy.

