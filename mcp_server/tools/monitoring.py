from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_server.config import ServerConfig


def get_server_stats(cfg: ServerConfig) -> Dict[str, Any]:
    # server_stats plugin is not available in Velociraptor 0.75 lab.
    raise RuntimeError("server_stats is not supported by this Velociraptor version")


def get_client_activity(cfg: ServerConfig, limit: int = 200) -> Dict[str, Any]:
    raise RuntimeError("client_activity is not supported by this Velociraptor version")


def list_alerts(cfg: ServerConfig, limit: int = 200) -> Dict[str, Any]:
    raise RuntimeError("alerts are not supported by this Velociraptor version")


def create_alert(
    cfg: ServerConfig,
    title: str,
    message: str,
    client_id: Optional[str] = None,
    severity: str = "INFO",
) -> Dict[str, Any]:
    raise RuntimeError("create_alert is not supported by this Velociraptor version")
