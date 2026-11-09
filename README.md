# ProbAI Plugin Marketplace

`probai-plugin` is the EURECOM ProbAI research group's marketplace for reusable skills and plugins in Codex and Claude Code.

## Skills catalog

| Plugin | Skill | Purpose | Availability |
| --- | --- | --- | --- |
| Slurm Ops (`slurm-ops`) | [Slurm operations](skills/slurm-ops/SKILL.md) | Prepare and run HPC workloads, inspect jobs and resources, and diagnose failures. | Codex and Claude Code |
| Slurm Ops (`slurm-ops`) | [Setup](skills/setup/SKILL.md) | Install or update the Slurm specialist and configure optional local settings. | Codex |

Each marketplace manifest lists the available plugins. Add future research-group plugins to both manifests and list their skills here. Give each plugin its own source directory and keep its skills, helpers, and hooks together.

## Slurm Ops

Slurm Ops provides an HPC specialist, reusable skills, and Python helpers for local development and Slurm operations in the current execution environment.

- **Local:** development, script preparation, and offline environment detection without Slurm.
- **Helix:** local scheduler diagnostics, workflow conventions, and proportional limits on CPU, memory, and other resources for GPU jobs.
- **Jean Zay:** IDRIS scheduler conventions, preparation for compute nodes without internet access, and storage selection across personal and project filesystems.

The plugin supports single-node CPU or GPU jobs and arrays of single-node jobs on macOS and Linux with Python 3.9 or later. The helpers use only the standard library. The plugin has no MCP service, background monitor, automatic synchronization, or dependency installation.

## Execution environment

The helpers inspect the current environment and validate resource requests. On a workstation, they support local development and offline script preparation. On a cluster, they use locally available Slurm commands.

Diagnostics and resource validation are read-only. Follow the [common workflows](skills/slurm-ops/references/common.md) for launchers, job authorization, and uncertain submissions.

## Existing installations

The marketplace was previously named `slurm-ops-local`. Remove that marketplace registration in your client, then add the marketplace and install `slurm-ops@probai-plugin` using the instructions below. In Codex, use `codex plugin marketplace remove slurm-ops-local`; in Claude Code, use `/plugin marketplace remove slurm-ops-local`. Marketplace removal may also remove installed plugins, so reinstall Slurm Ops under the new name.

## Install in Codex

The repository root is the plugin root. Codex loads `.codex-plugin/plugin.json`, which declares the skills, bundled hooks, and setup workflow. The repository marketplace is `.agents/plugins/marketplace.json`, named `probai-plugin`. Its `source.path` is `./`, relative to the repository root.

This package uses the Codex compatibility layout for hook discovery. In Codex `0.164.0-alpha.11.1`, a root `plugin.json` takes precedence and produces an empty hook registry for this package, including when a compatibility manifest is also present. Keep the manifest at `.codex-plugin/plugin.json` and leave the plugin root free of a separate `plugin.json`.

Add the GitHub marketplace and install the plugin:

```sh
codex plugin marketplace add eurecom-probai/slurm_ops_plugin
codex plugin add slurm-ops@probai-plugin
```

Start a new Codex session after installation. In the desktop app, restart if needed, open Plugins, and choose **ProbAI Plugin** to find **Slurm Ops**. The marketplace retains the name `probai-plugin` for both GitHub and local installations. Codex loads a cached copy of the installed plugin.

For a local checkout, replace the first command with `codex plugin marketplace add /absolute/path/to/slurm_ops_plugin`. To switch an existing configured source, run `codex plugin marketplace remove probai-plugin`, then add the desired source and install the plugin again.

To refresh a GitHub installation:

```sh
codex plugin marketplace upgrade probai-plugin
codex plugin add slurm-ops@probai-plugin
```

Start a new session after refreshing. For local development, refresh or reinstall after changing the checkout.

Review the bundled hooks with `/hooks` in Codex CLI. Mark the exact definitions as trusted when enabling them, and review changed definitions again. The marketplace requires an authentication policy field. The plugin uses no connected account or service authentication.

This package uses a repository marketplace and manually reviewed lifecycle hooks. For the package, command, and hook formats, see [Package your plugin](https://developers.openai.com/plugins/build/plugins), [Codex CLI reference](https://learn.chatgpt.com/docs/cli/reference), and [Hooks](https://learn.chatgpt.com/docs/hooks).

## Install in Claude Code

The Claude Code marketplace is `.claude-plugin/marketplace.json`, named `probai-plugin`. Its entry points to the repository root and exposes the existing `skills/slurm-ops` directory. Skills, references, specialist instructions, helpers, and hooks remain shared with Codex. The `setup` skill handles Codex specialist registration and stays in the Codex installation.

In Claude Code, add the GitHub marketplace and install the plugin:

```text
/plugin marketplace add eurecom-probai/slurm_ops_plugin
/plugin install slurm-ops@probai-plugin
```

The equivalent terminal commands are:

```sh
claude plugin marketplace add eurecom-probai/slurm_ops_plugin
claude plugin install slurm-ops@probai-plugin
```

Start a new Claude Code session after installation, then invoke `/slurm-ops:slurm-ops` or describe an HPC task. GitHub installation was verified with Claude Code 2.1.317: the installed plugin exposes one skill and the `SessionStart` and `PreToolUse` hooks.

For a local checkout, use `/plugin marketplace add /absolute/path/to/slurm_ops_plugin` instead. When switching from a local checkout to GitHub, first run `/plugin marketplace remove probai-plugin`, then run the GitHub add and install commands above. Claude requires the registered marketplace source to match its saved settings. Removing the marketplace also uninstalls its plugins.

To refresh a GitHub installation:

```text
/plugin marketplace update probai-plugin
/plugin update slurm-ops@probai-plugin
```

Start a new session after updating.

Claude Code discovers the shared `hooks/hooks.json`. Hook commands resolve the installed path through `CLAUDE_PLUGIN_ROOT` in Claude Code and `PLUGIN_ROOT` in Codex. Review the hooks through `/hooks`. The Slurm skill delegates using the instructions in the existing TOML definition when a registered specialist is unavailable.

See the [Claude Code marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference) for the marketplace format and the [plugin manifest reference](https://code.claude.com/docs/en/plugins-reference) for component discovery.

## Slurm specialist

The `slurm-ops` skill delegates HPC tasks to a `slurm_ops` specialist. It passes the task, working directory, constraints, authorization, relevant job IDs, and the skill path. The specialist uses the shared operational references and helpers, owns the affected scheduler actions, and returns findings, changed files, job states, and unresolved requirements. The parent agent can continue independent work and integrate the report.

The bundled definition is [agents/slurm_ops.toml](agents/slurm_ops.toml). Its discovery description covers HPC interactions broadly. Operational scope and site conventions remain in the skill references. Model settings and permissions follow the parent session.

For a named agent available across projects, invoke the plugin's `setup` skill and request specialist installation. Setup copies the definition to `~/.codex/agents/slurm_ops.toml`, or `agents/slurm_ops.toml` under `CODEX_HOME` when set. A project-scoped installation uses `.codex/agents/slurm_ops.toml`. Start a new Codex session after registration. See [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents#custom-agents) for discovery and configuration.

The plugin also supports delegation before registration: the skill passes the bundled instructions to a subagent. The specialist follows the operating guidance directly, and clients without delegation tools use it in the current context.

After refreshing the plugin, run setup to update a separately installed agent definition. Setup preserves local customizations. When removing a named specialist, remove its installed `slurm_ops.toml` file as well. Keep the plugin enabled while using the specialist so its skill and helpers remain available.

Example requests:

- Prepare this workload for the cluster using the project's launcher.
- Investigate this failed job and correct its execution configuration.
- Inspect my queued jobs and explain their pending reasons.

## Use the skills and helpers

Invoke the packaged `slurm-ops` skill for HPC work or `setup` for specialist registration and optional configuration. The agent can also select these skills for matching tasks. Follow existing project instructions and launchers for testing and commit practices.

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

The shared Codex and Claude Code hook adapter is in `hooks/codex.py`. Shared command classification is in `slurm_ops/guard.py`.

- `SessionStart` gathers a compact read-only snapshot through local Slurm commands for startup, resume, clear, compaction, and fork. It reports node totals, node state counts, accounts for the current user, default QoS, relevant allowed QoS limits, and queue state counts. It lists all returned partitions with their state, wall-time limit, and default status. It omits node resource profiles, individual node records, job names, and daemon configuration. Collection has a ten-second total limit and a three-second limit per command. The hook timeout is twelve seconds.
- The snapshot reports missing commands, denied queries, timeouts, incomplete inventory, and omitted rows as limitations. Without local Slurm commands, startup produces a brief message that Slurm is unavailable. Hooks submit no jobs, install no dependencies, and change no caches.
- The hook points to the main skill for [helper commands](skills/slurm-ops/SKILL.md#helper-commands) and reference selection.
- `PreToolUse` matches the `Bash` event in Codex and Claude Code, including Codex unified execution. On confirmed login nodes, it denies recognized standard training and test commands. It allows lightweight diagnostics and commands that execute within an allocation.
- Command classification recognizes simple environment prefixes, `uv run`, and `uvx`. Complex or ambiguous shell forms receive advice.
- Project scripts receive agent review under the [execution location guidance](skills/slurm-ops/references/common.md#execution-location). Individual jobs require no registration.
- Hook errors allow execution to continue.

## Project structure

The specialist definition is in `agents/slurm_ops.toml`. Shared helpers are in `slurm_ops/`. The command-line entry point is `scripts/slurm_ops.py`, and skill references are in `skills/slurm-ops/references/`. An adapter translates lifecycle and tool events from an agent application into calls to the shared logic.
