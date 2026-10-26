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

For each GPU job, let `k` be the number of requested allocatable GPU resources and `N` the **configured total allocatable GPU capacity of the node**, regardless of idle resources. Limit requests for CPUs, host memory, and other node resources to the fraction `k/N` of configured node capacity:

- CPUs: at most `floor(configured CPUs × k/N)` across the whole job.
- Host memory: at most `floor(configured memory × k/N)`, rounded down to the scheduler request unit.
- Other requested node resources: at most the same `k/N` share, with indivisible units rounded down.

Count MIG instances equally regardless of slice size. Build one allocatable instance inventory without counting backing GPUs, generic and typed TRES aliases, or alternative descriptions more than once. If the inventory is unclear, resolve it before submission.

Apply the ceiling to total effective requests after launcher settings, environment variables, scheduler defaults, and scheduler adjustments. `--mem=0`, whole-node allocation, or exclusive requests are invalid when they exceed the proportional share.

For heterogeneous eligible nodes, use the most restrictive per-resource ceiling across all eligible nodes. Narrow eligibility with justified constraints if needed. Resolve unknown capacities, eligibility, defaults, or request semantics before submitting. For CPU-only jobs, follow the [resource preparation guidance](common.md#prepare-and-run).

Example: `k=2`, `N=8`, 128 configured CPUs, and 524288 MiB configured memory permit at most **32 CPUs and 131072 MiB** (128 GiB). Apply this ceiling when preparing, reviewing, and submitting through every launcher. Use the [resource validation helper](resource-preflight.md) for normalized inventory and request JSON.

## Typed GPU example

Example full H200 request: `--gpus=h200:1`.

