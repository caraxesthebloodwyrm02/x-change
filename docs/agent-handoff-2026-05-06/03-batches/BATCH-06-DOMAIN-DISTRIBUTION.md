# Batch 06 - Domain Distribution

## Goal

Allocate local assets into practical usage domains and prepare visual analysis.

## Source Docs To Read First

- `../01-source-maps/domain-landscape-local-asset-allocation.md`
- `../01-source-maps/portfolio-inventory-benchmark.md`
- `../01-source-maps/buried-assets-resurfacing-inventory.md`

## Inputs

- domain model
- project rankings
- local asset lists
- resurfacing candidates

## Outputs

- domain registry
- asset-to-domain map
- diagram-ready graph data design
- batch-specific visualization targets

## Allowed Actions

- classify assets
- propose diagrams
- create domain records
- cross-link related projects

## Forbidden Actions

- move assets based only on domain classification
- collapse multi-domain projects into one label
- hide uncertainty in classifications

## Parallel-Safe Work

- education domain map
- finance domain map
- security domain map
- data and automation domain map
- personal development domain map

## Acceptance Criteria

- each domain has assets, gaps, and diagram candidates
- multi-domain projects preserve secondary tags
- visual data requirements are explicit

## Likely Blockers

- projects with multiple valid domains
- buried assets with unclear current status
- missing project metadata

## Schema Input Example

```json
{
  "asset": "x-change",
  "domains": ["education", "finance", "governance"],
  "primary_domain": "education",
  "evidence": ["policy-core", "reward lifecycle", "Stripe boundary"]
}
```

