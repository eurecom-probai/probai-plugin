"""Evaluate normalized, single-node Helix GPU requests without side effects.

``evaluate_request(nodes, request)`` uses configured node capacities.
``gpu_instances`` counts allocatable devices; ``gpu_types`` records profiles.
Mixed H200 inventories use compute-slice weights (full GPU: 7, ng profile: n).
Count-only inventories assert homogeneous resources.
Callers must resolve GRES aliases and overlapping GPU and MIG descriptions.
A missing count remains unknown. All resource quantities are integer counts
(memory in MiB).

Example::

    evaluate_request(
        [{"name": "gpu-node", "cpus": 128, "memory_mib": 524288,
          "gpu_instances": 8}],
        {"gpus": 2, "cpus": 32, "memory_mib": 131072},
    )["status"]  # "valid"

Explicit CPU totals use ``cpus``. Task CPU requests use ``ntasks`` and
``cpus_per_task``. Missing task values require known values in ``defaults``.
``defaults.cpus`` applies when both task fields are omitted. Memory uses one of
``memory_mib``, ``mem_per_cpu_mib``, or ``mem_per_gpu_mib``; absent explicit
memory requires exactly one known default: ``def_mem_per_node_mib``,
``def_mem_per_cpu_mib``, or ``def_mem_per_gpu_mib``. ``memory_mib=0`` and
``all_memory=True`` request all memory on the node. Unknown scheduler defaults
remain unresolved. Exclusive allocation is evaluated separately.

Result statuses are ``valid``, ``invalid`` (a definite violation or malformed
request), ``unresolved`` (unknown resource values or scheduler settings), and
``not_applicable`` (CPU-only). Definite violations take precedence over missing
information.
"""

import re
from typing import Any, Dict, List, Optional


def _integer(value: Any, minimum: int = 0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def gpu_profile_units(kind: str) -> Optional[int]:
    """Return H200 compute-slice units; a full H200 has seven units."""
    if kind in ("h200", "h200_nvl"):
        return 7
    match = re.fullmatch(r"h200(?:_nvl)?_([1-7])g\.\d+gb", kind)
    return int(match.group(1)) if match else None


def _typed_counts(value: Any) -> bool:
    return (isinstance(value, dict) and bool(value)
            and all(isinstance(key, str) and key and _integer(count, 1)
                    for key, count in value.items()))


def evaluate_request(nodes: List[dict], request: dict) -> dict:
    """Return a JSON-serializable assessment of proportional resource limits.

    ``nodes`` must contain every node eligible for the request, including busy
    nodes. Each has ``name``, ``cpus``, ``memory_mib``, ``gpu_instances``, and
    optionally ``gpu_types`` and ``other_resources``. Every requested other
    resource must have a configured count on each eligible node. The caller
    determines eligibility and normalizes launcher and scheduler settings. The function evaluates
    resource limits offline.
    """
    invalid: List[str] = []
    unresolved: List[str] = []
    ceilings: Dict[str, Any] = {"cpus": None, "memory_mib": None, "other_resources": {}}
    effective: Dict[str, Any] = {
        "gpus": None, "cpus": None, "memory_mib": None,
        "nodes": 1, "exclusive": False, "all_memory": False,
        "other_resources": {},
    }

    def result(status: Optional[str] = None) -> dict:
        if status is None:
            status = "invalid" if invalid else "unresolved" if unresolved else "valid"
        return {"status": status, "ceilings": ceilings,
                "effective_request": effective, "reasons": invalid + unresolved}

    if not isinstance(request, dict):
        invalid.append("Request must be an object.")
        return result()
    k = request.get("gpus")
    if k is None:
        unresolved.append("Requested GPU count is unknown.")
        return result()
    if not _integer(k):
        invalid.append("Requested gpus must be a nonnegative integer.")
        return result()
    effective["gpus"] = k
    if k == 0:
        return result("not_applicable")

    supported = {"gpus", "cpus", "ntasks", "cpus_per_task", "memory_mib",
                 "mem_per_cpu_mib", "mem_per_gpu_mib", "defaults", "nodes",
                 "exclusive", "all_memory", "other_resources", "gpu_types"}
    unknown = sorted(str(key) for key in request if key not in supported)
    if unknown:
        unresolved.append("Unnormalized request fields need review: " + ", ".join(unknown) + ".")

    requested_types = request.get("gpu_types")
    if requested_types is not None:
        if not _typed_counts(requested_types):
            invalid.append("Requested gpu_types must map type names to positive integer counts.")
            requested_types = None
        elif sum(requested_types.values()) != k:
            invalid.append("Requested gpu_types counts must sum to gpus.")
    effective["gpu_types"] = requested_types

    node_count = request.get("nodes", 1)
    effective["nodes"] = node_count
    if not _integer(node_count, 1):
        invalid.append("Requested nodes must be a positive integer.")
    elif node_count != 1:
        invalid.append("Only single-node requests are supported.")

    for flag in ("exclusive", "all_memory"):
        value = request.get(flag, False)
        if not isinstance(value, bool):
            invalid.append("%s must be a boolean." % flag)
        else:
            effective[flag] = value

    defaults = request.get("defaults", {})
    if not isinstance(defaults, dict):
        invalid.append("Request defaults must be an object.")
        defaults = {}
    known_defaults = {"cpus", "ntasks", "cpus_per_task", "def_mem_per_node_mib",
                      "def_mem_per_cpu_mib", "def_mem_per_gpu_mib"}
    unknown_defaults = sorted(str(key) for key in defaults if key not in known_defaults)
    if unknown_defaults:
        unresolved.append("Unnormalized scheduler defaults need review: " +
                          ", ".join(unknown_defaults) + ".")

    def quantity(value: Any, label: str, minimum: int = 1) -> Optional[int]:
        if value is None:
            unresolved.append("%s is unknown." % label)
            return None
        if not _integer(value, minimum):
            invalid.append("%s must be an integer >= %d." % (label, minimum))
            return None
        return value

    # The caller must provide known site defaults and launcher behavior.
    explicit_tasks = "ntasks" in request or "cpus_per_task" in request
    if "cpus" in request:
        if explicit_tasks:
            invalid.append("Total cpus and task CPU fields are mutually exclusive.")
        effective["cpus"] = quantity(request["cpus"], "Requested total CPUs")
    elif not explicit_tasks and "cpus" in defaults:
        effective["cpus"] = quantity(defaults["cpus"], "Default total CPUs")
    else:
        ntasks = quantity(request.get("ntasks", defaults.get("ntasks")), "Effective ntasks")
        per_task = quantity(request.get("cpus_per_task", defaults.get("cpus_per_task")),
                            "Effective CPUs per task")
        effective["ntasks"] = ntasks
        effective["cpus_per_task"] = per_task
        if ntasks is not None and per_task is not None:
            effective["cpus"] = ntasks * per_task

    memory_fields = [key for key in ("memory_mib", "mem_per_cpu_mib", "mem_per_gpu_mib")
                     if key in request]
    if len(memory_fields) > 1:
        invalid.append("Use only one explicit memory request form.")
    elif memory_fields:
        key = memory_fields[0]
        value = quantity(request[key], "Requested " + key, 0 if key == "memory_mib" else 1)
        if key == "memory_mib" and value == 0:
            effective["all_memory"] = True
        elif effective["all_memory"]:
            invalid.append("all_memory conflicts with an explicit nonzero memory request.")
        elif value is not None:
            if key == "memory_mib":
                effective["memory_mib"] = value
            elif key == "mem_per_gpu_mib":
                effective["memory_mib"] = value * k
            elif effective["cpus"] is not None:
                effective["memory_mib"] = value * effective["cpus"]
    elif not effective["all_memory"]:
        memory_defaults = [key for key in (
            "def_mem_per_node_mib", "def_mem_per_cpu_mib", "def_mem_per_gpu_mib")
            if defaults.get(key) is not None]
        if not memory_defaults:
            unresolved.append("Effective memory is unknown; inspect scheduler defaults or request it explicitly.")
        elif len(memory_defaults) > 1:
            unresolved.append("Multiple memory defaults are present; resolve the applicable scheduler semantics.")
        else:
            key = memory_defaults[0]
            value = quantity(defaults[key], "Default " + key,
                             0 if key == "def_mem_per_node_mib" else 1)
            if key == "def_mem_per_node_mib" and value == 0:
                effective["all_memory"] = True
            elif value is not None:
                if key == "def_mem_per_node_mib":
                    effective["memory_mib"] = value
                elif key == "def_mem_per_gpu_mib":
                    effective["memory_mib"] = value * k
                elif effective["cpus"] is not None:
                    effective["memory_mib"] = value * effective["cpus"]

    other = request.get("other_resources", {})
    if not isinstance(other, dict):
        invalid.append("Requested other_resources must be an object.")
        other = {}
    for resource, value in other.items():
        if not isinstance(resource, str) or not resource or resource in (
                "cpus", "memory_mib", "gpus", "gpu_instances"):
            invalid.append("Other resources must have nonempty, nonreserved names.")
            continue
        amount = quantity(value, "Requested " + resource, 0)
        if amount is not None:
            effective["other_resources"][resource] = amount

    if not isinstance(nodes, list) or not nodes:
        unresolved.append("The complete eligible node inventory is unavailable.")
        return result()

    capacity_keys = ["cpus", "memory_mib"]
    limits: Dict[str, List[int]] = {key: [] for key in capacity_keys}
    other_limits: Dict[str, List[int]] = {key: [] for key in effective["other_resources"]}
    shares = []
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            unresolved.append("Eligible node %d is malformed." % index)
            continue
        name = node.get("name") or "node[%d]" % index
        if node.get("issues"):
            unresolved.append("Resolve scheduler inventory issues for %s before validation." % name)
        n = node.get("gpu_instances")
        if not _integer(n):
            unresolved.append("Resolve the configured GPU/MIG instance count for %s." % name)
            continue
        if k > n:
            invalid.append("%s has %d configured GPU/MIG instances, fewer than the requested %d." % (name, n, k))
        if n == 0:
            continue
        numerator, denominator = k, n
        types = node.get("gpu_types")
        if types is not None:
            if not _typed_counts(types) or sum(types.values()) != n:
                unresolved.append("For %s, reconcile gpu_types with gpu_instances." % name)
                continue
            selected = requested_types
            if selected is None:
                if len(types) == 1:
                    selected = {next(iter(types)): k}
                else:
                    unresolved.append("For %s, specify requested gpu_types for its mixed inventory." % name)
                    continue
            for kind, count in selected.items():
                if count > types.get(kind, 0):
                    invalid.append("%s has insufficient configured instances of %s." % (name, kind))
            # Homogeneous types have equal shares even when their profile is unknown.
            if len(types) > 1:
                units = {kind: gpu_profile_units(kind) for kind in types}
                if any(value is None for value in units.values()):
                    unresolved.append("For %s, resolve compute weights for every GPU profile." % name)
                    continue
                if any(kind not in units for kind in selected):
                    continue
                numerator = sum(count * units[kind] for kind, count in selected.items())
                denominator = sum(count * units[kind] for kind, count in types.items())
        elif requested_types is not None:
            unresolved.append("For %s, provide gpu_types to verify the typed request." % name)
            continue
        shares.append({"node": name, "requested_units": numerator,
                       "configured_units": denominator})
        if numerator < denominator:
            if effective["exclusive"]:
                invalid.append("Exclusive allocation on %s exceeds the %d/%d resource share." %
                               (name, numerator, denominator))
            if effective["all_memory"]:
                invalid.append("All-node memory on %s exceeds the %d/%d memory share." %
                               (name, numerator, denominator))
        for key in capacity_keys:
            capacity = node.get(key)
            if not _integer(capacity, 1):
                unresolved.append("For %s, resolve the configured %s capacity." % (name, key))
                continue
            ceiling = capacity * numerator // denominator
            limits[key].append(ceiling)
            amount = effective[key]
            if amount is not None and amount > ceiling:
                invalid.append("Requested %s=%d exceeds the limit on %s: %d/%d share with a ceiling of %d." %
                               (key, amount, name, numerator, denominator, ceiling))
        node_other = node.get("other_resources", {})
        for resource, amount in effective["other_resources"].items():
            capacity = node_other.get(resource) if isinstance(node_other, dict) else None
            if not _integer(capacity):
                unresolved.append("For %s, resolve the configured %s capacity." % (name, resource))
                continue
            ceiling = capacity * numerator // denominator
            other_limits[resource].append(ceiling)
            if amount > ceiling:
                invalid.append("Requested %s=%d exceeds the limit on %s: %d/%d share with a ceiling of %d." %
                               (resource, amount, name, numerator, denominator, ceiling))

    ceilings["gpu_shares"] = shares

    # Global ceilings require complete data for every eligible node.
    # Known violations take precedence over missing information.
    for key, values in limits.items():
        if len(values) == len(nodes):
            ceilings[key] = min(values)
    for key, values in other_limits.items():
        ceilings["other_resources"][key] = min(values) if len(values) == len(nodes) else None
    return result()
