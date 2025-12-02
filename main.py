from __future__ import annotations

import argparse
import dataclasses
import sys

from mcp_server.config import ConfigError, load_config
from mcp_server.server import build_server


def parse_args():
    parser = argparse.ArgumentParser(description="Velociraptor MCP server (FastMCP).")
    parser.add_argument(
        "--config",
        dest="api_config",
        help="Path to velociraptor api.config.yaml (defaults to volumes/api/api.config.yaml or env VELOCIRAPTOR_API_CONFIG).",
    )
    parser.add_argument("--log-level", dest="log_level", default=None, help="Log level (INFO, DEBUG, ...)")
    parser.add_argument("--server-name", dest="server_name", default=None, help="MCP server name")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        cfg = load_config(
            default_path=args.api_config if args.api_config else None,
        )
        if args.log_level:
            cfg = dataclasses.replace(cfg, log_level=args.log_level.upper())
        if args.server_name:
            cfg = dataclasses.replace(cfg, server_name=args.server_name)
    except ConfigError as exc:
        sys.stderr.write(f"Config error: {exc}\n")
        sys.exit(1)

    server = build_server(cfg)

    try:
        server.run()  # type: ignore[attr-defined]
    except AttributeError:
        sys.stderr.write("fastmcp.FastMCP.run() not found. Ensure fastmcp is up to date.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
