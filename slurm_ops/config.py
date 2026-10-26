"""Read configuration hints while preserving the detected execution identity."""

import json
import os
from pathlib import Path
from typing import Mapping, Optional

MAX_CONFIG_BYTES = 32768
ALLOWED = {"account", "storage"}


def _validated(value: object, source: str, warnings: list) -> dict:
    if not isinstance(value, dict):
        warnings.append(source + ": expected a JSON object")
        return {}
    result = {}
    for key, item in value.items():
        if key not in ALLOWED:
            warnings.append(source + ": unsupported setting " + str(key)[:80])
        elif key == "account":
            if isinstance(item, str) and len(item) <= 160 and item.strip():
                result[key] = item
            else:
                warnings.append(source + ": invalid account")
        elif key == "storage":
            if isinstance(item, dict) and all(isinstance(k, str) and isinstance(v, str)
                                             for k, v in item.items()):
                result[key] = item
            else:
                warnings.append(source + ": storage must map names to path hints")
    return result


def load_config(cwd: Optional[str] = None, environ: Optional[Mapping[str, str]] = None,
                overrides: Optional[dict] = None) -> dict:
    env = os.environ if environ is None else environ
    base = Path(cwd or os.getcwd()).resolve()
    config_home = Path(env.get("XDG_CONFIG_HOME") or
                       str(Path(env.get("HOME", str(Path.home()))) / ".config"))
    paths = [config_home / "slurm-ops" / "config.json"]
    for parent in (base,) + tuple(base.parents):
        candidate = parent / ".slurm-ops.json"
        if candidate.is_file():
            paths.append(candidate)
            break
    settings = {"storage": {}}
    warnings, sources = [], []
    for path in paths:
        try:
            with path.open("rb") as handle:
                raw = handle.read(MAX_CONFIG_BYTES + 1)
            if len(raw) > MAX_CONFIG_BYTES:
                raise ValueError("configuration exceeds 32 KiB")
            layer = _validated(json.loads(raw), str(path), warnings)
        except FileNotFoundError:
            continue
        except (OSError, ValueError, UnicodeError) as exc:
            warnings.append(str(path) + ": " + str(exc)[:200])
            continue
        sources.append(str(path))
        for key, value in layer.items():
            if key == "storage":
                settings[key] = dict(settings[key], **value)
            else:
                settings[key] = value
    if overrides:
        for key, value in _validated(overrides, "arguments", warnings).items():
            if key == "storage":
                settings[key] = dict(settings[key], **value)
            else:
                settings[key] = value
    return {"settings": settings, "sources": sources, "warnings": warnings}
