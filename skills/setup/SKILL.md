---
name: setup
description: Install or update the Slurm Ops specialist and explain optional configuration and hook review when the user sets up the plugin.
---

# Set up Slurm Ops

## Specialist registration

When the user requests specialist installation, copy the [bundled agent definition](../../agents/slurm_ops.toml) to `agents/slurm_ops.toml` under the active Codex home (`CODEX_HOME`, or `~/.codex` when unset). Create the `agents` directory if needed. Use a project's `.codex/agents/slurm_ops.toml` instead when the user requests project scope. Resolve the source from this installed skill's location.

Inspect any existing destination before updating it. An identical file needs no change. Preserve custom model settings and instructions when merging an update; resolve conflicting customizations with the user. Keep the shared operational guidance in the plugin skill. The agent inherits its parent's model settings unless locally customized. Permissions follow the parent session.

Report the installed path and tell the user to start a new Codex session. Follow [specialist setup and lifecycle](../../README.md#slurm-specialist) for refresh and removal. When removing the specialist, delete only the requested agent file and preserve unrelated configuration.

## Configuration and hooks

Configuration is optional. Read the existing project instructions and launcher before choosing account or storage hints.

Read [configuration locations, fields, and precedence](../../README.md#optional-configuration). Write user or project configuration only when requested. Store personal accounts and paths in the chosen local configuration. Exclude credentials. Preserve unrelated Codex settings and the global installation.

Explain the [hook behavior and limits](../../README.md#hook-behavior-and-limits). Follow the [installation instructions](../../README.md#install-in-codex) for hook review and trust. During setup, do not install dependencies, import workloads, submit jobs, or move caches.
