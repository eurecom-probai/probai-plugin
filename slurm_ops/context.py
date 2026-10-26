"""Detect site and execution location from local process information."""

import os
import re
import socket
from typing import Any, Mapping, Optional

CLUSTER_SITES = {"eurecom": "helix", "jean-zay": "jean-zay"}
IDRIS_LOGIN_HOSTS = {"jean-zay1", "jean-zay2", "jean-zay3", "jean-zay4", "jean-zay5"}


def clean(value: Any, limit: int = 160) -> str:
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "?", str(value))[:limit]


def _host(value: str) -> str:
    return value.strip().lower().rstrip(".")


def detect_context(environ: Optional[Mapping[str, str]] = None,
                   hostname: Optional[str] = None) -> dict:
    """Use process-local evidence only; never run commands or resolve DNS."""
    env = os.environ if environ is None else environ
    host = _host(socket.gethostname() if hostname is None else hostname)
    short_host = host.split(".", 1)[0]
    idris_login = short_host in IDRIS_LOGIN_HOSTS and (host == short_host or host.endswith(".idris.fr"))
    cluster = env.get("SLURM_CLUSTER_NAME", "").strip().lower()
    evidence = []
    site = "unknown"
    if cluster == "eurecom":
        site = "helix"
        evidence.append("SLURM_CLUSTER_NAME=eurecom")
    elif cluster == "jean-zay":
        site = "jean-zay"
        evidence.append("SLURM_CLUSTER_NAME=jean-zay")
    if host == "login.helix.eurecom.fr" or host.endswith(".helix.eurecom.fr"):
        if site not in ("unknown", "helix"):
            evidence.append("conflicting site evidence")
            site = "unknown"
        else:
            site = "helix"
            evidence.append("Helix hostname suffix")
    if idris_login:
        if site not in ("unknown", "jean-zay"):
            evidence.append("conflicting site evidence")
            site = "unknown"
        else:
            site = "jean-zay"
            evidence.append("known IDRIS login identity")

    allocation = {}
    for key, names in {
        "job_id": ("SLURM_JOB_ID", "SLURM_JOBID"),
        "step_id": ("SLURM_STEP_ID", "SLURM_STEPID"),
        "node_name": ("SLURMD_NODENAME",),
        "node_list": ("SLURM_JOB_NODELIST", "SLURM_NODELIST"),
        "step_node_list": ("SLURM_STEP_NODELIST",),
        "partition": ("SLURM_JOB_PARTITION",),
        "account": ("SLURM_JOB_ACCOUNT",),
        "qos": ("SLURM_JOB_QOS",),
    }.items():
        for name in names:
            if env.get(name):
                allocation[key] = clean(env[name])
                break

    # Identify login hosts by their exact names; exclude numbered compilation nodes.
    if host == "login.helix.eurecom.fr" or idris_login:
        role = "login"
        evidence.append("known login hostname sets role=login")
    else:
        node = _host(env.get("SLURMD_NODENAME", ""))
        node_matches = bool(node and (node == host or (
            ("." not in node or "." not in host) and node.split(".")[0] == host.split(".")[0])))
        step = env.get("SLURM_STEP_ID") or env.get("SLURM_STEPID")
        singleton_step_host = _host(env.get("SLURM_STEP_NODELIST", "")) == host
        if allocation.get("job_id") and step and (node_matches or singleton_step_host):
            role = "compute"
            evidence.append("job and step evidence match this execution host")
        elif site != "unknown" or cluster or allocation or any(env.get(k) for k in (
                "SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY", "SLURM_CONF")):
            role = "unknown"
            evidence.append("remote or Slurm environment detected; execution role remains unknown")
        else:
            site, role = "local", "local"
            evidence.append("no cluster, allocation, or remote-session evidence")

    return {"site": site, "role": role, "hostname": clean(host),
            "allocation": allocation, "evidence": evidence,
            "site_guidance": "available" if site in ("local", "helix", "jean-zay") else "unconfigured"}
