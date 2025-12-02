from __future__ import annotations

from pathlib import Path

import pytest

from mcp_server.config import load_config
from mcp_server.tools import artifacts, clients, files, hunts, monitoring, vql


@pytest.fixture()
def cfg(tmp_path: Path):
    api_cfg = tmp_path / "api.config.yaml"
    api_cfg.write_text("dummy: true")
    return load_config(default_path=api_cfg)


@pytest.fixture()
def fake_client(monkeypatch):
    class FakeClient:
        def __init__(self):
            self.queries = []
            self.downloads = []

        def query(self, vql_stmt, params=None):
            self.queries.append((vql_stmt, params))
            return [{"ok": True}]

        def download(self, client_id, path, offset=0, length=0):
            self.downloads.append((client_id, path, offset, length))
            return b"data"

    fc = FakeClient()
    # Replace get_client in each tool module so every call uses the shared fake.
    for module in (vql, clients, hunts, artifacts, files):
        monkeypatch.setattr(module, "get_client", lambda _cfg, fc=fc: fc)
    return fc


def test_query_vql_passes_through(cfg, fake_client):
    out = vql.query_vql(cfg, "SELECT 1")
    assert out["rows"] == [{"ok": True}]
    stmt, _ = fake_client.queries[0]
    assert "SELECT 1" in stmt


def test_list_clients_builds_vql(cfg, fake_client):
    clients.list_clients(cfg, limit=10, offset=5)
    stmt, _ = fake_client.queries[-1]
    assert stmt.strip() == "SELECT * FROM clients()"


def test_get_client_info_uses_id(cfg, fake_client):
    clients.get_client_info(cfg, "C.1234")
    stmt, _ = fake_client.queries[-1]
    assert "clients()" in stmt and "C.1234" in stmt


def test_search_clients_combines_predicates(cfg, fake_client):
    clients.search_clients(
        cfg, hostname="host", label="prod", query="OS = 'linux'", limit=50
    )
    stmt, _ = fake_client.queries[-1]
    assert "Hostname =~ 'host'" in stmt
    assert "Labels =~ 'prod'" in stmt
    assert "OS = 'linux'" in stmt
    assert stmt.strip().startswith("SELECT * FROM clients() WHERE")


def test_list_hunts_with_state(cfg, fake_client):
    hunts.list_hunts(cfg, state="RUNNING", limit=10)
    stmt, _ = fake_client.queries[-1]
    assert "FROM hunts()" in stmt and "State = 'RUNNING'" in stmt and "LIMIT 10" in stmt


def test_create_hunt_includes_query_and_flag(cfg, fake_client):
    hunts.create_hunt(
        cfg,
        artifact="Demo.Art",
        query="SELECT * FROM info()",
        description="desc",
        start_immediately=False,
    )
    stmt, _ = fake_client.queries[-1]
    assert "hunt(" in stmt and "Demo.Art" in stmt
    assert "SELECT * FROM info()" in stmt
    assert "start_immediately=false" in stmt


def test_stop_hunt(cfg, fake_client):
    hunts.stop_hunt(cfg, "H.111")
    stmt, _ = fake_client.queries[-1]
    assert "hunt_delete" in stmt and "H.111" in stmt


def test_get_hunt_results_with_client(cfg, fake_client):
    hunts.get_hunt_results(cfg, "H.222", client_id="C.1", limit=5)
    stmt, _ = fake_client.queries[-1]
    assert (
        "hunt_results" in stmt
        and "H.222" in stmt
        and "ClientId = 'C.1'" in stmt
        and "LIMIT 5" in stmt
    )


def test_artifact_tools(cfg, fake_client):
    artifacts.list_artifacts(cfg, search="Windows")
    stmt, _ = fake_client.queries[-1]
    assert "Windows" in stmt and "artifact_definitions" in stmt

    artifacts.collect_artifact(
        cfg, client_id="C.9", artifact="Sys.Info", params={"foo": "bar"}
    )
    stmt, _ = fake_client.queries[-1]
    assert "collect_client" in stmt and "FROM scope()" in stmt

    artifacts.upload_artifact(
        cfg, name="Custom.Art", vql="SELECT 1", description="d", type_="CLIENT"
    )
    stmt, _ = fake_client.queries[-1]
    assert "artifact_set" in stmt and "Custom.Art" in stmt and "SELECT 1" in stmt

    artifacts.get_artifact_definition(cfg, name="Windows.Sys")
    stmt, _ = fake_client.queries[-1]
    assert "artifact_definitions" in stmt and "Windows.Sys" in stmt


def test_file_tools_and_download(cfg, fake_client):
    files.list_directory(cfg, client_id="C.7", path="/tmp")
    assert "vfs_files" in fake_client.queries[-1][0]

    files.get_file_info(cfg, client_id="C.7", path="/tmp/file.txt")
    assert "vfs_files" in fake_client.queries[-1][0]

    out = files.download_file(
        cfg, client_id="C.7", path="/tmp/file.txt", offset=1, length=2
    )
    # download uses gRPC VFSGetBuffer directly
    assert out["path"] == "/tmp/file.txt"
    assert out["length"] >= 0
    assert fake_client.downloads[-1] == ("C.7", "/tmp/file.txt", 1, 2)


def test_monitoring_tools(cfg, fake_client):
    with pytest.raises(RuntimeError):
        monitoring.get_server_stats(cfg)
    with pytest.raises(RuntimeError):
        monitoring.get_client_activity(cfg, limit=3)
    with pytest.raises(RuntimeError):
        monitoring.list_alerts(cfg, limit=4)
    with pytest.raises(RuntimeError):
        monitoring.create_alert(
            cfg, title="t", message="m", client_id="C.5", severity="ERROR"
        )
