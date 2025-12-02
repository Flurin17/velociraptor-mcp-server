# Velociraptor Podman Setup

This repo spins up a Velociraptor server plus a test client using Podman Compose and prepares an API client configuration for host-side testing.

## Prerequisites
- Podman with `podman-compose` (or `docker-compose` if you prefer Docker).
- Python 3.10+ on the host to run `test_api.py`.

## Quick start (Podman)
0. Ensure Podman machine is running (macOS/AppleHV):
   ```sh
   podman machine start
   podman system connection list   # should show podman-machine-default
   ```
1. Copy env template (only needed if you want to override defaults):
   ```sh
   cp .env.example .env
   ```
2. Start the stack. If `podman compose` is unavailable, install `podman-compose` or use the manual run steps below.
   ```sh
   podman compose -f podman-compose.yml up --build -d
   ```
   Generated on first start (gitignored):
   - `volumes/server/server.config.yaml`
   - `volumes/client/client.config.yaml`
   - `volumes/api/api.config.yaml` (mTLS creds for API user)
3. GUI: `http://localhost:${GUI_PORT:-8889}` (login with `ADMIN_USER` / `ADMIN_PASSWORD` from `.env`).
4. Host-side API check:
   ```sh
   python -m venv .venv
   . .venv/bin/activate
   pip install -r requirements.txt   # shared with MCP server
   python test_api.py --config volumes/api/api.config.yaml
   ```
   Expected: rows from `SELECT * FROM clients()` once the lab client enrolls.

### If `podman compose` is missing
Use Podman CLI directly (uses the already-built images/tags from this repo):
```sh
CONTAINER_HOST=unix://$(podman info --format '{{.Host.RemoteSocket.Path}}') \
podman network create velociraptor-net

CONTAINER_HOST=unix://$(podman info --format '{{.Host.RemoteSocket.Path}}') \
podman run -d --name velociraptor-server --hostname VelociraptorServer \
  --network velociraptor-net --network-alias VelociraptorServer \
  -p 8889:8889 -p 8001:8001 \
  -e ADMIN_USER=admin -e ADMIN_PASSWORD=admin -e API_USER=api-admin \
  -e GUI_PORT=8889 -e API_PORT=8001 -e SERVER_HOSTNAME=VelociraptorServer \
  -v $(pwd)/volumes/server:/config \
  -v $(pwd)/volumes/datastore:/var/lib/velociraptor \
  -v $(pwd)/volumes/client:/client \
  -v $(pwd)/volumes/api:/api \
  localhost/velociraptor-mcp-server_velociraptor-server:latest

CONTAINER_HOST=unix://$(podman info --format '{{.Host.RemoteSocket.Path}}') \
podman run -d --name velociraptor-client --network velociraptor-net \
  -e SERVER_HOSTNAME=VelociraptorServer -e API_PORT=8000 \
  -v $(pwd)/volumes/client:/client:ro \
  localhost/velociraptor-mcp-server_velociraptor-client:latest
```
Notes:
- The Velociraptor client talks to the frontend port (default 8000) inside the server; keep `API_PORT` for gRPC at 8001.
- If you rebuild images, Podman uses tags `localhost/velociraptor-mcp-server_velociraptor-server:latest` and `localhost/velociraptor-mcp-server_velociraptor-client:latest`.

### Troubleshooting
- If the client never enrolls and `clients()` is empty, ensure it can reach `https://VelociraptorServer:8000/` from inside the client container. The cert CN is `VelociraptorServer`; keep hostname/network alias consistent.
- Regenerate configs by deleting `volumes/{server,client,api,datastore}` and re-running the stack.
- Add debug tools inside containers (optional): modify Dockerfiles to install `iproute2`/`net-tools` to check ports.

## Services
- **velociraptor-server**: Generates configs on first boot, exposes GUI (`GUI_PORT`) and gRPC API (`API_PORT`).
- **velociraptor-client**: Lightweight Alpine container running the Velociraptor client using the generated `client.config.yaml`.

## Generated artifacts
Stored under `./volumes` (gitignored):
- `volumes/server/server.config.yaml` – server configuration with certificates
- `volumes/client/client.config.yaml` – client enrollment configuration
- `volumes/api/api.config.yaml` – mTLS API client credentials for host-side use
- `volumes/datastore` – Velociraptor datastore

## Customization
- Edit `.env` to pin a different Velociraptor release (`VELOCIRAPTOR_VERSION`), change ports, or set credentials.
- All bind addresses are set to `0.0.0.0` so GUI/API are reachable from the host through the published ports.

## Stopping and cleanup
```sh
podman compose down
# Remove generated data (irreversible)
rm -rf volumes/
```
