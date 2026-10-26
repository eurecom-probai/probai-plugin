---
name: slurm-ops
description: >-
  Use when interacting with HPC systems: preparing and running workloads, managing jobs and resources, diagnosing failures, or working with cluster environments, dependencies, and storage.
---

# Slurm operations

## Delegate HPC work

For a task involving HPC, delegate the HPC work to the `slurm_ops` specialist. Pass the task, working directory, user constraints, existing authorization, relevant launchers and job IDs, and the absolute path to this `SKILL.md`. Give the specialist ownership of the affected scheduler actions and files while it works, then integrate its report into the broader task.

Use the registered `slurm_ops` agent when available. Otherwise, read `developer_instructions` from the [bundled agent definition](../../agents/slurm_ops.toml) and include those instructions in a focused subagent task, identifying it as the Slurm Ops specialist.

When already acting as the Slurm Ops specialist, follow the operating guidance below directly. Handle the task in the current context when delegation tools are unavailable or the user requests direct handling. Reading this skill during startup requires delegation only when the current task involves HPC.

## Operating guidance

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
