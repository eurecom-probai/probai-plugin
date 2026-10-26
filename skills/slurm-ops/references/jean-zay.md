# Jean Zay (IDRIS)

Use [common workflows](common.md) for single-node jobs and arrays. Run scheduler discovery on Jean Zay before finalizing a request. Keep personal accounts and paths in local configuration.

## Compute nodes run offline

CPU and GPU compute jobs run offline. Prepare the complete runnable environment, code, datasets, model weights, tokenizers, and other runtime assets before submission.

Use the login environment's configured HTTP/HTTPS access for lightweight downloads and metadata operations. Preserve its proxy configuration. External SSH destinations require IDRIS authorization. For substantial compilation, installation, preprocessing, or transfers, select an appropriate allocated service partition: `compil`, `compil_h100`, `prepost`, or `archive`. Verify the chosen service node's connectivity before downloading there. See [GENCI's internet access rules](https://www.edari.fr/documentation/index.php/Accueil#Services_d'acc%C3%A8s_%C3%A0_internet).

Reuse the project's environment and launcher. Discover installed software with `module avail`, `module show MODULE`, and the current IDRIS software documentation. Load the matching architecture module, such as `arch/a100` or `arch/h100`, before architecture-specific software. Record exact module versions and initialize them explicitly in the job. Compile native extensions for the target architecture on an appropriate allocated node.

Create custom Python environments at their final path on Jean Zay with the project's lockfile and compatible Python/CUDA stack. Keep that path throughout execution. Stage wheels and build requirements for offline installations. Invoke the prepared interpreter directly in compute jobs. For uv projects, use `uv run --offline --no-sync ...` with the prepared project environment. See [uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/).

Configure workload-specific offline behavior before imports. For Hugging Face, prefetch the required revisions and use the same cache paths during preparation and execution; set `HF_HUB_OFFLINE=1` for jobs. Use local paths or the library's local-files-only option when supported. A missing asset must fail with its path or revision so it can be staged before resubmission. Configure experiment trackers for local/offline logging and synchronize later from an internet-enabled environment. See [Hugging Face offline mode](https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables#hfhuboffline).

## Select the project and filesystem

Read the Jean Zay shell's variables and the existing project layout. The `inspect --json` helper reports recognized storage variables, including project-prefixed aliases. Use these paths for remote filesystem operations. Preserve existing cache settings and follow the [common storage rules](common.md#storage-staging-and-caches).

| Variable or space | Operational use |
| --- | --- |
| `$HOME` | Small configuration files. Keep large environments, caches, datasets, and job I/O in suitable project storage. |
| `$WORK` / `$CCFRWORK` | Personal directory within the active project's persistent work area; suitable for code, prepared environments, logs, and retained results. Back up retained files explicitly. |
| `$SCRATCH` / `$CCFRSCRATCH` | High-performance filesystem shared across cluster nodes for temporary bulk data and active job I/O. Unused files are subject to a 30-day purge; keep recoverable copies of inputs and retained outputs elsewhere. |
| `$STORE` / `$CCFRSTORE` | Tape-backed archival storage. Bundle suitable files into archives; stage archive inputs into WORK or SCRATCH before compute and transfer retained outputs back afterward. |
| `$ALL_CCFRWORK`, `$ALL_CCFRSCRATCH`, `$ALL_CCFRSTORE` | Project-shared directories with the corresponding filesystem's quota and retention. |
| Project-prefixed aliases | Variables such as `${PROJECT_CCFRWORK}` and `${PROJECT_ALL_CCFRWORK}` select a specific project's personal or shared directory. Discover the actual variable names; `PROJECT` is a placeholder. |
| `$DSDIR` | Site-provided datasets. Inspect the available dataset and reuse it when suitable. |
| `$JOBSCRATCH`, `$TMPDIR`, WORKSF or other advertised spaces | Inspect availability, mount type, capacity, lifetime, and permissions on the executing node before use. Treat job-temporary output as requiring recovery before the allocation ends. |

Resolve filesystem roots from the discovered environment variables. The unsuffixed variables select the active storage project. Match the storage project to the selected Slurm account: inspect membership and the active project with `idrproj`, then select the matching project-prefixed aliases. Preserve the user's default project.

Inspect current byte and inode quotas with `idr_quota_user` and `idr_quota_project`; consult their help for filters. The project report refreshes daily, so allow for recent writes. Shared directories and users' personal directories can consume the same project quota. Use `df -hT PATH` to identify the mount and filesystem space.

For a new layout, keep the reproducible environment and retained results in WORK, use SCRATCH for expendable large files, and archive valuable results to STORE or another agreed backup destination. Give each job or array element a separate temporary/output directory. Copy important checkpoints periodically so they survive interrupted allocations. Verify copies before deleting a source. Confirm current retention and archive guarantees when they matter.

## Match account, accelerator, and resources

Use current associations, partition configuration, node features, and QoS limits from `inspect`. Account suffixes identify CPU or accelerator allocations. Examples include `PROJECT@cpu`, `PROJECT@v100`, `PROJECT@a100`, and `PROJECT@h100`; select only an association available to the user.

The following partition names were observed through read-only scheduler queries on 2026-10-23. Discover their current features and eligibility before using them:

| Hardware or purpose | Observed partitions |
| --- | --- |
| CPU | `cpu_p1` |
| V100 | `gpu_p13`, `gpu_p2`, `gpu_p2s`, `gpu_p2l` |
| A100 | `gpu_p5` |
| H100 | `gpu_p6` |
| Preparation, compilation, archival transfers, visualization | `prepost`, `compil`, `compil_h100`, `archive`, `visu` |

Match the account suffix, GPU request, partition or constraint, modules, and QoS. Jean Zay uses architecture-specific features such as `a100`, `h100`, `v100-16g`, and `v100-32g`. GPU GRES may be untyped or typed depending on the partition; choose from the actual inventory. Development QoS names include `qos_cpu-dev`, `qos_gpu_a100-dev`, and `qos_gpu_h100-dev`; verify membership and limits. Set the job's time limit within the account, partition, and QoS limits.

Resolve CPU counts, tasks, GPU count, physical cores versus hardware threads, and associated host memory together. Inspect partition memory defaults and limits and the effective allocation. GPU architectures have different CPU/memory ratios. Request the resources the workload needs within IDRIS limits; review accounting before increasing CPUs, memory, or exclusivity. Validate Jean Zay requests using IDRIS rules and live scheduler evidence.

Keep `--nodes=1` for this skill's jobs and each array element. Prepare persistent log directories before submission: Slurm opens output files before the script runs. Resolve log and working-directory paths in the launcher or `sbatch` arguments. Execute workloads through `srun` with the prepared environment and explicit resource settings.

