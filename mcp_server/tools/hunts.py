from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_hunts(
    cfg: ServerConfig, state: Optional[str] = None, limit: int = 100
) -> Dict[str, Any]:
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
    Create a hunt by defining an inline artifact with provided VQL.

    Velociraptor 0.75 exposes hunt() (function) rather than create_hunt() (plugin),
    and it must be invoked with FROM scope().
    """
    vql = (
        "SELECT hunt(description='{description}', artifacts=['{artifact}'], "
        "start_immediately={start_immediately}, "
        "artifact_doc={{Name:'{artifact}',Description:'{description}',Sources:[{{Queries:[{{VQL:'''{query}'''}}]}}]}}) "
        "AS Hunt FROM scope()"
    ).format(
        description=description,
        artifact=artifact,
        query=query.replace("'", "''"),
        start_immediately=str(start_immediately).lower(),
    )
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def stop_hunt(cfg: ServerConfig, hunt_id: str) -> Dict[str, Any]:
    # There is no stop_hunt plugin in v0.75; best-effort delete via hunt_delete() if available.
    vql = f"SELECT hunt_delete(hunt_id='{hunt_id}') AS Deleted FROM scope()"
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def get_hunt_results(
    cfg: ServerConfig, hunt_id: str, client_id: Optional[str] = None, limit: int = 200
) -> Dict[str, Any]:
    predicate = ""
    if client_id:
        predicate = f" WHERE ClientId = '{client_id}'"
    vql = f"SELECT * FROM hunt_results(hunt_id='{hunt_id}'){predicate} LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"results": normalize_records(rows)}
