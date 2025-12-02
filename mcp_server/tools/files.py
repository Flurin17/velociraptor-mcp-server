from __future__ import annotations

import time
from typing import Any, Dict

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_directory(cfg: ServerConfig, client_id: str, path: str) -> Dict[str, Any]:
    """
    Populate and return a VFS directory listing by launching the
    System.VFS.ListDirectory artifact on the client, then polling the
    resulting flow for rows.
    """
    client = get_client(cfg)
    safe_client_id = client_id.replace("'", "''")
    safe_path = path.replace("'", "''")
    # Kick off the collection.
    start_vql = (
        "SELECT collect_client("
        "client_id='{client_id}', artifacts=['System.VFS.ListDirectory'], "
        "parameters={{Path:'{path}', Accessor:'auto', Depth:0}})"
        " AS Flow FROM scope()"
    ).format(client_id=safe_client_id, path=safe_path)
    flow_rows = list(client.query(start_vql))
    flow_id = None
    if flow_rows and flow_rows[0].get("Flow"):
        flow = flow_rows[0]["Flow"]
        flow_id = (
            flow.get("flow_id")
            or flow.get("FlowId")
            or flow.get("flow_id".upper(), None)
        )

    entries: list[dict[str, Any]] = []
    if flow_id:
        # Poll for up to ~15 seconds for results to arrive.
        poll_vql = f"SELECT * FROM flow_results(client_id='{safe_client_id}', flow_id='{flow_id}')"
        for _ in range(15):
            rows = list(client.query(poll_vql))
            if rows:
                entries = normalize_records(rows)
                break
            time.sleep(1)

    return {"entries": entries, "flow_id": flow_id}


def get_file_info(cfg: ServerConfig, client_id: str, path: str) -> Dict[str, Any]:
    safe_client_id = client_id.replace("'", "''")
    safe_path = path.replace("'", "''")
    vql = (
        "SELECT * FROM query(query=\"SELECT * FROM stat(path='{path}', accessor='vfs')\", "
        "env=dict(ClientId='{client_id}'))"
    ).format(path=safe_path, client_id=safe_client_id)
    rows = get_client(cfg).query(vql)
    return {"info": normalize_records(rows)}


def download_file(
    cfg: ServerConfig, client_id: str, path: str, offset: int = 0, length: int = 0
) -> Dict[str, Any]:
    import base64

    safe_client_id = client_id.replace("'", "''")
    safe_path = path.replace("'", "''")
    # read_file accessor 'vfs' uses ClientId from env; returns rows with Data field.
    vql = (
        'SELECT Data, Offset FROM query(query="SELECT Data, Offset FROM read_file('
        "accessor='vfs', filenames=['{path}'], offset={offset}, length={length})\", "
        "env=dict(ClientId='{client_id}'))"
    ).format(path=safe_path, offset=offset, length=length, client_id=safe_client_id)
    rows = list(get_client(cfg).query(vql))
    if not rows:
        return {
            "path": path,
            "client_id": client_id,
            "offset": offset,
            "length": 0,
            "data_base64": "",
        }
    data_field = rows[0].get("Data", b"")
    if isinstance(data_field, str):
        # Velociraptor returns base64-encoded bytes as str already.
        encoded = data_field
        data_len = len(base64.b64decode(encoded))
    else:
        encoded = base64.b64encode(data_field).decode("ascii")
        data_len = len(data_field)
    return {
        "path": path,
        "client_id": client_id,
        "offset": offset,
        "length": length or data_len,
        "data_base64": encoded,
    }
