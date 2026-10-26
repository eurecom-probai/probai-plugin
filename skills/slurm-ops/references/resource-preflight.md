# Resource validation

Use the offline `validate-resources` helper to validate a normalized single-node GPU request against [the Helix proportional resource ceiling](helix.md#strict-proportional-resource-ceiling). Follow [scheduler discovery](common.md#discover-before-requesting) and [job authorization](common.md#prepare-and-run) for submission.

## Invocation

Resolve `<plugin-root>` using the [helper command guidance](../SKILL.md#helper-commands). Replace the placeholders below with actual absolute paths and retain the quotes. Invoke the helper from any working directory.

```sh
python3 "<plugin-root>/scripts/slurm_ops.py" validate-resources --inventory "/absolute/path/inventory.json" --request "/absolute/path/request.json" --json
```

Both JSON files are local inputs, limited to 2 MiB each. Omit `--json` for a short text report.

## Node inventory

Inventory must include **every eligible node** for the intended partition, GPU type, account, constraints, and other placement requirements, including busy nodes. Normalize configured capacities according to the [Helix resource policy](helix.md#strict-proportional-resource-ceiling).

The inventory object requires `complete: true` and a `nodes` list of objects with the fields below. A bare list of node objects is also accepted as an assertion that the inventory is complete.

| Node field | Meaning |
| --- | --- |
| `name` | Node identity for diagnostics. |
| `cpus` | Configured CPU capacity as a positive integer. |
| `memory_mib` | Configured host-memory capacity in integer MiB. |
| `gpu_instances` | Configured allocatable GPU or MIG instance count, including busy instances. |
| `other_resources` | Optional object mapping other resource names to configured integer counts. |

The `inspect` helper provides normalized node evidence. Its `complete` field describes a successfully parsed node listing. Filter and verify that listing for job eligibility, and resolve aliases or MIG ambiguity before asserting a complete eligible inventory. Build the eligible-node inventory from detailed scheduler records and refresh them before submission.

## Effective request

Normalize the effective request from the actual launcher before validation. Include scheduler adjustments, task totals, `SBATCH_*` and `SRUN_*` environment settings, and partition defaults. All resource quantities are integer counts. Boolean values are invalid as counts.

| Request field | Meaning |
| --- | --- |
| `gpus` | Requested allocatable GPU or MIG count. Required. Zero produces `not_applicable`. |
| `cpus` | Total requested CPUs. Mutually exclusive with explicit task CPU fields. |
| `ntasks`, `cpus_per_task` | Alternative CPU form: the total is their product. Both effective values must be known. |
| `memory_mib` | Total requested host memory in MiB. Zero means all-node memory. |
| `mem_per_cpu_mib` | Alternative memory form: multiply by effective total CPUs. |
| `mem_per_gpu_mib` | Alternative memory form: multiply by requested GPUs. |
| `nodes` | Optional node count. Defaults to one and must equal one. |
| `exclusive`, `all_memory` | Optional booleans. Default to false. Requests for a whole node or all memory must satisfy the same proportional ceiling. |
| `other_resources` | Optional object mapping resource names to requested nonnegative integer counts. Each requested resource needs a configured capacity on every eligible node. |
| `defaults` | Optional known scheduler defaults, described below. |

Use exactly one explicit memory form. Do not combine `all_memory: true` with an explicit nonzero memory request. Convert unsupported request forms, such as CPU-per-GPU options, into the supported effective totals. Do not add unrecognized fields. Unrecognized request and default fields need review and remain unresolved.

If explicit CPU values are absent, `defaults` can contain `cpus`, or `ntasks` and `cpus_per_task`. Missing task values can also come from these defaults when one task field is explicit. When explicit memory is absent, provide exactly one applicable memory default:

- `def_mem_per_node_mib`: total memory. Zero means all-node memory.
- `def_mem_per_cpu_mib`: memory multiplied by effective total CPUs.
- `def_mem_per_gpu_mib`: memory multiplied by requested GPUs.

Provide defaults only after establishing their actual effective values.

## Results and limits

Evaluated requests return `status`, `ceilings`, `effective_request`, and `reasons`. Failures while reading inputs return `status` and `reasons`. Exit codes are:

| Exit | Status | Action |
| --- | --- | --- |
| 0 | `valid` | The normalized GPU request satisfies the proportional limit for the provided inventory. |
| 2 | `invalid` | Correct the definite resource violation or malformed request before submission. |
| 3 | `unresolved` | Resolve missing or ambiguous inputs before submission. |
| 3 | `not_applicable` | CPU-only request. Follow the [resource preparation guidance](common.md#prepare-and-run). |

A definite violation takes precedence over missing information. Continue to enforce the resource ceiling after any nonzero exit status. Verify that the JSON inputs match the current job request and eligible inventory before submission.
