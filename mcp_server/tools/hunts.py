from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_hunts(cfg: ServerConfig, state: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
    predicate = ""
    if state:
        predicate = f" WHERE State = '{state}'"
    vql = f"SELECT * FROM hunts(){predicate} ORDER BY Created DESC LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"hunts": normalize_records(rows)}


def get_hunt_details(cfg: ServerConfig, hunt_id: str) -> Dict[str, Any]:
    vql = f"SELECT * FROM hunt_details(hunt_id='{hunt_id}')"
    rows = get_client(cfg).query(vql)
    return {"hunt": normalize_records(rows)}


def create_hunt(
    cfg: ServerConfig,
    artifact: str,
    query: str,
    description: str = "",
    start_immediately: bool = True,
) -> Dict[str, Any]:
    """
    Create a hunt by defining an artifact with provided VQL.
    """
    vql = f"""
LET hunt_artifact <= {{
    Name: '{artifact}',
    Description: '{description}',
    Sources: [{{Queries: [{{VQL: '''{query}'''}}]}}]
}};
SELECT create_hunt(artifact=hunt_artifact, start_immediately={str(start_immediately).lower()}) AS HuntId
"""
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def stop_hunt(cfg: ServerConfig, hunt_id: str) -> Dict[str, Any]:
    vql = f"SELECT stop_hunt(hunt_id='{hunt_id}') AS Stopped"
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def get_hunt_results(cfg: ServerConfig, hunt_id: str, client_id: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
    predicate = ""
    if client_id:
        predicate = f" WHERE ClientId = '{client_id}'"
    vql = f"SELECT * FROM hunt_results(hunt_id='{hunt_id}'){predicate} LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"results": normalize_records(rows)}
