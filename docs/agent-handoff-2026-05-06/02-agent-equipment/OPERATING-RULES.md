# Operating Rules

## Source Authority

1. Closest project `AGENTS.md` and `CLAUDE.md` win for code work.
2. `/home/irfankabir/AGENTS.md` and `/home/irfankabir/CLAUDE.md` define workspace-level authority.
3. This handoff pack defines the execution map for inventory, registry, wiring, and maintenance work.
4. Source maps are point-in-time evidence. Re-verify live paths before modifying anything.

## Safety

- Never expose secret values.
- Treat `.env`, credentials, OAuth, token, private key, and `settings.local.json` files as path-only.
- Do not run `sudo`.
- Do not delete, prune, reset, upgrade, or migrate without an explicit implementation batch and validation plan.
- Prefer read-only probes before repair.
- Separate environment failures from code failures.

## Path Rules

- Active home is `/home/irfankabir`.
- Preserved caraxes home is `/mnt/arch_data/home/caraxes`.
- Treat `/home/caraxes` as stale unless a file is explicitly archived or a fixture.
- Do not assume symlinks are live; verify.
- Do not move project roots until registry authority exists.

## Tool Rules

- Python project commands should use `uv`.
- CascadeProjects TypeScript MCP servers expect npm/npx tooling.
- `docker compose` exists; standalone `docker-compose` may not.
- Go, Rust, Cargo, and Code through snap were degraded during audit.
- Check `command -v` before assuming a binary.

## Reporting

Every implementation batch must end with:

- files changed
- validation commands and results
- unresolved blockers
- next recommended batch
- any stale assumptions discovered

