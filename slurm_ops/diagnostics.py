"""Run read-only Slurm commands on the current host within fixed limits."""

import getpass
import os
import pwd
import re
import selectors
import shutil
import signal
import subprocess
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Mapping, Optional
from copy import deepcopy

from .context import CLUSTER_SITES, clean, detect_context

COMMAND_TIMEOUT = 3.0
TOTAL_TIMEOUT = 15.0
OUTPUT_LIMIT = 65536  # Combined stdout/stderr per command, bounded while reading.
NODE_OVERVIEW_LIMIT = 1024 * 1024
STORAGE_PATH_LIMIT = 4096
STORAGE_VARIABLES = frozenset({
    "HOME", "WORK", "SCRATCH", "STORE", "CCFRWORK", "CCFRSCRATCH", "CCFRSTORE",
    "ALL_CCFRWORK", "ALL_CCFRSCRATCH", "ALL_CCFRSTORE", "WORKSF", "ALL_CCFRWORKSF",
    "DSDIR", "JOBSCRATCH", "TMPDIR",
})
PROJECT_STORAGE_VARIABLE = re.compile(
    r"[A-Za-z][A-Za-z0-9_]*_(?:ALL_)?CCFR(?:WORKSF|WORK|SCRATCH|STORE)"
)


def _storage_paths(environ: Mapping[str, str]) -> dict:
    """Report allowlisted storage values without expanding or inspecting paths."""
    return {key: clean(environ[key], limit=STORAGE_PATH_LIMIT)
            for key in sorted(environ)
            if (key in STORAGE_VARIABLES or PROJECT_STORAGE_VARIABLE.fullmatch(key))
            and environ.get(key)}


def _kill(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def run_readonly(argv: list, timeout: float = COMMAND_TIMEOUT,
                 output_limit: int = OUTPUT_LIMIT) -> dict:
    """Run fixed arguments with output limits and process group cleanup."""
    result = {"command": argv, "status": "ok", "returncode": None,
              "stdout": "", "stderr": "", "truncated": False}
    if not shutil.which(argv[0]):
        result["status"] = "missing"
        return result
    if timeout <= 0:
        result["status"] = "deadline"
        return result
    env = dict(os.environ, LC_ALL="C", SLURM_PAGER="cat", PAGER="cat")
    try:
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, shell=False, env=env,
                                start_new_session=True)
    except OSError as exc:
        result.update(status="denied" if isinstance(exc, PermissionError) else "error",
                      stderr=clean(exc))
        return result
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    remaining = output_limit
    deadline = time.monotonic() + timeout
    selector = selectors.DefaultSelector()
    try:
        for label, stream in (("stdout", proc.stdout), ("stderr", proc.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            left = deadline - time.monotonic()
            if left <= 0:
                result["status"] = "timeout"
                _kill(proc)
                break
            for key, _ in selector.select(min(left, 0.05)):
                chunk = os.read(key.fd, min(8192, remaining + 1))
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffers[key.data].extend(chunk[:remaining])
                remaining -= min(remaining, len(chunk))
                if sum(len(b) for b in buffers.values()) >= output_limit:
                    result.update(status="output_limit", truncated=True)
                    _kill(proc)
                    break
            if result["status"] == "output_limit":
                break
        if result["status"] == "ok":
            try:
                proc.wait(timeout=max(0.001, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
                _kill(proc)
        proc.wait(timeout=1)
    finally:
        selector.close()
        if proc.poll() is None:
            _kill(proc)
            proc.wait(timeout=1)
        proc.stdout.close()
        proc.stderr.close()
    result["returncode"] = proc.returncode
    for label, data in buffers.items():
        result[label] = re.sub(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]", "?",
                               data.decode("utf-8", errors="replace"))
    if result["status"] == "ok" and proc.returncode:
        denied = re.search(r"permission denied|access denied|not authorized|not permitted",
                           result["stderr"], re.I)
        result["status"] = "denied" if denied else "error"
    return result


def parse_fields(line: str) -> dict:
    return {m.group(1): m.group(2).strip() for m in re.finditer(
        r"(?:^|\s)([A-Za-z][A-Za-z0-9_/]*)=(.*?)(?=\s+[A-Za-z][A-Za-z0-9_/]*=|$)", line)}


def _integer(value: Optional[str]) -> Optional[int]:
    try:
        result = int(value)
        return result if result >= 0 else None
    except (TypeError, ValueError):
        return None


def memory_mib(value: Optional[str]) -> Optional[int]:
    """Parse Slurm configured memory in MiB, with binary K/M/G/T suffixes."""
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([KMGT]?)", value or "", re.I)
    if not match:
        return None
    factor = {"": Fraction(1), "K": Fraction(1, 1024), "M": Fraction(1),
              "G": Fraction(1024), "T": Fraction(1024 ** 2)}[match.group(2).upper()]
    return int(Fraction(match.group(1)) * factor)


def gpu_inventory(gres: str, tres: dict) -> tuple:
    """Count allocatable gpu entries in GRES and compare the CfgTRES total."""
    entries = re.split(r",(?![^()]*\))", gres)
    types, untyped, errors = {}, False, []
    if any(part.split(":")[0] in ("mps", "shard") for part in entries):
        return None, {}, ["overlapping MPS/shard inventory needs explicit review"]
    for entry in entries:
        if not entry.startswith("gpu:"):
            continue
        match = re.fullmatch(r"gpu(?::([^:(),]+))?:(\d+)(?:\([^)]*\))?", entry)
        if not match:
            errors.append("unrecognized GPU GRES entry")
            continue
        kind = match.group(1) or "untyped"
        if kind in types:
            errors.append("duplicate GPU type inventory needs review")
        types[kind] = types.get(kind, 0) + int(match.group(2))
        untyped = untyped or kind == "untyped"
    if untyped and len(types) > 1:
        errors.append("mixed aggregate and typed GPU entries may double-count devices")
    count = sum(types.values())
    aggregate = _integer(tres.get("gres/gpu"))
    if aggregate is not None and count != aggregate:
        errors.append("GPU GRES and aggregate CfgTRES counts disagree")
    if not types and aggregate:
        errors.append("GPU aggregate lacks allocatable GRES inventory")
    return (None if errors else count), types, errors


def parse_nodes(output: str) -> list:
    nodes = []
    for line in output.splitlines():
        row = parse_fields(line)
        if "NodeName" not in row:
            continue
        tres = dict(item.split("=", 1) for item in row.get("CfgTRES", "").split(",")
                    if "=" in item)
        allocated = dict(item.split("=", 1) for item in row.get("AllocTRES", "").split(",")
                         if "=" in item)
        cpus = [v for v in (_integer(row.get("CPUTot")), _integer(row.get("CPUEfctv")),
                            _integer(tres.get("cpu"))) if v is not None]
        real = _integer(row.get("RealMemory"))
        reserved = _integer(row.get("MemSpecLimit", "0"))
        mems = [v for v in (memory_mib(tres.get("mem")),
                            real - reserved if real is not None and reserved is not None else None)
                if v is not None and v >= 0]
        gres = row.get("Gres", "")
        gpus, types, issues = gpu_inventory(gres, tres)
        if not gres:
            gpus = None
            issues.append("missing GRES field")
        nodes.append({"name": row["NodeName"], "cpus": min(cpus) if cpus else None,
                      "memory_mib": min(mems) if mems else None, "gpu_instances": gpus,
                      "allocated_cpus": _integer(row.get("CPUAlloc", allocated.get("cpu"))),
                      "allocated_memory_mib": _integer(row.get("AllocMem"))
                          if row.get("AllocMem") is not None else memory_mib(allocated.get("mem")),
                      "allocated_gpu_instances": _integer(allocated.get("gres/gpu")),
                      "gpu_types": types, "gres": gres, "state": row.get("State"),
                      "partitions": row.get("Partitions", "").split(","),
                      "features": row.get("AvailableFeatures"), "issues": issues})
    return nodes


def parse_node_overview(output: str) -> tuple:
    """Parse compact sinfo records for each node and merge duplicate partition rows.

    The overview summarizes node resources. Resource validation requires full
    inspection and separate identification of all eligible nodes.
    """
    nodes, complete = {}, True
    for line in output.splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) != 7:
            complete = False
            continue
        name, state, cpus, memory, gres, partition, cpu_states = (item.strip() for item in fields)
        if not name or any(char in name for char in "[],"):
            complete = False
            continue
        count, types, issues = gpu_inventory(gres, {})
        cpu_parts = cpu_states.split("/")
        allocated_cpus = _integer(cpu_parts[0]) if len(cpu_parts) == 4 else None
        record = {"name": name, "state": state.upper(), "cpus": _integer(cpus),
                  "memory_mib": memory_mib(memory), "gpu_instances": count,
                  "gpu_types": types, "gres": gres, "issues": issues,
                  "allocated_cpus": allocated_cpus,
                  "allocated_memory_mib": None, "allocated_gpu_instances": None,
                  "partitions": [partition.rstrip("*")] if partition else [],
                  "capacity_source": "sinfo overview"}
        if name in nodes:
            prior = nodes[name]
            prior["partitions"] = sorted(set(prior["partitions"] + record["partitions"]))
            for key in ("cpus", "memory_mib", "gpu_instances", "gpu_types"):
                if prior[key] != record[key]:
                    prior[key] = {} if key == "gpu_types" else None
                    complete = False
            continue
        nodes[name] = record
    return list(nodes.values()), complete and bool(nodes)


def current_user() -> str:
    """Prefer the effective OS identity over inherited LOGNAME/USER values."""
    try:
        return pwd.getpwuid(os.geteuid()).pw_name
    except (OSError, KeyError):
        try:
            return getpass.getuser()
        except (OSError, KeyError):
            return ""


def inspect_current_host(total_timeout: float = TOTAL_TIMEOUT,
                         command_timeout: float = COMMAND_TIMEOUT,
                         context: Optional[dict] = None,
                         compact_nodes: bool = False) -> dict:
    """Take a bounded snapshot; startup callers can select a shorter deadline."""
    deadline = time.monotonic() + total_timeout
    context = detect_context() if context is None else deepcopy(context)
    user = current_user()
    user_ok = bool(re.fullmatch(r"[A-Za-z0-9_.@-]{1,128}", user))
    overview = compact_nodes and bool(shutil.which("sinfo"))
    node_command = (["sinfo", "--Node", "--noheader", "--format=%N|%T|%c|%m|%G|%P|%C"]
                    if overview else ["scontrol", "--oneliner", "show", "nodes"])
    commands = [
        ("config", ["scontrol", "show", "config"]),
        ("nodes", node_command),
        ("partitions", ["scontrol", "--oneliner", "show", "partitions"]),
        ("qos", ["sacctmgr", "--noheader", "--parsable2", "show", "qos",
                 "format=Name,MaxWall,MaxTRESPU,MaxJobsPU,Flags,PreemptMode"]),
    ]
    if user_ok:
        commands.extend([
            ("associations", ["sacctmgr", "--noheader", "--parsable2", "show", "assoc",
                              "where", "user=" + user,
                              "format=Cluster,Account,User,Partition,QOS,DefaultQOS"]),
            ("queue", ["squeue", "--noheader", "--user", user,
                       "--format=%i|%P|%j|%T|%M|%l|%D|%R"]),
        ])
    results = {}
    for name, argv in commands:
        options = {"output_limit": NODE_OVERVIEW_LIMIT} if name == "nodes" and overview else {}
        results[name] = run_readonly(argv, timeout=min(command_timeout,
                                                      deadline - time.monotonic()), **options)
    config = {}
    allowed = {"ClusterName", "DefMemPerCPU", "DefMemPerNode", "DefMemPerGPU",
               "SelectType", "SelectTypeParameters", "GresTypes"}
    for line in results["config"]["stdout"].splitlines():
        if "=" in line:
            key, value = (part.strip() for part in line.split("=", 1))
            if key in allowed:
                config[key] = value
    # Retain only the selected configuration fields.
    results["config"]["stdout"] = "\n".join(k + "=" + v for k, v in config.items())
    cluster_name = config.get("ClusterName", "").lower()
    scheduler_site = CLUSTER_SITES.get(cluster_name)
    if context["site"] in ("local", "unknown") and scheduler_site:
        context["site"] = scheduler_site
        context["site_guidance"] = "available"
        if context["role"] == "local":
            context["role"] = "unknown"
        context["evidence"].append("local Slurm config reports " + cluster_name + "; role requires host/step evidence")
    elif scheduler_site and context["site"] != scheduler_site:
        context["evidence"].append("scheduler ClusterName conflicts with host/environment site evidence")
    nodes_result = results["nodes"]
    if overview:
        nodes, parsed_complete = parse_node_overview(nodes_result["stdout"])
    else:
        nodes = parse_nodes(nodes_result["stdout"])
        node_lines = [line for line in nodes_result["stdout"].splitlines() if line.strip()]
        parsed_complete = bool(nodes) and len(node_lines) == len(nodes) and all(node["name"] for node in nodes)
    listing_complete = nodes_result["status"] == "ok" and parsed_complete
    storage_paths = _storage_paths(os.environ)
    return {"observed_at": datetime.now(timezone.utc).isoformat(),
            "context": context, "complete": listing_complete,
            "inventory_kind": "overview" if overview else "detailed",
            "nodes": nodes, "scheduler_config": config, "commands": results,
            "shell_environment": {
                "module_initialization_advertised": any(os.environ.get(key) for key in (
                    "MODULESHOME", "LMOD_CMD", "BASH_FUNC_module%%")),
                "storage_variables_present": list(storage_paths),
                "storage_paths": storage_paths,
            },
            "notes": ["Scheduler inspection runs read-only commands.",
                      "Select all eligible nodes before resource validation. The scheduler determines placement.",
                      "Configured capacity determines Helix shares.",
                      "When module or storage variables are absent, verify shell initialization and available site facilities."]}
