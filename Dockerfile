FROM python:3.13-slim

WORKDIR /app
COPY . /app

# Install runtime deps only
RUN pip install --no-cache-dir .

# Expect caller to mount api.config.yaml or set env
ENV VELOCIRAPTOR_API_CONFIG=/app/velociraptor_lab/volumes/api/api.config.yaml \
    MCP_LOG_LEVEL=INFO \
    MCP_SERVER_NAME=velociraptor-mcp

CMD ["velociraptor-mcp", "--config", "/app/velociraptor_lab/volumes/api/api.config.yaml", "--log-level", "INFO", "--server-name", "velociraptor-mcp"]
