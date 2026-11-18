<h1 align="center">ProbAI Plugin Marketplace</h1>

<p align="center">
  EURECOM ProbAI tools for running Slurm workloads and preparing scientific figures.
</p>

<p align="center">
  <a href="#install-in-codex"><img alt="Install in Codex" src="https://img.shields.io/badge/Install-Codex-243447?style=flat"></a>
  <a href="#install-in-claude-code"><img alt="Install in Claude Code" src="https://img.shields.io/badge/Install-Claude%20Code-984725?style=flat"></a>
</p>

## Installation

Add the marketplace once, then run the install command for each plugin you want. Choose `slurm-ops` for cluster jobs or `research-plots` for manuscript figures. Start a new session after installation.

### Install in Codex

Run these commands in your terminal.

```sh
codex plugin marketplace add eurecom-probai/probai-plugin
codex plugin add slurm-ops@probai-plugin
codex plugin add research-plots@probai-plugin
```

### Install in Claude Code

Run these commands inside Claude Code.

```text
/plugin marketplace add eurecom-probai/probai-plugin
/plugin install slurm-ops@probai-plugin
/plugin install research-plots@probai-plugin
```

For Slurm Ops, review the bundled hooks with `/hooks` before enabling them. In Codex CLI, trust the definitions you reviewed and review them again after changes. See [hook behavior and limits](#hook-behavior-and-limits).

## Skills

Describe the task in a new session or invoke a skill by name.

| Task | Skill | Codex | Claude Code |
| --- | --- | --- | --- |
| Prepare a job, inspect the queue, or diagnose a failure | [Slurm Ops](#slurm-ops) | `$slurm-ops` | `/slurm-ops:slurm-ops` |
| Prepare a manuscript figure | [Research Plots](#research-plots) | `$research-plots` | `/research-plots:research-plots` |
| Register or update the Slurm specialist | [Setup](#slurm-specialist) | `$setup` | Codex only |

### Slurm Ops

Try “Inspect my queued jobs and explain why they are pending.” The [Slurm skill](skills/slurm-ops/SKILL.md) uses the scheduler and project launcher available in the current environment.

- **Local:** development, script preparation, and offline environment detection without Slurm.
- **Helix:** local scheduler diagnostics, workflow conventions, and proportional limits on CPU, memory, and other resources for GPU jobs.
- **Jean Zay:** IDRIS scheduler conventions, preparation for compute nodes without internet access, and storage selection across personal and project filesystems.

The plugin supports single-node CPU or GPU jobs and arrays of single-node jobs on macOS and Linux with Python 3.9 or later. The helpers use only the standard library. The plugin has no MCP service, background monitor, automatic synchronization, or dependency installation.

### Research Plots

Ask for a figure at its intended publication size, for example, “Plot prediction error against training observations in two panels at ICML full width. Use the supplied uncertainty bands.”

The skill produces one editable script per figure and exports a PDF. Scripts can share fonts, colors, and legend settings through a local `_config.py`. Manuscript dimensions take precedence over the ICML, ICLR, AISTATS, NeurIPS, and TMLR presets. See the [plotting skill](plugins/research-plots/skills/research-plots/SKILL.md), [venue dimensions](plugins/research-plots/skills/research-plots/references/venues.md), and [figure template](plugins/research-plots/skills/research-plots/assets/figure_template.py).

#### Example figures

Both examples use synthetic data and declare their dependencies inline for `uv`. Keep the [shared configuration](plugins/research-plots/examples/_config.py) beside the scripts when copying them. They use LaTeX when available and otherwise use native Matplotlib text.

| Example | Layout | Files |
| --- | --- | --- |
| Learning curves | Two panels at full manuscript width with illustrative shaded bands | [Python](plugins/research-plots/examples/learning_curves.py) · [PDF](plugins/research-plots/examples/learning_curves.pdf) |
| Compute cost and prediction error | Single-column scatter plot with three method groups | [Python](plugins/research-plots/examples/cost_scatter.py) · [PDF](plugins/research-plots/examples/cost_scatter.pdf) |

Run either script from the repository root to save its PDF beside the source file.

```sh
uv run plugins/research-plots/examples/learning_curves.py
uv run plugins/research-plots/examples/cost_scatter.py
```

## Agents

### Slurm specialist

The Slurm Ops skill delegates cluster work to the `slurm_ops` specialist when delegation is available. For example, ask “Investigate why this job failed and suggest a change to the launcher.” The specialist inspects the job and its logs, then reports its findings and any changes. It inherits the parent session’s permissions and model settings. Before registration, the skill can use the bundled specialist instructions. Clients without delegation tools follow those instructions in the current session.

**Register a named specialist in Codex.** Invoke `$setup` and ask “Install the Slurm specialist for this project” or “Install the Slurm specialist for all my projects.” Start a new Codex session after registration.

| Scope | Installed agent definition |
| --- | --- |
| Current project | `.codex/agents/slurm_ops.toml` in the project |
| All projects | `agents/slurm_ops.toml` under `CODEX_HOME`, which defaults to `~/.codex` |

Keep the plugin enabled so the specialist can use its skills and helpers. After a plugin update, run setup again to update the registered definition and preserve local customizations. To remove the named specialist, delete its installed definition. See the [setup skill](skills/setup/SKILL.md) and [bundled agent definition](agents/slurm_ops.toml).

## Slurm Ops reference

### Execution environment

The helpers inspect the current environment and validate resource requests. On a workstation, they support local development and offline script preparation. On a cluster, they use locally available Slurm commands.

Diagnostics and resource validation are read-only. Follow the [common workflows](skills/slurm-ops/references/common.md) for launchers, job authorization, and uncertain submissions.

### Command-line helpers

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

The offline validator compares the effective job request with configured node capacities under the Helix proportional resource limits, weighting mixed H200 MIG profiles by their compute slices. The [resource validation reference](skills/slurm-ops/references/resource-preflight.md) contains the command, JSON schema, exit codes, and normalization requirements.

### Optional configuration

- User defaults: `$XDG_CONFIG_HOME/slurm-ops/config.json`, or `~/.config/slurm-ops/config.json` when `XDG_CONFIG_HOME` is unset.
- Project overrides: the nearest `.slurm-ops.json` in the current directory or an ancestor directory. Discovery also works outside Git repositories.

Explicit helper input takes precedence over project hints. Project hints override user defaults. A more specific account hint replaces the broader one. Storage hints are merged by name.

| Field | Type and purpose |
| --- | --- |
| `account` | String hint for the existing local account. |
| `storage` | Object mapping names to literal path strings used as storage hints. |

See [examples/config.json](examples/config.json). Setup writes configuration only when requested. Keep personal paths and accounts in local configuration. Never store credentials in the package. The site, execution role, and execution environment come from local observations.

### Hook behavior and limits

The shared Codex and Claude Code hook adapter is in `hooks/codex.py`. Shared command classification is in `slurm_ops/guard.py`.

- `SessionStart` gathers a compact read-only snapshot through local Slurm commands for startup, resume, clear, compaction, and fork. It reports node totals, node state counts, accounts for the current user, default QoS, relevant allowed QoS limits, and queue state counts. It lists all returned partitions with their state, wall-time limit, and default status. It omits node resource profiles, individual node records, job names, and daemon configuration. Collection has a ten-second total limit and a three-second limit per command. The hook timeout is twelve seconds.
- The snapshot reports missing commands, denied queries, timeouts, incomplete inventory, and omitted rows as limitations. Without local Slurm commands, startup produces a brief message that Slurm is unavailable. Hooks submit no jobs, install no dependencies, and change no caches.
- The hook points to the main skill for [helper commands](skills/slurm-ops/SKILL.md#helper-commands) and reference selection.
- `PreToolUse` matches the `Bash` event in Codex and Claude Code, including Codex unified execution. On confirmed login nodes, it denies recognized standard training and test commands. It allows lightweight diagnostics and commands that execute within an allocation.
- Command classification recognizes simple environment prefixes, `uv run`, and `uvx`. Complex or ambiguous shell forms receive advice.
- Project scripts receive agent review under the [execution location guidance](skills/slurm-ops/references/common.md#execution-location). Individual jobs require no registration.
- Hook errors allow execution to continue.

## Update or switch installations

| Client | Refresh the marketplace | Update an installed plugin |
| --- | --- | --- |
| Codex CLI | `codex plugin marketplace upgrade probai-plugin` | `codex plugin add slurm-ops@probai-plugin` |
| Claude Code | `/plugin marketplace update probai-plugin` | `/plugin update slurm-ops@probai-plugin` |

For Research Plots, replace `slurm-ops` with `research-plots` in the update command. Start a new session after updating.

To install from a local checkout, use its absolute path in the marketplace add command. When switching sources, remove the existing registration first with `codex plugin marketplace remove probai-plugin` or `/plugin marketplace remove probai-plugin`. If you used the former marketplace name, remove `slurm-ops-local` instead. Add the new source and reinstall the plugins you use.

## Marketplace maintenance

Register each plugin in the [Codex marketplace](.agents/plugins/marketplace.json) and the [Claude Code marketplace](.claude-plugin/marketplace.json). Slurm Ops lives at the repository root. Research Plots has its own [plugin directory](plugins/research-plots).

Keep the Slurm Ops manifest at `.codex-plugin/plugin.json`. In Codex `0.164.0-alpha.11.1`, adding a separate root `plugin.json` causes hook discovery to return an empty registry. Both clients use the [shared hook definitions](hooks/hooks.json).
