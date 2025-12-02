from __future__ import annotations

import logging
from typing import Any

from mcp_server import tools
from mcp_server.config import ServerConfig
from mcp_server.resources import ARTIFACT_CATALOG, VQL_TEMPLATES
from mcp_server.prompts import INCIDENT_RESPONSE_PROMPTS


def build_server(cfg: ServerConfig):
    """
    Create and configure a FastMCP server with all Velociraptor tools/resources/prompts.
    """
    try:
        from mcp.server.fastmcp import FastMCP  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "fastmcp is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    logging.basicConfig(level=getattr(logging, cfg.log_level, logging.INFO))

    mcp = FastMCP(
        name=cfg.server_name,
        instructions="Velociraptor MCP server exposing VQL, hunts, artifacts, VFS, and monitoring tools.",
        log_level=cfg.log_level,
    )

    #
    # Tool registrations (thin wrappers to inject cfg)
    #
    @mcp.tool()
    def query_vql(vql: str):
        """Execute an arbitrary VQL query and return rows."""
        return tools.query_vql(cfg, vql=vql)

    @mcp.tool()
    def list_clients(limit: int = 200, offset: int = 0):
        """List enrolled Velociraptor clients."""
        return tools.list_clients(cfg, limit=limit, offset=offset)

    @mcp.tool()
    def get_client_info(client_id: str):
        """Get detailed information for a client."""
        return tools.get_client_info(cfg, client_id=client_id)

    @mcp.tool()
    def search_clients(
        hostname: str | None = None,
        label: str | None = None,
        query: str | None = None,
        limit: int = 200,
    ):
        """Search clients by hostname, label, or VQL filter."""
        return tools.search_clients(
            cfg, hostname=hostname, label=label, query=query, limit=limit
        )

    @mcp.tool()
    def list_hunts(state: str | None = None, limit: int = 100):
        """List hunts with optional state filter."""
        return tools.list_hunts(cfg, state=state, limit=limit)

    @mcp.tool()
    def get_hunt_details(hunt_id: str):
        """Get detailed info for a hunt."""
        return tools.get_hunt_details(cfg, hunt_id=hunt_id)

    @mcp.tool()
    def create_hunt(
        artifact: str, query: str, description: str = "", start_immediately: bool = True
    ):
        """Create and optionally start a hunt from a VQL query."""
        return tools.create_hunt(
            cfg,
            artifact=artifact,
            query=query,
            description=description,
            start_immediately=start_immediately,
        )

    @mcp.tool()
    def stop_hunt(hunt_id: str):
        """Stop a running hunt."""
        return tools.stop_hunt(cfg, hunt_id=hunt_id)

    @mcp.tool()
    def get_hunt_results(hunt_id: str, client_id: str | None = None, limit: int = 200):
        """Retrieve hunt results, optionally scoped to a client."""
        return tools.get_hunt_results(
            cfg, hunt_id=hunt_id, client_id=client_id, limit=limit
        )

    @mcp.tool()
    def list_artifacts(search: str | None = None, limit: int = 200):
        """List artifacts available on the server."""
        return tools.list_artifacts(cfg, search=search, limit=limit)

    @mcp.tool()
    def collect_artifact(
        client_id: str, artifact: str, params: dict[str, Any] | None = None
    ):
        """Collect an artifact from a client."""
        return tools.collect_artifact(
            cfg, client_id=client_id, artifact=artifact, params=params
        )

    @mcp.tool()
    def upload_artifact(
        name: str, vql: str, description: str = "", type_: str = "CLIENT"
    ):
        """Upload a custom artifact definition."""
        return tools.upload_artifact(
            cfg, name=name, vql=vql, description=description, type_=type_
        )

    @mcp.tool()
    def get_artifact_definition(name: str):
        """Fetch a stored artifact definition."""
        return tools.get_artifact_definition(cfg, name=name)

    @mcp.tool()
    def list_directory(client_id: str, path: str):
        """List a directory from the Velociraptor VFS."""
        return tools.list_directory(cfg, client_id=client_id, path=path)

    @mcp.tool()
    def get_file_info(client_id: str, path: str):
        """Get file metadata from the VFS."""
        return tools.get_file_info(cfg, client_id=client_id, path=path)

    @mcp.tool()
    def download_file(client_id: str, path: str, offset: int = 0, length: int = 0):
        """Download a file (base64) from the VFS."""
        return tools.download_file(
            cfg, client_id=client_id, path=path, offset=offset, length=length
        )

    @mcp.tool()
    def get_server_stats():
        """Retrieve Velociraptor server stats."""
        return tools.get_server_stats(cfg)

    @mcp.tool()
    def get_client_activity(limit: int = 200):
        """Recent client activity."""
        return tools.get_client_activity(cfg, limit=limit)

    @mcp.tool()
    def list_alerts(limit: int = 200):
        """List recent alerts."""
        return tools.list_alerts(cfg, limit=limit)

    @mcp.tool()
    def create_alert(
        title: str, message: str, client_id: str | None = None, severity: str = "INFO"
    ):
        """Create a custom alert."""
        return tools.create_alert(
            cfg, title=title, message=message, client_id=client_id, severity=severity
        )

    #
    # Resources
    #
    @mcp.resource("resource://artifact-catalog")
    def artifact_catalog() -> list[dict[str, str]]:
        """Static catalog of common artifacts."""
        return ARTIFACT_CATALOG

    @mcp.resource("vql-template://{name}")
    def vql_template(name: str) -> str:
        """Return a named VQL template."""
        if name not in VQL_TEMPLATES:
            raise KeyError(f"Unknown template: {name}")
        return VQL_TEMPLATES[name]

    #
    # Prompts
    #
    @mcp.prompt()
    def incident_response_prompt(name: str) -> str:
        """Incident response prompt snippets by name."""
        if name not in INCIDENT_RESPONSE_PROMPTS:
            raise KeyError(f"Unknown prompt: {name}")
        return INCIDENT_RESPONSE_PROMPTS[name]

    return mcp
