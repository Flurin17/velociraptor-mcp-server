from __future__ import annotations

from typing import Any, Dict, List, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_clients(cfg: ServerConfig, limit: int = 200, offset: int = 0) -> Dict[str, Any]:
    """List enrolled clients."""
    vql = f"SELECT * FROM clients() LIMIT {limit} OFFSET {offset}"
    rows = get_client(cfg).query(vql)
    return {"clients": normalize_records(rows)}


def get_client_info(cfg: ServerConfig, client_id: str) -> Dict[str, Any]:
    """Fetch detailed info for a client."""
    vql = f"SELECT * FROM client_info(client_id='{client_id}')"
    rows = get_client(cfg).query(vql)
    return {"client": normalize_records(rows)}


def search_clients(
    cfg: ServerConfig,
    hostname: Optional[str] = None,
    label: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 200,
) -> Dict[str, Any]:
    """
    Search clients by hostname or labels using VQL filters.
    """
    predicates: List[str] = []
    if hostname:
        predicates.append(f"Hostname =~ '{hostname}'")
    if label:
        predicates.append(f"Labels =~ '{label}'")
    if query:
        predicates.append(query)
    where_clause = " WHERE " + " AND ".join(predicates) if predicates else ""
    vql = f"SELECT * FROM clients(){where_clause} LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"clients": normalize_records(rows)}
