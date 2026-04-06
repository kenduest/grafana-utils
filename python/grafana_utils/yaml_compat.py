"""YAML compatibility helpers with an optional PyYAML dependency."""

from __future__ import annotations

import json
from typing import Any

try:  # pragma: no cover - exercised only when PyYAML is available.
    import yaml as _yaml  # type: ignore
except Exception:  # pragma: no cover - fallback is covered by tests.
    _yaml = None


def safe_load(text: str) -> Any:
    """Load YAML when PyYAML is available, otherwise accept JSON-compatible YAML."""

    if _yaml is not None:  # pragma: no branch - tiny shim.
        return _yaml.safe_load(text)
    stripped = text.strip()
    if not stripped:
        return None
    return json.loads(stripped)


def safe_dump(data: Any) -> str:
    """Dump YAML when PyYAML is available, otherwise emit JSON-compatible YAML."""

    if _yaml is not None:  # pragma: no branch - tiny shim.
        return _yaml.safe_dump(data, sort_keys=False, default_flow_style=False)
    return json.dumps(data, indent=2, sort_keys=False)
