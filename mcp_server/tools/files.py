from __future__ import annotations

from typing import Any, Dict

from mcp_server.client import get_client
from mcp_server.config import ServerConfig
from mcp_server.utils import normalize_records


def list_directory(cfg: ServerConfig, client_id: str, path: str) -> Dict[str, Any]:
    """
    List directory contents from the VFS.
    """
    client = get_client(cfg)
    # Query the VFS directly - this returns cached VFS data
    vql = f"SELECT * FROM vfs_files(client_id='{client_id}', path='{path}')"
    rows = list(client.query(vql))
    return {"entries": normalize_records(rows)}


def get_file_info(cfg: ServerConfig, client_id: str, path: str) -> Dict[str, Any]:
    # Query the VFS for file info on the server side
    vql = f"SELECT * FROM vfs_files(client_id='{client_id}', path='{path}')"
    rows = get_client(cfg).query(vql)
    return {"info": normalize_records(rows)}


def download_file(
    cfg: ServerConfig, client_id: str, path: str, offset: int = 0, length: int = 0
) -> Dict[str, Any]:
    import base64

    # Use the gRPC VFSGetBuffer method directly
    client = get_client(cfg)
    data = client.download(client_id=client_id, path=path, offset=offset, length=length)
    encoded = base64.b64encode(data).decode("ascii")
    return {
        "path": path,
        "client_id": client_id,
        "offset": offset,
        "length": len(data),
        "data_base64": encoded,
    }
