# Grove / mount-independence rollback notes

**Purpose:** Satisfy the directory authority no-break rule before any physical move of `grove/` or repointing symlinks.

**Current chain (2026-05-07):**

- `/home/irfankabir/grove` → symlink → `/home/irfankabir/CascadeProjects/grove` (real directory; irfankabir02 git scope).

**Pre-move checklist (do not skip):**

1. `git status` clean or intentional WIP documented inside `~/CascadeProjects/grove` (or subtree repos).
2. Copy or `rsync` full tree to target location; verify `.git` and remotes.
3. Search references: `~/grove`, `CascadeProjects/grove`, `github-irfan`, workspace JSON, `PROJECT_REGISTRY.yaml`.
4. Update [`consolidation-registry.yaml`](./consolidation-registry.yaml) `grove_accounts.canonical_path` and symlink section.
5. Rollback: keep a tarball or second remote push before removing the old path.

**Deferred:** No filesystem move performed during this consolidation pass; operator enables when mount policy is explicit.
