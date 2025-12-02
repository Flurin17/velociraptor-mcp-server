from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def query_vql(cfg: ServerConfig, vql: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute arbitrary VQL and return results as a list of dicts.
    Note: params are not interpolated automatically; include them directly in VQL.
    """
    rows = get_client(cfg).query(vql, params=None)
    return {"rows": normalize_records(rows)}
