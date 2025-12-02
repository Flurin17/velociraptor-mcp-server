import argparse
import json
import sys
import os

import pytest

pyvelociraptor = pytest.importorskip("pyvelociraptor")
from pyvelociraptor import api_pb2, api_pb2_grpc
import grpc


def parse_args():
    p = argparse.ArgumentParser(description="Test Velociraptor API connectivity")
    p.add_argument("--config", default="volumes/api/api.config.yaml", help="Path to api.config.yaml")
    p.add_argument("--query", default="SELECT * FROM clients()", help="VQL query to run")
    p.add_argument("--org", default=None, help="Org ID (optional)")
    p.add_argument("--timeout", type=int, default=0, help="Query timeout (0 = stream)")
    return p.parse_args()


def main():
    args = parse_args()
    # Ensure proxies do not intercept gRPC connection to the local container
    for key in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
        os.environ.pop(key, None)
    try:
        cfg = pyvelociraptor.LoadConfigFile(args.config)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load API config: {exc}", file=sys.stderr)
        sys.exit(1)

    creds = grpc.ssl_channel_credentials(
        root_certificates=cfg["ca_certificate"].encode("utf-8"),
        private_key=cfg["client_private_key"].encode("utf-8"),
        certificate_chain=cfg["client_cert"].encode("utf-8"),
    )
    options = (("grpc.ssl_target_name_override", "VelociraptorServer"),)

    with grpc.secure_channel(cfg["api_connection_string"], creds, options) as channel:
        stub = api_pb2_grpc.APIStub(channel)
        request = api_pb2.VQLCollectorArgs(
            org_id=args.org or cfg.get("org_id", ""),
            max_wait=1,
            max_row=100,
            timeout=args.timeout,
            Query=[api_pb2.VQLRequest(Name="Test", VQL=args.query)],
        )
        try:
            for response in stub.Query(request):
                if response.Response:
                    for row in json.loads(response.Response):
                        print(row)
                elif response.log:
                    print(f"LOG {response.timestamp}: {response.log}")
        except Exception as exc:  # noqa: BLE001
            print(f"Query failed: {exc}", file=sys.stderr)
            sys.exit(2)


if __name__ == "__main__":
    main()
