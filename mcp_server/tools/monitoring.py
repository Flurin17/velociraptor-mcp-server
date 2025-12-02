from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def get_server_stats(cfg: ServerConfig) -> Dict[str, Any]:
    vql = "SELECT * FROM server_stats()"
    rows = get_client(cfg).query(vql)
    return {"stats": normalize_records(rows)}


def get_client_activity(cfg: ServerConfig, limit: int = 200) -> Dict[str, Any]:
    vql = f"SELECT * FROM client_activity() ORDER BY Timestamp DESC LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"activity": normalize_records(rows)}


def list_alerts(cfg: ServerConfig, limit: int = 200) -> Dict[str, Any]:
    vql = f"SELECT * FROM alerts() ORDER BY Timestamp DESC LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"alerts": normalize_records(rows)}


def create_alert(cfg: ServerConfig, title: str, message: str, client_id: Optional[str] = None, severity: str = "INFO") -> Dict[str, Any]:
    client_part = f"client_id='{client_id}'," if client_id else ""
    vql = f"""
SELECT create_alert(
    artifact="Custom.Alert",
    {client_part}
    title="{title}",
    message="{message}",
    severity="{severity}"
) AS AlertId
"""
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}
