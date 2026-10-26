#!/usr/bin/env python3
"""Provide slurm-ops guidance to Codex; return silently after errors."""

import sys

sys.dont_write_bytecode = True

import argparse
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT))

MAX_INPUT_BYTES = 131072
# Preserve all partition names within query output limits.
MAX_OUTPUT_BYTES = 256 * 1024
SNAPSHOT_TIMEOUT = 10.0
SNAPSHOT_COMMAND_TIMEOUT = 3.0


def _read_event(stream):
    raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        return None
    if not raw.strip():
        return {}
    value = json.loads(raw)
    return value if isinstance(value, dict) else None


def _session_start(context, snapshot=None):
    site = context.get("site", "unknown")
    role = context.get("role", "unknown")
    guidance = "Read {}.".format(PLUGIN_ROOT / "skills/slurm-ops/SKILL.md")
    message = snapshot + "\n" + guidance if snapshot else (
        "slurm-ops: site={}, role={}. ".format(site, role) + guidance)
    return {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": message}}


def handle_event(event_name, event):
    """Return hook JSON or None; main handles exceptions."""
    from slurm_ops.context import detect_context

    if event_name == "session-start":
        context = detect_context()
        try:
            from slurm_ops.diagnostics import inspect_current_host
            from slurm_ops.snapshot import format_snapshot

            report = inspect_current_host(total_timeout=SNAPSHOT_TIMEOUT,
                                          command_timeout=SNAPSHOT_COMMAND_TIMEOUT,
                                          context=context, compact_nodes=True)
            snapshot = format_snapshot(report)
            context = report.get("context", context)
        except Exception:
            result = _session_start(context)
            result["hookSpecificOutput"]["additionalContext"] += "\nSlurm startup snapshot unavailable."
            return result
        return _session_start(context, snapshot)
    if event.get("tool_name") != "Bash":
        return None
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command", tool_input.get("cmd"))
    if not isinstance(command, str):
        return None
    from slurm_ops.guard import classify_command

    result = classify_command(command, detect_context())
    output = {"hookEventName": "PreToolUse"}
    if result["decision"] == "deny":
        output.update(permissionDecision="deny", permissionDecisionReason=result["reason"])
    elif result["decision"] == "advisory":
        output["additionalContext"] = result["reason"]
    else:
        return None  # Never return permissionDecision=allow or bypass approval.
    return {"hookSpecificOutput": output}


def main(argv=None, stream=None, output=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event", choices=("session-start", "pre-tool-use"), required=True)
    args = parser.parse_args(argv)
    try:
        event = _read_event(stream if stream is not None else sys.stdin.buffer)
        if event is None:
            return 0
        result = handle_event(args.event, event)
        if result is not None:
            encoded = json.dumps(result, ensure_ascii=True)
            if len(encoded.encode("utf-8")) <= MAX_OUTPUT_BYTES:
                (output if output is not None else sys.stdout).write(encoded + "\n")
    except Exception:
        # Hook errors must leave the session usable. Ignore malformed input,
        # unavailable modules or configuration, and adapter errors.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
