# Velociraptor MCP Server Implementation Plan

## Overview

Build a FastMCP-based MCP server that exposes comprehensive Velociraptor capabilities including VQL queries, client management, hunt operations, artifact collection, file operations, and monitoring. The server will run as a standalone Python service that connects to the existing Velociraptor API using the generated `api.config.yaml` with mTLS authentication. The Velociraptor gRPC API surface is intentionally small—everything is driven by two RPCs: `Query` (execute arbitrary VQL) and `VFSGetBuffer` (stream file/blob data). All higher-level actions (hunts, artifacts, client ops, admin tasks, event monitoring) must be expressed as VQL or downloads over these two calls.

## Architecture

- **Standalone Python service** using FastMCP framework
- **Connects to existing Velociraptor API** via `pyvelociraptor` using mTLS from `volumes/api/api.config.yaml`
- **Compatible with Codex CLI** via standard MCP protocol
- **Modular tool design** following single-responsibility principle
- **Validated in `velociraptor_lab`**: spin up the included Podman/Docker lab to generate `api.config.yaml`, then run MCP integration tests against the live lab stack before release.

## Files to Create

### 1. `mcp_server/__init__.py`

- Package initialization

### 2. `mcp_server/server.py`

- Main FastMCP server instance
- Initialize Velociraptor client connection using `api.config.yaml`
- Register all tools, resources, and prompts
- Configure error handling and logging

### 3. `mcp_server/tools/__init__.py`

- Tools package initialization

### 4. `mcp_server/tools/vql.py`

- `query_vql`: Execute arbitrary VQL queries with parameter validation
- Input: VQL query string, optional parameters
- Output: Query results as structured data
- Error handling for invalid queries and connection failures

### 5. `mcp_server/tools/clients.py`

- `list_clients`: List all enrolled clients with filtering options
- `get_client_info`: Get detailed information about a specific client
- `search_clients`: Search clients by hostname, labels, or other attributes
- Input validation for client IDs and search parameters

### 6. `mcp_server/tools/hunts.py`

- `list_hunts`: List all hunts with status filtering
- `get_hunt_details`: Get detailed hunt information including results
- `create_hunt`: Create a new hunt with artifact and target specification
- `stop_hunt`: Stop a running hunt
- `get_hunt_results`: Retrieve hunt results for specific clients

### 7. `mcp_server/tools/artifacts.py`

- `list_artifacts`: List available artifacts
- `collect_artifact`: Collect an artifact from one or more clients
- `upload_artifact`: Upload a custom artifact definition
- `get_artifact_definition`: Retrieve artifact definition details

### 8. `mcp_server/tools/files.py`

- `download_file`: Download files from clients (VFS paths)
- `list_directory`: List directory contents from client VFS
- `get_file_info`: Get file metadata and hash information
- Support for Velociraptor VFS paths

### 9. `mcp_server/tools/monitoring.py`

- `get_server_stats`: Retrieve server statistics and health
- `get_client_activity`: Get recent client activity and check-ins
- `list_alerts`: List and filter security alerts
- `create_alert`: Create custom alerts based on conditions

### 10. `mcp_server/resources/__init__.py`

- Resources package initialization

### 11. `mcp_server/resources/vql_templates.py`

- Static resource: Common VQL query templates
- Examples: client enumeration, process listing, file system queries, network connections

### 12. `mcp_server/resources/artifact_catalog.py`

- Static resource: Catalog of common Velociraptor artifacts
- Descriptions, use cases, and example queries

### 13. `mcp_server/prompts/__init__.py`

- Prompts package initialization

### 14. `mcp_server/prompts/incident_response.py`

- Prompt templates for common incident response scenarios
- Examples: "Investigate suspicious process", "Analyze network connections", "Collect forensic artifacts"

### 15. `mcp_server/config.py`

- Configuration management
- Load API config path from environment or default location
- Validate configuration file existence
- Handle configuration errors gracefully

### 16. `mcp_server/client.py`

- Velociraptor API client wrapper
- Singleton pattern for connection reuse
- Connection pooling and retry logic
- Error translation (Velociraptor errors → MCP-friendly errors)

### 17. `mcp_server/utils.py`

- Utility functions for data transformation
- VQL result formatting
- Client data normalization
- Error message formatting

### 18. `main.py`

- Entry point for the MCP server
- Parse command-line arguments (config path, log level)
- Initialize and run FastMCP server
- Handle graceful shutdown

### 19. `requirements.txt` (update)

- Single universal set for both MCP server and `velociraptor_lab` host scripts (shared `.venv`):
  - `fastmcp`
  - `pyvelociraptor`
  - `pydantic`
  - `python-dotenv`
  - `grpcio`, `grpcio-tools` (proto regeneration if needed)
  - `pytest` (unit/integration tests across MCP + lab)

### 20. `mcp_server/config.example.yaml` or `.env.example` (update)

- Add MCP server configuration options
- API config path
- Logging configuration
- Optional: server name, description

### 21. `README.md`

- Documentation for the MCP server
- Installation instructions
- Configuration guide
- Codex CLI integration instructions
- Example tool usage
- Troubleshooting

### 22. `test_mcp_server.py`

- Unit tests for tools
- Integration tests with mock Velociraptor API
- Test error handling and edge cases

## Implementation Details

### FastMCP Server Setup

- Use `fastmcp.Server` as base class
- Configure server metadata (name, version, description)
- Enable structured logging
- Implement proper error handling middleware

### Tool Design Principles

- **Single responsibility**: Each tool performs one specific operation
- **Input validation**: Use Pydantic models for all tool inputs
- **Error handling**: Graceful error messages, no stack traces exposed
- **Idempotency**: Where applicable, make operations idempotent
- **Security**: Validate all inputs, sanitize outputs, log security-relevant operations

### Velociraptor Client Integration

- Initialize `VQLClient` from `api.config.yaml` on server startup
- Implement connection retry logic
- Handle mTLS certificate expiration
- Cache connection for performance
- Provide helper methods to wrap common VQL patterns (hunts, artifacts, VFS reads, monitoring) so tools stay thin.

### API Surface Mapping

Because the gRPC API only exposes `Query` and `VFSGetBuffer`, every tool must translate to VQL primitives:
- **Clients**: `SELECT * FROM clients()`, `client_info(client_id=...)`
- **Hunts/flows**: `create_hunt()`, `list_hunts()`, `hunt_details()`, `hunt_results()`, `flows(client_id=...)`, `source(client_id, flow_id, artifact=...)`
- **Artifacts**: `artifacts()`, `collect_client()`, `collect_hunt()`, `upload_artifact()`, `artifact_definition(name=...)`
- **VFS/files**: `stat_vfs(client_id, path)`, `vfs_listdir(...)`, `download_table(...)` + `VFSGetBuffer` for file/blob downloads
- **Monitoring/events**: `watch_monitoring(artifact=...)`, `list_alerts()`, `create_alert()` (via VQL), event feeds
- **Admin**: `gui_users()`, ACL grant/show, org/user maintenance via VQL helpers
Document the VQL invoked by each MCP tool alongside its input model for traceability.

### Codex CLI Compatibility

- Follow standard MCP protocol specifications
- Ensure proper JSON-RPC message formatting
- Support standard MCP capabilities (tools, resources, prompts)
- Test with Codex CLI configuration in `~/.codex/config.toml`

### Security Considerations

- Never expose mTLS certificates in tool outputs
- Validate all VQL queries for dangerous operations
- Implement rate limiting for expensive operations
- Log all tool invocations for audit trail
- Sanitize client data in responses

### Performance Optimization

- Cache artifact definitions and common queries
- Implement connection pooling for API calls
- Use async operations where FastMCP supports it
- Batch operations when possible

### Tooling Best Practices (Anthropic guide)

- Selectively wrap high-impact workflows; avoid 1:1 endpoint mirroring and consolidate related actions into purposeful tools.
- Keep namespaces and names consistent and disambiguated (e.g., `hunts_list`, `hunts_create`, `files_download`) to help agents pick the right tool.
- Return high-signal, human-readable context with optional “concise” vs “detailed” modes; avoid dumping verbose IDs/metadata by default.
- Design for token efficiency: filtering, pagination, truncation with clear “truncated” markers so agents can re-query precisely.
- Write precise tool specs/descriptions with explicit parameter semantics, examples, and constraints; small description tweaks materially reduce tool-call errors.
- Prototype → evaluate → iterate using live transcripts from `velociraptor_lab` runs; let agents surface ambiguity and refine the tools.

## Testing Strategy

1. **Unit tests**: Test individual tools with mocked Velociraptor client
2. **Integration tests**: Test with actual Velociraptor API (requires running containers)
3. **Codex CLI tests**: Verify MCP protocol compliance
4. **Error scenario tests**: Test connection failures, invalid inputs, permission errors

## Codex CLI Integration

Add to `~/.codex/config.toml`:

```toml
[[mcp_servers]]
name = "velociraptor"
command = "python"
args = ["/path/to/main.py", "--config", "/path/to/volumes/api/api.config.yaml"]
```

## Dependencies

- `fastmcp`: FastMCP framework for MCP server implementation
- `pyvelociraptor`: Velociraptor Python API client
- `pydantic`: Data validation (may be included in fastmcp)
- `python-dotenv`: Environment variable management
- `grpcio`, `grpcio-tools`: proto/build utilities
- `pytest`: shared test runner for MCP + lab validation

## File Structure

```
velociraptor-mcp-server/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py
│   ├── client.py
│   ├── config.py
│   ├── utils.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── vql.py
│   │   ├── clients.py
│   │   ├── hunts.py
│   │   ├── artifacts.py
│   │   ├── files.py
│   │   └── monitoring.py
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── vql_templates.py
│   │   └── artifact_catalog.py
│   └── prompts/
│       ├── __init__.py
│       └── incident_response.py
├── main.py
├── tests/
│   ├── test_mcp_server.py
│   └── fixtures/           # sample VQL responses, api.config.yaml stub
├── requirements.txt        # universal venv for MCP + lab scripts
├── README.md
├── velociraptor_lab/       # Podman/Docker lab (existing)
└── .venv/ (gitignored)     # shared virtualenv
```

## Lab Integration Plan (`velociraptor_lab`)
- Use the included Podman/Docker stack to spin up a Velociraptor server + client, generating `volumes/api/api.config.yaml` for mTLS access.
- Reuse the shared `.venv` (`pip install -r requirements.txt`) to run `velociraptor_lab/test_api.py` and MCP integration tests against the live lab.
- Validation loop: `podman compose up -d` → run `test_api.py` (baseline API check) → run MCP integration tests hitting the lab server → iterate on tool/VQL fixes → `podman compose down`.
