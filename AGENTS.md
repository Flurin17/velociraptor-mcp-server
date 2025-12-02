# Repository Guidelines

## Project Structure & Module Organization
- `mcp_server/`: FastMCP server implementation (config loading, gRPC client, VQL/tool adapters, resources, prompts).
- `main.py`: CLI entrypoint that wires the server and starts stdio transport.
- `tests/`: Pytest suite covering config, client wiring, and tool behavior.
- `velociraptor_lab/`: Podman/Docker lab for spinning up a local Velociraptor stack and generating `api.config.yaml`.
- `requirements.txt`: Shared Python dependencies for both the MCP server and the lab tooling.

## Build, Test, and Development Commands
- Create universal venv: `python3 -m venv .venv && . .venv/bin/activate`.
- Install deps: `pip install -r requirements.txt` (covers MCP + lab helpers).
- Run MCP server locally: `python3 main.py --config velociraptor_lab/volumes/api/api.config.yaml --log-level INFO`.
- Launch lab (from `velociraptor_lab/`): `podman machine start` then `podman compose -f podman-compose.yml up --build -d` (or the manual `podman run` commands in that README).
- Execute tests: `python3 -m pytest -q`.
- Smoke test API directly: `python test_api.py --config velociraptor_lab/volumes/api/api.config.yaml --query "SELECT * FROM clients()"`.

## Coding Style & Naming Conventions
- Python, PEP 8, 4-space indentation; favor type hints and small, composable functions.
- Tool names stay snake_case and map closely to the VQL they call (e.g., `list_clients`, `query_vql`).
- Keep configuration keys UPPER_SNAKE (e.g., `VELOCIRAPTOR_API_CONFIG`, `MCP_LOG_LEVEL`).
- Add concise docstrings/comments only where intent is non-obvious.

## Testing Guidelines
- Framework: `pytest`; place new tests in `tests/` mirroring module paths.
- Name tests with behavior focus (e.g., `test_query_vql_returns_rows`).
- When adding tools, include tests that mock VQL responses and validate argument validation/error paths.
- Run full suite before PRs: `python3 -m pytest -q`.

## Commit & Pull Request Guidelines
- Commits: short, imperative subject lines (e.g., “Add hunt creation tool”); group related changes and tests together.
- PRs: describe intent, main changes, and any lab steps needed to reproduce; link issues if applicable and include screenshots/log snippets for lab or MCP runs.

## Security & Configuration Tips
- The Velociraptor API requires mTLS; keep `api.config.yaml` and generated certs in `velociraptor_lab/volumes/api/` and never commit private keys.
- Use env overrides (`VELOCIRAPTOR_API_CONFIG`, `MCP_LOG_LEVEL`, `MCP_SERVER_NAME`) for local tweaks; avoid hard-coding hostnames/ports in code.
- The lab is the preferred way to validate new endpoints end-to-end before shipping changes to the MCP server.
