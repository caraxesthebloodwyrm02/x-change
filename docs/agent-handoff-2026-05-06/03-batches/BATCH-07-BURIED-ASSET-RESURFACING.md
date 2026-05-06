# Batch 07 - Buried Asset Resurfacing

## Goal

Promote high-value nested assets into visible infrastructure without losing provenance or breaking placement.

## Source Docs To Read First

- `../01-source-maps/buried-assets-resurfacing-inventory.md`
- `../01-source-maps/domain-landscape-local-asset-allocation.md`
- `../01-source-maps/directory-structure-consolidation-playbook.md`

## Inputs

- resurfacing tiers
- candidate paths
- domain allocation
- directory discipline rules

## Outputs

- resurfacing registry
- promotion plan
- candidate-to-domain mapping
- validation checklist

## Allowed Actions

- verify candidate paths
- classify candidates
- design promotion targets
- add registry entries

## Forbidden Actions

- move buried assets without a promotion plan
- delete originals
- flatten nuanced assets into generic buckets
- promote generated cache files

## Parallel-Safe Work

- Tier 1 candidate verification
- Tier 2 candidate verification
- domain mapping
- provenance capture

## Acceptance Criteria

- each candidate has value, current path, proposed surface, and validation
- no candidate is promoted without owner and domain tags
- archived candidates remain marked as archived until reactivated

## Likely Blockers

- missing paths
- unclear active/archive status
- candidates embedded inside larger systems

## Schema Input Example

```json
{
  "candidate": "Claude-Cursor Integration Bridge",
  "tier": 1,
  "current_status": "buried",
  "target_surface": "agent-harness/wiring",
  "validation": ["path_exists", "owner_classified", "domain_tags_assigned"]
}
```

