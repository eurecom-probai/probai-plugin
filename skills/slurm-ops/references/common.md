# Common workflows

## Prepare and select a launcher

Read the project instructions, launcher, environment, testing rules, commit conventions, and output conventions first.

Reuse an existing launcher. When creating a new one, explain the choices and ask the user to choose:

- Native Slurm (`sbatch`, `srun`) fits shell workflows and gives direct control of scheduler options and logs.
- Submitit fits Python workflows and provides job handles, result retrieval, arrays, checkpoint support, and resubmission when the callable supports them. It adds a Python dependency and maps its parameters to scheduler options.

Use the selected approach consistently. Consider `uv` for project dependency management and `uvx` for standalone tools only when tooling is unspecified. Preserve module, virtualenv, Conda, container, or other explicit choices.

## Execution location

Limit login-node activity to lightweight operations such as static analysis, syntax validation, file inspection, and scheduler diagnostics. Run tests, benchmarks, training, and numerical work on allocated compute nodes. Read project code before running submission commands on login nodes. A Submitit executor or submission script can perform lightweight submission and schedule computation on compute nodes.

For interactive execution, request resources with `salloc`. Its shell may remain on the login node. Execute the workload through `srun` into the allocation, or verify that the process runs on the allocated compute node.

## Discover before requesting

Use fresh `inspect` results to verify job eligibility before submission. Treat missing, denied, timed-out, incomplete, or omitted scheduler data as unknown. Inspect relevant local details as necessary:

```sh
sinfo -o '%P %a %l %D %G'
scontrol show partition
scontrol show nodes -o
scontrol show config
squeue --me -o '%.18i %.9P %.30j %.8T %.10M %.6D %R'
```

Account associations and QoS may require `sacctmgr` access. Use the documented site environment initialization or existing project setup. Do not guess installation paths or install Slurm.

Inspect partition resource settings and defaults, typed GPUs, account and QoS eligibility, time limits, CPU counts, memory, and configured GPU inventory. Distinguish configured capacity from currently available capacity. Before preparing, reviewing, or submitting a Helix GPU request, follow the [Helix resource ceiling](helix.md#strict-proportional-resource-ceiling).

Use typed GPU requests when required by the selected partition. Select GPU and MIG type names from the current scheduler inventory.

## Prepare and run

Use explicit single-node resources, a useful job name, a time limit, and persistent logs. Choose the smallest CPU, memory, and accelerator requests that support the workload. Resolve task counts, CPUs per task, GPU count and type, and memory semantics together. Avoid `--mem=0`, exclusive nodes, or inherited environment defaults that expand the effective request unexpectedly. Preserve useful existing launcher settings. Avoid duplicate or conflicting flags. Each array element is a separately scheduled single-node job. Choose resources and concurrency for these jobs deliberately.

Use the helpers for diagnosis and validation. Perform authorized job launches, cancellations, and resubmissions through local shell commands and the project launcher. Submit only when a user request or existing authorization covers running the job. Reuse that authorization without repeated confirmation. Record the returned job ID and enough submission metadata to investigate failures or timeouts. Exclude credentials.

If submission times out or acceptance is uncertain, stop automatic retries. Inspect the user queue and recent accounting for the matching job name, user, working directory, submission time, and other available metadata. Recover the accepted job ID when possible. If acceptance remains unresolved, explain that a retry can duplicate work and obtain a user decision before submitting again. Continue honoring prior run authorization when acceptance is resolved.

## Diagnose and modify existing jobs

Use exact job IDs and inspect current state before acting. Typical local queries are:

```sh
squeue --me
scontrol show job JOB_ID
sacct -j JOB_ID --format=JobID,JobName,State,ExitCode,Elapsed,AllocCPUS,ReqMem,MaxRSS
```

Replace placeholders with verified IDs. Limit queries to the affected jobs and time range. Accounting may lag, and `MaxRSS` may be recorded only on job steps. Use pending reasons to distinguish resource pressure, priority, association and QoS limits, dependency problems, unavailable nodes, and invalid requests. Do not promise a start time or repeatedly poll by default.

Find standard output and error paths from the launcher or `scontrol show job`. Read limited portions. Use state, exit codes, step records, and logs to distinguish scheduler rejection, application failure, memory exhaustion, time-limit expiration, cancellation, preemption, and node failure. GPU memory failures are distinct from host-memory failures. Reduce the workload or revise resources within site ceilings. Preserve the resources allocated to other users on the same node.

Cancel only the intended authorized jobs or array elements using `scancel JOB_ID` or `scancel ARRAY_JOB_ID_TASK_ID`. Avoid commands that cancel all jobs unless explicitly requested. Verify the resulting state. Requeue only when authorized and when the application can restart safely. Verify application checkpoint support, checkpoint existence, persistent output paths, idempotence, and whether an array element or whole array is affected. Requeuing restarts execution.

## Storage, staging, and caches

Discover the actual existing data and output layout before creating another one. Preserve cache paths and cache environment variables. Relocate them when requested or when a demonstrated storage shortage requires it. Limit the change and explain the reason. Inspect space and quota on the affected filesystem when investigating a shortage.

For staging between shared storage and local compute-node storage, confirm the source, destination, available space, and output recovery paths. Stage inputs on the executing node. Keep durable checkpoints and results in a shared location when needed outside the node. Copy outputs before the allocation ends. Report copy failures and preserve the only remaining copy.

Verify quotas, archive destinations, retention, backup policies, and network restrictions in current site documentation when needed. Report missing information.
