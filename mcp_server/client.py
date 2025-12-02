from __future__ import annotations

import json
import threading
from functools import lru_cache
from typing import Any, Dict, Iterable, Optional

import grpc

from .config import ServerConfig


class VelociraptorUnavailable(RuntimeError):
    """Raised when the Velociraptor API cannot be reached or initialized."""


class VelociraptorClient:
    """Thin wrapper over Velociraptor gRPC API using pyvelociraptor protos."""

    def __init__(self, cfg: ServerConfig):
        self.cfg = cfg
        self._lock = threading.Lock()
        self._stub = None
        self._cfg = None

    def _ensure_stub(self):
        if self._stub:
            return
        try:
            from pyvelociraptor import api_pb2, api_pb2_grpc, LoadConfigFile  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise VelociraptorUnavailable(
                "pyvelociraptor is not installed or missing protos. Run `pip install -r requirements.txt`."
            ) from exc

        with self._lock:
            if self._stub:
                return
            try:
                cfg = LoadConfigFile(str(self.cfg.api_config_path))
                creds = grpc.ssl_channel_credentials(
                    root_certificates=cfg["ca_certificate"].encode("utf-8"),
                    private_key=cfg["client_private_key"].encode("utf-8"),
                    certificate_chain=cfg["client_cert"].encode("utf-8"),
                )
                options = (("grpc.ssl_target_name_override", "VelociraptorServer"),)
                channel = grpc.secure_channel(cfg["api_connection_string"], creds, options)
                self._stub = api_pb2_grpc.APIStub(channel)
                self._cfg = cfg
            except Exception as exc:  # pragma: no cover
                raise VelociraptorUnavailable(f"Failed to connect to Velociraptor: {exc}") from exc

        self._api_pb2 = api_pb2

    def query(self, vql: str, params: Optional[Dict[str, Any]] = None) -> Iterable[Dict[str, Any]]:
        """Execute VQL and yield rows. Parameters should be interpolated into the VQL by caller."""
        self._ensure_stub()
        assert self._stub is not None
        req = self._api_pb2.VQLCollectorArgs(
            org_id=self._cfg.get("org_id", "") if self._cfg else "",
            max_wait=1,
            max_row=1000,
            Query=[
                self._api_pb2.VQLRequest(
                    Name="MCP",
                    VQL=vql,
                )
            ],
        )
        for resp in self._stub.Query(req):
            if resp.Response:
                for row in json.loads(resp.Response):
                    yield row

    def download(self, client_id: str, path: str, offset: int = 0, length: int = 0) -> bytes:
        """Download VFS buffer."""
        self._ensure_stub()
        assert self._stub is not None
        req = self._api_pb2.VFSDownloadRequest(
            client_id=client_id,
            path=path,
            offset=offset,
            length=length,
        )
        chunks: list[bytes] = []
        for chunk in self._stub.VFSGetBuffer(req):
            chunks.append(chunk.data)
        return b"".join(chunks)


@lru_cache(maxsize=1)
def get_client(cfg: ServerConfig) -> VelociraptorClient:
    """Singleton Velociraptor client per process."""
    return VelociraptorClient(cfg)
