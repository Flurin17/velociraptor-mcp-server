"""Tool entrypoints to be registered with FastMCP."""

from .vql import query_vql
from .clients import list_clients, get_client_info, search_clients
from .hunts import list_hunts, get_hunt_details, create_hunt, stop_hunt, get_hunt_results
from .artifacts import (
    list_artifacts,
    collect_artifact,
    upload_artifact,
    get_artifact_definition,
)
from .files import download_file, list_directory, get_file_info
from .monitoring import get_server_stats, get_client_activity, list_alerts, create_alert

__all__ = [
    "query_vql",
    "list_clients",
    "get_client_info",
    "search_clients",
    "list_hunts",
    "get_hunt_details",
    "create_hunt",
    "stop_hunt",
    "get_hunt_results",
    "list_artifacts",
    "collect_artifact",
    "upload_artifact",
    "get_artifact_definition",
    "download_file",
    "list_directory",
    "get_file_info",
    "get_server_stats",
    "get_client_activity",
    "list_alerts",
    "create_alert",
]
