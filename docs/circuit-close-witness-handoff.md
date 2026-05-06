# Circuit Close Witness Handoff (Leg 1)

Objective: run an independent verification of Circuit Close by a second operator and return a structured result.

## Scope

- This is not a product demo.
- This is a reproducibility check of the technical mechanism.
- Expected output is a PASS/FAIL style verification report plus generated artifacts.

## Preconditions

- Repo access to x-change (private is fine)
- Python 3.13+
- uv installed
- Access to these scripts:
  - /home/irfankabir/scripts/xchange-ingest-bridge.py
  - /home/irfankabir/scripts/xchange-seed-circuit-close.py
  - /home/irfankabir/scripts/xchange-circuit-close-proof.py

## Runbook

Follow:

- docs/circuit-close-runbook.md

Do not skip staleness checks, and do not use bypass flags.

## Evidence required from witness

Return all of the following:

1. Terminal output snippets for:
   - Step 4 ingest (pre-attestation)
   - Step 5 ingest (contract_satisfied)
   - Step 6 proof generation status
2. Generated files:
   - proofs/circuit-close-proof.md
   - proofs/circuit-close-proof.json
3. SHA-256 values:

```bash
sha256sum proofs/circuit-close-proof.md proofs/circuit-close-proof.json
```

4. Final checklist status from the generated markdown proof.

## PASS criteria

- Checklist in proof markdown shows all Gate 2 checks passing.
- Transition reason includes:

`contract_satisfied: drafted -> earned`

- Evidence trail contains both pre-attestation and attestation entries.
- No staleness bypass used.

## Witness return template

Copy and fill this exactly:

```text
Witness: <name or handle>
Date (UTC): <timestamp>
Repo commit tested: <git rev-parse HEAD>
Runbook followed: yes/no
Staleness bypass used: yes/no
Gate 1: pass/fail
Gate 2: pass/fail
Gate 3: pass/fail
Transition reason observed: <text>
proof.md sha256: <hash>
proof.json sha256: <hash>
Notes: <optional>
```
