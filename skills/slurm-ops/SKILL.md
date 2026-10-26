---
name: slurm-ops
description: Prepare, inspect, and troubleshoot single-node Slurm jobs and arrays in the current environment, with Helix and Jean Zay conventions and local development guidance. Use for HPC resource choices, launchers, queues, logs, storage, and allocation practices.
---

# Slurm operations

Support single-node CPU and GPU jobs and arrays. Defer multi-node operations.

Read [common workflows](references/common.md) before Slurm job work and all cluster operations. Then read the applicable environment reference:

- [Local development](references/local.md) for workstation development and offline job preparation.
- [Helix](references/helix.md) for Helix operations and script preparation.
- [Jean Zay](references/jean-zay.md) for IDRIS operations, offline compute environments, project filesystems, and script preparation.

## Helper commands

Resolve `<plugin-root>` from the installed skill location. It is the directory two levels above this skill directory and contains `.codex-plugin/plugin.json`. Replace the placeholder with the actual absolute path. Quote paths containing spaces.

The helpers require Python 3.9 or later and its standard library.

- Run `python3 <plugin-root>/scripts/slurm_ops.py context --json` to establish the current execution context. It runs offline and reports site, role, allocation, and evidence separately.
- Run `python3 <plugin-root>/scripts/slurm_ops.py inspect --json` for detailed, read-only scheduler evidence.
