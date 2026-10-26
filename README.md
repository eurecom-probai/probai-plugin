# Slurm Ops

A skills plugin for local development and Slurm operations in the current execution environment. It includes Codex integration. Other agent applications can reuse the guidance and Python helpers through adapters.

- **Local:** development, script preparation, and offline environment detection without Slurm.
- **Helix:** local scheduler diagnostics, workflow conventions, and proportional limits on CPU, memory, and other resources for GPU jobs.
- **Jean Zay:** IDRIS scheduler conventions, preparation for compute nodes without internet access, and storage selection across personal and project filesystems.

The plugin supports single-node CPU or GPU jobs and arrays of single-node jobs on macOS and Linux with Python 3.9 or later. The helpers use only the standard library. The plugin has no MCP service, background monitor, automatic synchronization, or dependency installation.

## Execution environment

The helpers inspect the current environment and validate resource requests. On a workstation, they support local development and offline script preparation. On a cluster, they use locally available Slurm commands.

Diagnostics and resource validation are read-only. Follow the [common workflows](skills/slurm-ops/references/common.md) for launchers, job authorization, and uncertain submissions.

## Install in Codex

The repository root is the plugin root. Codex loads `.codex-plugin/plugin.json`, which declares the skills, bundled hooks, and setup workflow. The repository marketplace is `.agents/plugins/marketplace.json`, named `slurm-ops-local`. Its `source.path` is `./`, relative to the repository root.

This package uses the Codex compatibility layout for hook discovery. In Codex `0.164.0-alpha.11.1`, a root `plugin.json` takes precedence and produces an empty hook registry for this package, including when a compatibility manifest is also present. Keep the manifest at `.codex-plugin/plugin.json` and leave the plugin root free of a separate `plugin.json`.

Use the absolute path to the checkout:

```sh
codex plugin marketplace add /absolute/path/to/slurm_ops_plugin
codex plugin add slurm-ops@slurm-ops-local
```

Run these commands to install the plugin. Start a new Codex session after installation. In the desktop app, restart if needed, open Plugins, choose **Slurm Ops Local**, and install **Slurm Ops**. Codex loads a cached copy of the installed plugin. After changing the checkout, reinstall or refresh the local plugin and start a new session.

Review the bundled hooks with `/hooks` in Codex CLI. Mark the exact definitions as trusted when enabling them, and review changed definitions again. The marketplace requires an authentication policy field. The plugin uses no connected account or service authentication.

This package uses a local repository marketplace and manually reviewed lifecycle hooks. For the package, command, and hook formats, see [Package your plugin](https://developers.openai.com/plugins/build/plugins), [Codex CLI reference](https://learn.chatgpt.com/docs/cli/reference), and [Hooks](https://learn.chatgpt.com/docs/hooks).

## Use the skills and helpers

Invoke the packaged `slurm-ops` skill for operational guidance or `setup` for optional configuration. The agent can also select these skills for matching tasks. Follow existing project instructions and launchers for testing and commit practices.

From the plugin checkout:

```sh
python3 scripts/slurm_ops.py context --json
python3 scripts/slurm_ops.py inspect --json
python3 scripts/slurm_ops.py validate-resources --inventory inventory.json --request request.json --json
```

From another working directory, use the absolute path to the installed script. Quote paths containing spaces. These commands work without Git.

| Command | Behavior |
| --- | --- |
| `context [--json]` | Reports the current site, execution role, allocation, and evidence offline. |
| `inspect [--json]` | Runs local Slurm queries with time and output limits for resources, node capacities, user associations, QoS, and the queue for the current user. Reports storage paths advertised by the current environment. |
| `validate-resources --inventory FILE --request FILE [--json]` | Validates Helix proportional resource limits offline using normalized JSON. |

Follow the [execution location guidance](skills/slurm-ops/references/common.md#execution-location) before running cluster workloads.

For Jean Zay, read the [site reference](skills/slurm-ops/references/jean-zay.md) before selecting accounts, modules, storage, or dependencies. Prepare dependencies and data before submission; compute jobs run offline. Diagnostics list recognized storage variables and their sanitized values under `shell_environment.storage_variables_present` and `shell_environment.storage_paths`. Verify path availability, quotas, retention, and required connectivity in the execution environment.

### Helix resource validation

The offline validator compares the effective job request with configured node capacities under the Helix proportional resource limits. The [resource validation reference](skills/slurm-ops/references/resource-preflight.md) contains the command, JSON schema, exit codes, and normalization requirements.

## Optional configuration

Configuration is optional:

- User defaults: `$XDG_CONFIG_HOME/slurm-ops/config.json`, or `~/.config/slurm-ops/config.json` when `XDG_CONFIG_HOME` is unset.
- Project overrides: the nearest `.slurm-ops.json` in the current directory or an ancestor directory. Discovery also works outside Git repositories.

Explicit helper input takes precedence over project hints. Project hints override user defaults. A more specific account hint replaces the broader one. Storage hints are merged by name.

| Field | Type and purpose |
| --- | --- |
| `account` | String hint for the existing local account. |
| `storage` | Object mapping names to literal path strings used as storage hints. |

See [examples/config.json](examples/config.json). Setup writes configuration only when requested. Keep personal paths and accounts in local configuration. Never store credentials in the package. The site, execution role, and execution environment come from local observations.

## Hook behavior and limits

The Codex adapter is in `hooks/codex.py`. Shared command classification is in `slurm_ops/guard.py`.

- `SessionStart` gathers a compact read-only snapshot through local Slurm commands for startup, resume, clear, compaction, and fork. It reports node totals, node state counts, accounts for the current user, default QoS, relevant allowed QoS limits, and queue state counts. It lists all returned partitions with their state, wall-time limit, and default status. It omits node resource profiles, individual node records, job names, and daemon configuration. Collection has a ten-second total limit and a three-second limit per command. The hook timeout is twelve seconds.
- The snapshot reports missing commands, denied queries, timeouts, incomplete inventory, and omitted rows as limitations. Without local Slurm commands, startup produces a brief message that Slurm is unavailable. Hooks submit no jobs, install no dependencies, and change no caches.
- The hook points to the main skill for [helper commands](skills/slurm-ops/SKILL.md#helper-commands) and reference selection.
- `PreToolUse` matches the documented Codex `Bash` event, including unified execution. On confirmed login nodes, it denies recognized standard training and test commands. It allows lightweight diagnostics and commands that execute within an allocation.
- Command classification recognizes simple environment prefixes, `uv run`, and `uvx`. Complex or ambiguous shell forms receive advice.
- Project scripts receive agent review under the [execution location guidance](skills/slurm-ops/references/common.md#execution-location). Individual jobs require no registration.
- Hook errors allow execution to continue.

## Project structure

Shared helpers are in `slurm_ops/`. The command-line entry point is `scripts/slurm_ops.py`, and skill references are in `skills/slurm-ops/references/`. An adapter translates lifecycle and tool events from an agent application into calls to the shared logic.
