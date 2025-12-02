from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_clients(
    cfg: ServerConfig, limit: int = 200, offset: int = 0
) -> Dict[str, Any]:
    """List enrolled clients."""
    vql = "SELECT * FROM clients()"
    rows = normalize_records(get_client(cfg).query(vql))
    return {"clients": rows[offset : offset + limit if limit else None]}


def get_client_info(cfg: ServerConfig, client_id: str) -> Dict[str, Any]:
    """Fetch detailed info for a client."""
    safe_client_id = client_id.replace("'", "''")
    vql = f"SELECT * FROM clients() WHERE client_id='{safe_client_id}'"
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
    predicates: list[str] = []
    if hostname:
        safe_hostname = hostname.replace("'", "''")
        predicates.append(f"Hostname =~ '{safe_hostname}'")
    if label:
        safe_label = label.replace("'", "''")
        predicates.append(f"Labels =~ '{safe_label}'")
    if query:
        predicates.append(query)
    where_clause = " WHERE " + " AND ".join(predicates) if predicates else ""
    vql = f"SELECT * FROM clients(){where_clause}"
    rows = normalize_records(get_client(cfg).query(vql))
    return {"clients": rows[:limit] if limit else rows}
