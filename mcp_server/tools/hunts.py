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
        safe_state = state.replace("'", "''")
        predicate = f" WHERE State = '{safe_state}'"
    vql = f"SELECT * FROM hunts(){predicate} ORDER BY Created DESC LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"hunts": normalize_records(rows)}


def get_hunt_details(cfg: ServerConfig, hunt_id: str) -> Dict[str, Any]:
    vql = f"SELECT * FROM hunts() WHERE HuntId = '{hunt_id}'"
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
    # Escape single quotes in all user-provided strings
    safe_description = description.replace("'", "''")
    safe_artifact = artifact.replace("'", "''")
    # For VQL in triple quotes, escape triple single quotes
    safe_query = query.replace("'''", "' ''").replace("'", "''")
    vql = (
        "SELECT hunt(description='{description}', artifacts=['{artifact}'], "
        "start_immediately={start_immediately}, "
        "artifact_doc={{Name:'{artifact}',Description:'{description}',Sources:[{{Queries:[{{VQL:'''{query}'''}}]}}]}}) "
        "AS Hunt FROM scope()"
    ).format(
        description=safe_description,
        artifact=safe_artifact,
        query=safe_query,
        start_immediately=str(start_immediately).lower(),
    )
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def stop_hunt(cfg: ServerConfig, hunt_id: str) -> Dict[str, Any]:
    # There is no stop_hunt plugin in v0.75; best-effort delete via hunt_delete() if available.
    safe_hunt_id = hunt_id.replace("'", "''")
    vql = f"SELECT hunt_delete(hunt_id='{safe_hunt_id}') AS Deleted FROM scope()"
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def get_hunt_results(
    cfg: ServerConfig, hunt_id: str, client_id: Optional[str] = None, limit: int = 200
) -> Dict[str, Any]:
    safe_hunt_id = hunt_id.replace("'", "''")
    predicate = ""
    if client_id:
        safe_client_id = client_id.replace("'", "''")
        predicate = f" WHERE ClientId = '{safe_client_id}'"
    vql = (
        f"SELECT * FROM hunt_results(hunt_id='{safe_hunt_id}'){predicate} LIMIT {limit}"
    )
    rows = get_client(cfg).query(vql)
    return {"results": normalize_records(rows)}
