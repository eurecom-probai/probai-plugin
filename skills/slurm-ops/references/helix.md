# Helix

Follow these workflow and resource limits for Helix jobs. Scheduler-enforced limits may be more restrictive.

## Storage

- Keep code in `/users/$USER`.
- For a new layout, put active datasets, caches, checkpoints, and results in shared `/scratches/$USER`.
- `/scratch` is local to each compute node. Use it for temporary job data and local I/O. The same path on another node refers to separate storage.

Follow the [storage, staging, and cache rules](common.md#storage-staging-and-caches) for existing layouts, relocation, output recovery, and storage guarantees. Follow the [project environment guidance](common.md#prepare-and-select-a-launcher) for Python tooling.

## Development QoS and accelerators

Follow the [execution location rules](common.md#execution-location) for login-node activity and allocated compute execution.

For short development jobs, prefer `dev` QoS and the smallest suitable resources. Use [scheduler discovery](common.md#discover-before-requesting) to verify its current limits and eligibility. For longer jobs, explain the available QoS choices and ask which to use unless the user has already selected one.

Consider MIG slices, L40S, and full GPUs available in the current Helix inventory. Follow the [resource preparation guidance](common.md#prepare-and-run) when choosing an accelerator.

## Strict proportional resource ceiling

Always run the [`validate-resources` helper](resource-preflight.md) when preparing, reviewing, or submitting a Helix GPU job through any launcher. Supply the normalized effective request and the complete eligible-node inventory, including GPU/MIG profile counts. Require a `valid` result before submission. Rerun the check whenever the effective request or eligible-node inventory changes.

For each GPU job, compute the requested accelerator weight `w` and the configured total allocatable accelerator weight `W` on each eligible node, including busy resources. Limit CPUs, host memory, and other node resources to the fraction `w/W` of configured node capacity:

- CPUs: at most `floor(configured CPUs × w/W)` across the whole job.
- Host memory: at most `floor(configured memory × w/W)`, rounded down to the scheduler request unit.
- Other requested node resources: at most the same `w/W` share, with indivisible units rounded down.

For H200 inventories, weight a full GPU by 7 compute slices and an `ng` MIG profile by `n`: `1g.18gb` and `1g.35gb` each contribute 1, `2g.35gb` contributes 2, `3g.71gb` contributes 3, and `4g.71gb` contributes 4. These weights allocate host resources according to GPU compute slices. The profile's memory suffix identifies GPU memory capacity and remains part of the exact requested type.

Sum weights over the configured allocatable GRES inventory. Count each instance once; exclude backing GPUs, generic and typed TRES aliases, and alternative descriptions. For homogeneous inventories the share reduces to the requested instance count divided by the configured instance count. Mixed inventories require explicit requested types and known weights for every configured type. Resolve unknown profiles or ambiguous inventories before submission.

Apply the ceiling to total effective requests after launcher settings, environment variables, scheduler defaults, and scheduler adjustments. `--mem=0`, whole-node allocation, or exclusive requests are invalid when they exceed the proportional share.

For heterogeneous eligible nodes, use the most restrictive per-resource ceiling across all eligible nodes. Narrow eligibility with justified constraints if needed. Resolve unknown capacities, eligibility, defaults, or request semantics before submitting. For CPU-only jobs, follow the [resource preparation guidance](common.md#prepare-and-run).

Example: two full GPUs out of eight give `w/W=2/8`. A node with 128 configured CPUs and 524288 MiB configured memory permits at most **32 CPUs and 131072 MiB** (128 GiB).

## Typed GPU example

Example full H200 request: `--gpus=h200:1`.

## Verified profile example

Scheduler inspection on 12 November 2026 reported `helix03` with 128 CPUs, 1024000 MiB host memory, and these configured H200 NVL profiles: ten `1g.35gb`, four `4g.71gb`, four `3g.71gb`, and twelve `1g.18gb`. Its total allocatable compute weight is `10 + 16 + 12 + 12 = 50`. One `h200_nvl_4g.71gb` instance therefore permits at most 10 CPUs and 81920 MiB host memory (`4/50` of the node). One `h200_nvl_1g.35gb` instance permits 2 CPUs and 20480 MiB (`1/50`). Refresh the inventory and evaluate every eligible node before submission.
