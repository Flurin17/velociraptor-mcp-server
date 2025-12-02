from __future__ import annotations

from typing import Any, Dict, Optional

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_artifacts(
    cfg: ServerConfig, search: Optional[str] = None, limit: int = 200
) -> Dict[str, Any]:
    predicate = ""
    if search:
        safe_search = search.replace("'", "''")
        predicate = f" WHERE name =~ '{safe_search}' OR description =~ '{safe_search}'"
    # artifact_definitions() returns both compiled-in and custom artifacts; field names are lowercase.
    vql = f"SELECT name, description, type FROM artifact_definitions(){predicate} LIMIT {limit}"
    rows = get_client(cfg).query(vql)
    return {"artifacts": normalize_records(rows)}


def collect_artifact(
    cfg: ServerConfig,
    client_id: str,
    artifact: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Build VQL dict syntax for parameters: dict(key1='val1', key2='val2')
    param_clause = ""
    if params:
        param_items = ", ".join(
            f"{k}='{str(v).replace(chr(39), chr(39)+chr(39))}'"
            for k, v in params.items()
        )
        param_clause = f", parameters=dict({param_items})"
    # Escape single quotes in inputs
    safe_client_id = client_id.replace("'", "''")
    safe_artifact = artifact.replace("'", "''")
    # collect_client must be executed with FROM scope()
    vql = (
        "SELECT collect_client(client_id='{client_id}', artifacts=['{artifact}']{param_clause}) "
        "AS FlowId FROM scope()"
    ).format(
        client_id=safe_client_id, artifact=safe_artifact, param_clause=param_clause
    )
    rows = get_client(cfg).query(vql)
    return {"result": normalize_records(rows)}


def upload_artifact(
    cfg: ServerConfig, name: str, vql: str, description: str = "", type_: str = "CLIENT"
) -> Dict[str, Any]:
    # Escape single quotes in strings (double them for VQL)
    safe_name = name.replace("'", "''")
    safe_desc = description.replace("'", "''")
    # For VQL in triple quotes, escape triple single quotes
    safe_vql = vql.replace("'''", "' ''")
    artifact_doc = f"{{Name:'{safe_name}',Description:'{safe_desc}',Type:'{type_}',Sources:[{{Queries:[{{VQL:'''{safe_vql}'''}}]}}]}}"
    # upload_artifact() is not available in recent versions; artifact_set replaces it.
    vql_stmt = f"SELECT artifact_set(artifact={artifact_doc}) AS Uploaded FROM scope()"
    rows = get_client(cfg).query(vql_stmt)
    return {"result": normalize_records(rows)}


def get_artifact_definition(cfg: ServerConfig, name: str) -> Dict[str, Any]:
    safe_name = name.replace("'", "''")
    vql = f"SELECT * FROM artifact_definitions(name='{safe_name}')"
    rows = get_client(cfg).query(vql)
    return {"artifact": normalize_records(rows)}
