"""Summarize read-only scheduler observations across agent applications."""

import json
import re
import unicodedata
from collections import Counter
from typing import Any, Optional


# Limit summary size separately from partition listings.
MAX_SUMMARY_BYTES = 2200


def _size(text: str) -> int:
    """Measure the ASCII-escaped JSON content length."""
    return len(json.dumps(text, ensure_ascii=True)) - 2


def _clean(value: Any, limit: Optional[int] = 80) -> str:
    if value is None:
        return "?"
    text = "".join("?" if unicodedata.category(char) in ("Cc", "Cf", "Zl", "Zp")
                   else char for char in str(value))
    return text if limit is None or len(text) <= limit else text[:max(0, limit - 3)] + "..."


def _clip(text: str, budget: int) -> str:
    if _size(text) <= budget:
        return text
    suffix = "..."
    left, right = 0, len(text)
    while left < right:
        middle = (left + right + 1) // 2
        if _size(text[:middle] + suffix) <= budget:
            left = middle
        else:
            right = middle - 1
    return text[:left] + suffix


def _items(prefix: str, values: list, budget: int, unit: str,
           maximum: int = 4) -> str:
    """Fit representative items while always disclosing omitted distinct items."""
    selected = []
    for value in values[:maximum]:
        remaining = len(values) - len(selected) - 1
        marker = "; +%d %s omitted" % (remaining, unit) if remaining else ""
        # Bound each item to preserve space for the remaining summary.
        candidate = _clip(value, min(120, max(30, budget - _size(prefix) - 55)))
        line = prefix + "; ".join(selected + [candidate]) + marker
        if _size(line) > budget:
            break
        selected.append(candidate)
    omitted = len(values) - len(selected)
    suffix = "; +%d %s omitted" % (omitted, unit) if omitted else ""
    return _clip(prefix + "; ".join(selected) + suffix, budget)


def _result(report: dict, key: str) -> dict:
    commands = report.get("commands", {})
    value = commands.get(key) if isinstance(commands, dict) else None
    return value if isinstance(value, dict) else {"status": "not queried"}


def _lines(result: dict) -> list:
    output = result.get("stdout", "")
    return [line.strip() for line in output.splitlines() if line.strip()] if isinstance(output, str) else []


def _fields(line: str) -> dict:
    return {match.group(1): match.group(2).strip() for match in re.finditer(
        r"(?:^|\s)([A-Za-z][A-Za-z0-9_/]*)=(.*?)(?=\s+[A-Za-z][A-Za-z0-9_/]*=|$)", line)}


def _table(result: dict, columns: int) -> tuple:
    rows, malformed = [], 0
    for line in _lines(result):
        values = line.split("|")
        if len(values) == columns + 1 and not values[-1]:
            values.pop()
        if len(values) != columns:
            malformed += 1
        else:
            rows.append(values)
    return rows, malformed


def _complete(result: dict, malformed: int = 0) -> bool:
    return result.get("status") == "ok" and not result.get("truncated") and not malformed



def format_snapshot(report: dict) -> str:
    """Format aggregate scheduler observations for session startup."""
    context = report.get("context", {})
    context = context if isinstance(context, dict) else {}
    header = _clip("Slurm %s | site=%s role=%s host=%s" % (
        _clean(report.get("observed_at", "unknown"), 32), _clean(context.get("site"), 20),
        _clean(context.get("role"), 20), _clean(context.get("hostname"), 70)), 180)
    commands = report.get("commands", {})
    commands = commands if isinstance(commands, dict) else {}
    raw_nodes = report.get("nodes", [])
    raw_nodes = raw_nodes if isinstance(raw_nodes, list) else []
    nodes = [node for node in raw_nodes if isinstance(node, dict)]
    if not nodes and commands and all(isinstance(value, dict) and value.get("status") == "missing"
                                      for value in commands.values()):
        return header + "\nLocal Slurm commands unavailable; no scheduler snapshot."

    problems = []

    def track(key: str, malformed: int = 0) -> dict:
        result = _result(report, key)
        flags = []
        if result.get("status") != "ok":
            flags.append(_clean(result.get("status", "unknown"), 16))
        if result.get("truncated"):
            flags.append("truncated")
        if malformed:
            flags.append("%d malformed" % malformed)
        if flags:
            problems.append(key + "=" + "/".join(flags))
        return result

    track("config")
    node_result = track("nodes", len(raw_nodes) - len(nodes))
    complete_nodes = bool(report.get("complete")) and _complete(node_result) and len(nodes) == len(raw_nodes)
    states = Counter(_clean(node.get("state"), 22) for node in nodes)
    state_rows = ["%s=%d" % pair for pair in sorted(states.items())]
    count = str(len(nodes)) if complete_nodes else ">=%d observed; partial" % len(nodes) if nodes else "unknown"
    node_line = _items("Nodes: %s" % count + ("; " if state_rows else ""), state_rows, 170, "states", 5)
    if any(node.get("issues") for node in nodes):
        problems.append("resource inventory needs review")

    partitions_result = _result(report, "partitions")
    partitions, bad_partitions = [], 0
    for line in _lines(partitions_result):
        fields = _fields(line)
        if not fields.get("PartitionName"):
            bad_partitions += 1
            continue
        state = fields.get("State", "?")
        value = _clean(fields["PartitionName"], None) + ("*" if fields.get("Default") == "YES" else "")
        value += "[" + _clean(state, 12)
        if fields.get("MaxTime"):
            value += ",wall=" + _clean(fields["MaxTime"], 22)
        partitions.append(value + "]")
    track("partitions", bad_partitions)
    if partitions:
        partial = "; partial" if not _complete(partitions_result, bad_partitions) else ""
        partition_line = "Partitions (*default%s): " % partial + "; ".join(dict.fromkeys(partitions))
    else:
        partition_line = "Partitions: unknown." if not _complete(partitions_result, bad_partitions) else "Partitions: none returned."

    associations_result = _result(report, "associations")
    associations, bad_associations = _table(associations_result, 6)
    accounts, allowed = {}, set()
    relative_membership = False
    for _, account, _, partition, qos_names, default in associations:
        if not account:
            bad_associations += 1
            continue
        item = accounts.setdefault(account, {"partitions": set(), "defaults": set()})
        if partition:
            item["partitions"].add(partition)
        if default:
            item["defaults"].add(default)
            allowed.add(default)
        # Keep relative +/- membership unresolved until effective membership is known.
        memberships = [name.strip() for name in qos_names.split(",") if name.strip()]
        relative_membership = relative_membership or any(name[0] in "+-" for name in memberships)
        allowed.update(name for name in memberships if name[0] not in "+-")
    track("associations", bad_associations)
    account_groups = {}
    for account, values in sorted(accounts.items()):
        key = (tuple(sorted(values["partitions"])), tuple(sorted(values["defaults"])))
        account_groups.setdefault(key, []).append(account)
    account_rows = []
    for (partitions, defaults), names in account_groups.items():
        details = []
        if partitions:
            details.append("part=" + ",".join(partitions))
        if defaults:
            details.append("default=" + ",".join(defaults))
        account_rows.append(_clean(",".join(names), 90) + ("[" + _clean(",".join(details), 80) + "]" if details else ""))
    account_line = _items("Accounts (you): ", account_rows, 240, "account groups", 4) if account_rows else "Accounts (you): unknown." if not _complete(associations_result, bad_associations) else "Accounts (you): none returned."

    qos_result = _result(report, "qos")
    qos_rows, bad_qos = _table(qos_result, 6)
    track("qos", bad_qos)
    qos_by_name = {row[0]: row for row in qos_rows if row[0]}
    qos_values = []
    for name in sorted(allowed):
        row = qos_by_name.get(name)
        if row is None:
            qos_values.append(_clean(name, 26) + "[limits unknown]")
            continue
        limits = []
        if row[1]:
            limits.append("wall=" + _clean(row[1], 22))
        qos_values.append(_clean(name, 26) + ("[" + ",".join(limits) + "]" if limits else "[wall unset]"))
    if not _complete(associations_result, bad_associations) or relative_membership:
        prefix = "QoS (observed allowed; eligibility partial): " if allowed else "QoS: eligibility unknown (accounts unavailable)."
    else:
        prefix = "QoS (allowed by associations): " if allowed else "QoS: eligibility unknown (no membership returned)."
    qos_line = _items(prefix, qos_values, 400, "QoS", 8) if qos_values else prefix

    queue_result = _result(report, "queue")
    queue_rows, bad_queue = _table(queue_result, 8)
    queue_states = Counter(_clean(row[3], 24) for row in queue_rows if row[3])
    if queue_rows and any(not row[3] for row in queue_rows):
        bad_queue += sum(not row[3] for row in queue_rows)
    track("queue", bad_queue)
    if _complete(queue_result, bad_queue):
        queue_summary = ["RUNNING=%d" % queue_states.pop("RUNNING", 0),
                         "PENDING=%d" % queue_states.pop("PENDING", 0)]
        queue_summary.extend("%s=%d" % pair for pair in sorted(queue_states.items()))
        queue_line = _items("Own queue: ", queue_summary, 150, "states", 5)
    elif queue_states:
        queue_line = _items("Own queue (partial observed): ", ["%s=%d" % pair for pair in sorted(queue_states.items())], 150, "states", 4)
    else:
        queue_line = "Own queue: unknown."

    lines = [header, node_line, partition_line, account_line, qos_line, queue_line]
    if problems:
        lines.append(_items("Status: ", problems, 240, "issues", 7))
    text = "\n".join(lines)
    assert _size(text) - _size(partition_line) <= MAX_SUMMARY_BYTES
    return text
