from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_artifacts(cfg: ServerConfig, search: Optional[str] = None, limit: int = 200) -> Dict[str, Any]:
    predicate = ""
    if search:
        predicate = f" WHERE Name =~ '{search}' OR Description =~ '{search}'"
    # artifact_definitions() returns both compiled-in and custom artifacts.
    vql = f"SELECT Name, Description, Type FROM artifact_definitions(){predicate} LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"artifacts": normalize_records(rows)}


def collect_artifact(
    cfg: ServerConfig,
    client_id: str,
    artifact: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    parameters = params or {}
    vql = f"SELECT collect_client(client_id='{client_id}', artifacts=['{artifact}'], parameters={parameters}) AS FlowId"
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def upload_artifact(cfg: ServerConfig, name: str, vql: str, description: str = "", type_: str = "CLIENT") -> Dict[str, Any]:
    artifact_doc = f"{{Name:'{name}',Description:'{description}',Type:'{type_}',Sources:[{{Queries:[{{VQL:'''{vql}'''}}]}}]}}"
    vql_stmt = f"SELECT upload_artifact(artifact={artifact_doc}) AS Uploaded"
    rows = get_client(cfg).query(vql_stmt)
    return {"result": normalize_records(rows)}


def get_artifact_definition(cfg: ServerConfig, name: str) -> Dict[str, Any]:
    vql = f"SELECT * FROM artifact_definition(name='{name}')"
    rows = get_client(cfg).query(vql)
    return {"artifact": normalize_records(rows)}
