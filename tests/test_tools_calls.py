from __future__ import annotations

import base64
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
    for module in (vql, clients, hunts, artifacts, files, monitoring):
        monkeypatch.setattr(module, "get_client", lambda _cfg, fc=fc: fc)
    return fc


def test_query_vql_passes_through(cfg, fake_client):
    out = vql.query_vql(cfg, "SELECT 1")
    assert out["rows"] == [{"ok": True}]
    stmt, params = fake_client.queries[0]
    assert "SELECT 1" in stmt
    assert params is None


def test_list_clients_builds_vql(cfg, fake_client):
    clients.list_clients(cfg, limit=10, offset=5)
    stmt, _ = fake_client.queries[-1]
    assert "clients()" in stmt and "LIMIT 10" in stmt and "OFFSET 5" in stmt


def test_get_client_info_uses_id(cfg, fake_client):
    clients.get_client_info(cfg, "C.1234")
    stmt, _ = fake_client.queries[-1]
    assert "client_info" in stmt and "C.1234" in stmt


def test_search_clients_combines_predicates(cfg, fake_client):
    clients.search_clients(cfg, hostname="host", label="prod", query="OS = 'linux'", limit=50)
    stmt, _ = fake_client.queries[-1]
    assert "Hostname =~ 'host'" in stmt
    assert "Labels =~ 'prod'" in stmt
    assert "OS = 'linux'" in stmt
    assert "LIMIT 50" in stmt


def test_list_hunts_with_state(cfg, fake_client):
    hunts.list_hunts(cfg, state="RUNNING", limit=10)
    stmt, _ = fake_client.queries[-1]
    assert "FROM hunts()" in stmt and "State = 'RUNNING'" in stmt and "LIMIT 10" in stmt


def test_create_hunt_includes_query_and_flag(cfg, fake_client):
    hunts.create_hunt(cfg, artifact="Demo.Art", query="SELECT * FROM info()", description="desc", start_immediately=False)
    stmt, _ = fake_client.queries[-1]
    assert "Demo.Art" in stmt
    assert "SELECT * FROM info()" in stmt
    assert "start_immediately=false" in stmt


def test_stop_hunt(cfg, fake_client):
    hunts.stop_hunt(cfg, "H.111")
    stmt, _ = fake_client.queries[-1]
    assert "stop_hunt" in stmt and "H.111" in stmt


def test_get_hunt_results_with_client(cfg, fake_client):
    hunts.get_hunt_results(cfg, "H.222", client_id="C.1", limit=5)
    stmt, _ = fake_client.queries[-1]
    assert "hunt_results" in stmt and "H.222" in stmt and "ClientId = 'C.1'" in stmt and "LIMIT 5" in stmt


def test_artifact_tools(cfg, fake_client):
    artifacts.list_artifacts(cfg, search="Windows")
    assert "Windows" in fake_client.queries[-1][0]

    artifacts.collect_artifact(cfg, client_id="C.9", artifact="Sys.Info", params={"foo": "bar"})
    stmt, _ = fake_client.queries[-1]
    assert "collect_client" in stmt and "C.9" in stmt and "Sys.Info" in stmt and "parameters={'foo': 'bar'}" in stmt

    artifacts.upload_artifact(cfg, name="Custom.Art", vql="SELECT 1", description="d", type_="CLIENT")
    stmt, _ = fake_client.queries[-1]
    assert "upload_artifact" in stmt and "Custom.Art" in stmt and "SELECT 1" in stmt

    artifacts.get_artifact_definition(cfg, name="Windows.Sys")
    stmt, _ = fake_client.queries[-1]
    assert "artifact_definition" in stmt and "Windows.Sys" in stmt


def test_file_tools_and_download(cfg, fake_client):
    files.list_directory(cfg, client_id="C.7", path="/tmp")
    assert "vfs_listdir" in fake_client.queries[-1][0]

    files.get_file_info(cfg, client_id="C.7", path="/tmp/file.txt")
    assert "stat_vfs" in fake_client.queries[-1][0]

    out = files.download_file(cfg, client_id="C.7", path="/tmp/file.txt", offset=1, length=2)
    assert fake_client.downloads[-1] == ("C.7", "/tmp/file.txt", 1, 2)
    assert out["data_base64"] == base64.b64encode(b"data").decode("ascii")
    assert out["length"] == 2


def test_monitoring_tools(cfg, fake_client):
    monitoring.get_server_stats(cfg)
    assert "server_stats" in fake_client.queries[-1][0]

    monitoring.get_client_activity(cfg, limit=3)
    assert "client_activity" in fake_client.queries[-1][0] and "LIMIT 3" in fake_client.queries[-1][0]

    monitoring.list_alerts(cfg, limit=4)
    assert "alerts()" in fake_client.queries[-1][0] and "LIMIT 4" in fake_client.queries[-1][0]

    monitoring.create_alert(cfg, title="t", message="m", client_id="C.5", severity="ERROR")
    stmt, _ = fake_client.queries[-1]
    assert "create_alert" in stmt and 'title="t"' in stmt and 'message="m"' in stmt
    assert 'client_id=\'C.5\'' in stmt and 'severity="ERROR"' in stmt
