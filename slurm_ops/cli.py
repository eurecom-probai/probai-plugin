"""Inspect the current host and validate normalized resource requests offline."""

import argparse
import json
import sys
from pathlib import Path

from .config import load_config
from .context import detect_context
from .diagnostics import inspect_current_host
from .resources import evaluate_request

MAX_INPUT_BYTES = 2 * 1024 * 1024


def _read_json(path: str):
    with Path(path).open("rb") as handle:
        raw = handle.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("JSON input exceeds 2 MiB")
    return json.loads(raw)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Slurm guidance diagnostics on the current host only.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("context", "inspect", "validate-resources"):
        command = commands.add_parser(name)
        command.add_argument("--json", action="store_true", help="emit structured JSON")
        if name == "validate-resources":
            command.add_argument("--inventory", required=True, help="JSON containing all eligible nodes")
            command.add_argument("--request", required=True, help="normalized effective request JSON")
    args = parser.parse_args(argv)
    code = 0
    if args.command == "context":
        report = detect_context()
        report["configuration"] = load_config()
    elif args.command == "inspect":
        report = inspect_current_host()
        report["configuration"] = load_config()
    else:
        try:
            inventory = _read_json(args.inventory)
            request = _read_json(args.request)
            if isinstance(inventory, dict):
                if inventory.get("inventory_kind") == "overview":
                    raise ValueError("Resource validation requires a detailed inventory; use detailed inspect")
                if inventory.get("complete") is not True:
                    raise ValueError("inventory must declare complete=true")
                nodes = inventory.get("nodes")
            else:
                nodes = inventory
            report = evaluate_request(nodes, request)
        except (OSError, ValueError, TypeError) as exc:
            report = {"status": "unresolved", "reasons": [str(exc)]}
        code = {"valid": 0, "invalid": 2}.get(report["status"], 3)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.command == "context":
        print("site={site} role={role} host={hostname}".format(**report))
        print("allocation=" + json.dumps(report["allocation"], sort_keys=True))
        for note in report["evidence"]:
            print("- " + note)
        for warning in report["configuration"]["warnings"]:
            print("config: " + warning)
    elif args.command == "inspect":
        print("Current-host Slurm inspection: " + report["context"]["site"])
        for name, result in report["commands"].items():
            print(name + ": " + result["status"])
            if result["stdout"]:
                print(result["stdout"])
            if result["stderr"]:
                print(result["stderr"], file=sys.stderr)
        print("Inventory complete: " + str(report["complete"]))
    else:
        print(report["status"])
        if "ceilings" in report:
            print("ceilings=" + json.dumps(report["ceilings"], sort_keys=True))
        for reason in report.get("reasons", []):
            print("- " + reason)
    return code
