# Velociraptor MCP Server

## Quickstart (3 commands)
```sh
python3 -m venv .venv
. .venv/bin/activate
pip install .
velociraptor-mcp --config /absolute/path/to/velociraptor_lab/volumes/api/api.config.yaml
```
You need a Velociraptor mTLS API config (`api.config.yaml`). The included `velociraptor_lab` can generate one (see “Using the lab”).

A FastMCP-based server that exposes Velociraptor capabilities (VQL queries, hunts, artifacts, VFS/file ops, monitoring, alerts) over the MCP protocol for use with Codex/ChatGPT-style agents.

## Prerequisites
- Python 3.10+
- Podman (or Docker) if you want to use the included `velociraptor_lab` for local testing.
- Generated Velociraptor mTLS API config (`api.config.yaml`) – the lab can generate this for you.

## Installation
Create a virtualenv (avoids macOS/Homebrew PEP 668 errors) and install the package:
```sh
python3 -m venv .venv
. .venv/bin/activate
pip install .            # runtime install
# or, for tests and tooling
pip install -e .[dev]
```
The legacy workflow still works if you prefer the raw requirements:
```sh
pip install -r requirements.txt
```

## Running the MCP server
After installing, you can either call the module directly or use the installed console script:
```sh
# installed entry point
velociraptor-mcp --config velociraptor_lab/volumes/api/api.config.yaml \
  --log-level INFO --server-name velociraptor-mcp

# or, from source
python3 main.py --config velociraptor_lab/volumes/api/api.config.yaml \
  --log-level INFO --server-name velociraptor-mcp
```
Options:
- `--config` or env `VELOCIRAPTOR_API_CONFIG`: path to `api.config.yaml` (default `volumes/api/api.config.yaml`)
- `--log-level` or env `MCP_LOG_LEVEL` (default `INFO`)
- `--server-name` or env `MCP_SERVER_NAME`

## Available tools (summary)
- VQL: `query_vql`
- Clients: `list_clients`, `get_client_info`, `search_clients`
- Hunts: `list_hunts`, `get_hunt_details`, `create_hunt`, `stop_hunt`, `get_hunt_results`
- Artifacts: `list_artifacts`, `collect_artifact`, `upload_artifact`, `get_artifact_definition`
- Files/VFS: `list_directory`, `get_file_info`, `download_file`
- Monitoring/Alerts: `get_server_stats`, `get_client_activity`, `list_alerts`, `create_alert`
- Resources/Prompts: artifact catalog, VQL templates, incident-response prompts

## Using the lab (recommended for development)
`velociraptor_lab/` contains a Podman/Docker stack that spins up:
- Velociraptor server (GUI + gRPC)
- Test client that should auto-enroll
- Generated mTLS configs under `velociraptor_lab/volumes/{server,client,api,datastore}`

Quick start (Podman):
```sh
cd velociraptor_lab
podman machine start                     # macOS/AppleHV
podman compose -f podman-compose.yml up --build -d
# or use the manual podman run commands in velociraptor_lab/README.md
```
Verify API:
```sh
. ../.venv/bin/activate
python test_api.py --config volumes/api/api.config.yaml
```
Then run the MCP server (see above) pointing at the generated `api.config.yaml`.

Troubleshooting lab enrollment:
- The client must reach `https://VelociraptorServer:8000/` inside the podman network. Keep hostname/alias consistent with the cert CN.
- If `clients()` is empty, delete `velociraptor_lab/volumes/*` and redeploy the lab.
- For manual probing, `python test_api.py --query "SELECT * FROM clients()"`.

## Development
- Create a fresh venv and install dev extras: `python3 -m venv .venv && . .venv/bin/activate && pip install -e .[dev]`.
- Run unit tests locally: `. .venv/bin/activate && pytest`.
- Validate API wiring against the lab: `python test_api.py --config velociraptor_lab/volumes/api/api.config.yaml --query "SELECT * FROM clients()"` (after bringing up the lab).
- Linting is minimal today; focus on tests and keeping tool names/config keys aligned with VQL and env vars.

## Tests
```sh
. .venv/bin/activate
pytest
```
Note: lab API test is skipped automatically if `pyvelociraptor` or configs are missing.

## Codex MCP setup
You can register this server with the Codex CLI (stdio transport).

**Fast path (CLI):**
```sh
codex mcp add velociraptor \
  --env VELOCIRAPTOR_API_CONFIG=/absolute/path/to/velociraptor_lab/volumes/api/api.config.yaml \
  -- python3 main.py --config /absolute/path/to/velociraptor_lab/volumes/api/api.config.yaml \
  --log-level INFO --server-name velociraptor-mcp
```
- Run the command from the repo root or use absolute paths so Codex can find `main.py`.
- Restart Codex; inside the TUI `/mcp` shows active servers.

**Config file (manual):** add to `~/.codex/config.toml` if you prefer editing directly:
```toml
[mcp_servers.velociraptor]
command = "python3"
args = ["main.py", "--config", "/absolute/path/to/velociraptor_lab/volumes/api/api.config.yaml", "--log-level", "INFO", "--server-name", "velociraptor-mcp"]
env = { VELOCIRAPTOR_API_CONFIG = "/absolute/path/to/velociraptor_lab/volumes/api/api.config.yaml" }
cwd = "/absolute/path/to/velociraptor-mcp-server"
startup_timeout_sec = 15   # optional; defaults to 10
tool_timeout_sec = 120     # optional; defaults to 60
```
Either approach keeps your `api.config.yaml` path in one place via `VELOCIRAPTOR_API_CONFIG`. Codex shares the same MCP config between the CLI and IDE.

## Troubleshooting
- `ModuleNotFoundError` or `grpc` missing → ensure you’re in the venv and ran `pip install .`.
- `Velociraptor API config not found` → point `--config` / `VELOCIRAPTOR_API_CONFIG` to the generated `api.config.yaml`.
- Handshake fails in Codex → check `~/.codex/log/codex-tui.log`; most common is the missing config path.
- PEP 668 “externally managed” error → always use a venv (as above).

## Structure
```
mcp_server/       # server, tools, resources, prompts
main.py           # entrypoint
tests/            # unit tests + fixtures
requirements.txt  # shared deps (MCP + lab)
velociraptor_lab/ # podman/docker lab for local Velociraptor API
```

## Publishing to PyPI (manual)
```sh
. .venv/bin/activate
pip install -U pip build twine
python -m build
twine upload dist/*   # requires PYPI_USERNAME and PYPI_PASSWORD or token in ~/.pypirc
```
Tagging a release is recommended (see CI section).

## Releasing via GitHub Actions
If your CI publishes on tagged pushes, use these steps:
```sh
git add pyproject.toml mcp_server/__init__.py README_MCP.md
git commit -m "Release 0.1.2"        # or skip if already committed
git tag -a v0.1.2 -m "v0.1.2"        # bump tag version as needed
git push origin main                  # adjust branch name if different
git push origin v0.1.2                # triggers the release workflow
```

## License
This project is licensed under the MIT License. See `LICENSE` for the full text.
