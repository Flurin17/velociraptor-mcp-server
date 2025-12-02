from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List


def normalize_records(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert generator/iterable to list of plain dicts."""
    return [dict(r) for r in rows]


def pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, default=str)
