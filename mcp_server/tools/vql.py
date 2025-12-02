from __future__ import annotations

from typing import Any, Dict

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def query_vql(cfg: ServerConfig, vql: str) -> Dict[str, Any]:
    """
    Execute arbitrary VQL and return results as a list of dicts.
    """
    rows = get_client(cfg).query(vql)
    return {"rows": normalize_records(rows)}
