from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

DEFAULT_API_CONFIG = Path("volumes/api/api.config.yaml")


class ConfigError(RuntimeError):
    """Raised when configuration is invalid or missing."""


@dataclass(frozen=True)
class ServerConfig:
    api_config_path: Path
    log_level: str = "INFO"
    server_name: str = "velociraptor-mcp"


def load_config(
    api_config_env: str = "VELOCIRAPTOR_API_CONFIG",
    default_path: Path | None = DEFAULT_API_CONFIG,
    log_level_env: str = "MCP_LOG_LEVEL",
    server_name_env: str = "MCP_SERVER_NAME",
) -> ServerConfig:
    """
    Resolve configuration from environment with sane defaults.

    - api_config_path: env `VELOCIRAPTOR_API_CONFIG` or `volumes/api/api.config.yaml`
    - log_level: env `MCP_LOG_LEVEL` or INFO
    - server_name: env `MCP_SERVER_NAME` or velociraptor-mcp
    """
    api_path_str: Optional[str] = os.getenv(api_config_env)
    if api_path_str:
        api_path = Path(api_path_str)
    elif default_path is not None:
        api_path = Path(default_path)
    else:
        api_path = DEFAULT_API_CONFIG

    if not api_path.exists():
        raise ConfigError(
            f"Velociraptor API config not found at {api_path}. "
            "Generate it via velociraptor_lab (podman compose up) or set VELOCIRAPTOR_API_CONFIG."
        )

    log_level = os.getenv(log_level_env, "INFO").upper()
    server_name = os.getenv(server_name_env, "velociraptor-mcp")

    return ServerConfig(api_config_path=api_path, log_level=log_level, server_name=server_name)
