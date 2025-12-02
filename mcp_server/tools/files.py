from __future__ import annotations

from typing import Any, Dict

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_directory(cfg: ServerConfig, client_id: str, path: str) -> Dict[str, Any]:
    # vfs accessor pulls ClientId from scope/env; use query() helper to inject it.
    vql = (
        "SELECT * FROM query(query=\"SELECT * FROM vfs_ls(path='{path}')\", "
        "env=dict(ClientId='{client_id}'))"
    ).format(path=path, client_id=client_id)
    rows = get_client(cfg).query(vql)
    return {"entries": normalize_records(rows)}


def get_file_info(cfg: ServerConfig, client_id: str, path: str) -> Dict[str, Any]:
    vql = (
        "SELECT * FROM query(query=\"SELECT * FROM stat(path='{path}', accessor='vfs')\", "
        "env=dict(ClientId='{client_id}'))"
    ).format(path=path, client_id=client_id)
    rows = get_client(cfg).query(vql)
    return {"info": normalize_records(rows)}


def download_file(
    cfg: ServerConfig, client_id: str, path: str, offset: int = 0, length: int = 0
) -> Dict[str, Any]:
    import base64

    # read_file accessor 'vfs' uses ClientId from env; returns rows with Data field.
    vql = (
        'SELECT Data, Offset FROM query(query="SELECT Data, Offset FROM read_file('
        "accessor='vfs', filenames=['{path}'], offset={offset}, length={length})\", "
        "env=dict(ClientId='{client_id}'))"
    ).format(path=path, offset=offset, length=length, client_id=client_id)
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
