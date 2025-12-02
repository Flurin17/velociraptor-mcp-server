from pathlib import Path

import pytest

from mcp_server.config import ConfigError, load_config


def test_load_config_success(tmp_path: Path):
    api_cfg = tmp_path / "api.config.yaml"
    api_cfg.write_text("dummy: true")
    cfg = load_config(default_path=api_cfg)
    assert cfg.api_config_path == api_cfg
    assert cfg.server_name == "velociraptor-mcp"


def test_load_config_missing(tmp_path: Path):
    with pytest.raises(ConfigError):
        load_config(default_path=tmp_path / "missing.yaml")


def test_build_server_initializes(tmp_path: Path):
    """FastMCP is available in the environment; server should initialize."""
    api_cfg = tmp_path / "api.config.yaml"
    api_cfg.write_text("dummy: true")
    cfg = load_config(default_path=api_cfg)
    from mcp_server import server

    mcp = server.build_server(cfg)
    assert hasattr(mcp, "run")
