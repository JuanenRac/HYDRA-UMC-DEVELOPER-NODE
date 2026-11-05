# =============================================================================
# HYDRA-UMC-DEVELOPER-NODE - tests/test_server_push.py
# Copyright (C) 2026 JuanenRac (Electro Hobby 3D) <electrohobby3d@gmail.com>
# GPL-3.0-or-later - see LICENSE
# =============================================================================
"""`panel push`: the status document goes to the server with the token of this node; closed by default, HTTPS only, no redirect, no secret in an error."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest

from hydra_umc_developer_node import panel
from hydra_umc_developer_node.settings import SettingsError, parse_settings
from hydra_umc_developer_node.store import Store

TOKEN = "node-token-0123456789abcdef"


def _settings(tmp_path: Path, **push: Any):
    section = {"enabled": True, "url": "http://127.0.0.1:1", "nodeId": "dev-1", "tokenEnv": "DEV_NODE_TEST_TOKEN"}
    section.update(push)
    return parse_settings({"dataDir": str(tmp_path / "data"), "panel": {"enabled": True}, "serverPush": section})


class _Server:
    def __init__(self, status: int = 201, redirect: str | None = None) -> None:
        outer = self
        self.seen: list[dict[str, Any]] = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args: Any) -> None:
                pass

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length", "0"))
                outer.seen.append({"path": self.path, "auth": self.headers.get("Authorization"), "node": self.headers.get("X-Node-Id"),
                                   "body": json.loads(self.rfile.read(length))})
                if redirect:
                    self.send_response(302)
                    self.send_header("Location", redirect)
                    self.end_headers()
                    return
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"node_id": "dev-1", "seq": 3}).encode())

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def test_it_is_closed_by_default(tmp_path: Path) -> None:
    settings = parse_settings({"dataDir": str(tmp_path / "data"), "panel": {"enabled": True}})
    assert settings.switches()["serverPush"] is False
    with Store(settings.data_path() / "node.sqlite") as store, pytest.raises(panel.PanelError):
        panel.push_status(settings, store)


def test_the_settings_are_checked() -> None:
    for bad in ({"serverPush": {"nope": 1}}, {"serverPush": {"enabled": "yes"}}, {"serverPush": {"timeoutSeconds": 0}}):
        with pytest.raises(SettingsError):
            parse_settings(bad)


def test_the_status_document_reaches_the_server_with_the_token_of_the_node(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _Server()
    try:
        monkeypatch.setenv("DEV_NODE_TEST_TOKEN", TOKEN)
        settings = _settings(tmp_path, url=server.url)
        with Store(settings.data_path() / "node.sqlite") as store:
            result = panel.push_status(settings, store, now=1.0)
        assert result == {"status": 201, "answer": {"node_id": "dev-1", "seq": 3}}
        sent = server.seen[0]
        assert sent["path"] == "/api/ingest/developer-node/status" and sent["auth"] == f"Bearer {TOKEN}" and sent["node"] == "dev-1"
        assert sent["body"]["contract"] == "developer-node-status/1" and sent["body"]["generated_at"] == 1.0
    finally:
        server.close()


def test_the_token_can_come_from_a_file(tmp_path: Path) -> None:
    server = _Server()
    try:
        token_file = tmp_path / "token"
        token_file.write_text(TOKEN + "\n", encoding="utf-8")
        settings = _settings(tmp_path, url=server.url, tokenFile=str(token_file))
        with Store(settings.data_path() / "node.sqlite") as store:
            panel.push_status(settings, store)
        assert server.seen[0]["auth"] == f"Bearer {TOKEN}"
    finally:
        server.close()


def test_no_or_short_token_sends_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _Server()
    try:
        settings = _settings(tmp_path, url=server.url)
        monkeypatch.delenv("DEV_NODE_TEST_TOKEN", raising=False)
        with Store(settings.data_path() / "node.sqlite") as store, pytest.raises(panel.PushError):
            panel.push_status(settings, store)
        monkeypatch.setenv("DEV_NODE_TEST_TOKEN", "short")
        with Store(settings.data_path() / "node.sqlite") as store, pytest.raises(panel.PushError):
            panel.push_status(settings, store)
        assert server.seen == []
    finally:
        server.close()


def test_a_plain_http_url_for_another_machine_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEV_NODE_TEST_TOKEN", TOKEN)
    for url in ("http://server.example", "ftp://server.example", "https://user:pw@server.example", "https://"):
        settings = _settings(tmp_path, url=url)
        with Store(settings.data_path() / "node.sqlite") as store, pytest.raises(panel.PushError):
            panel.push_status(settings, store)


def test_a_redirect_is_not_followed_and_the_error_does_not_carry_the_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    other = _Server()
    server = _Server(redirect=other.url + "/steal")
    try:
        monkeypatch.setenv("DEV_NODE_TEST_TOKEN", TOKEN)
        settings = _settings(tmp_path, url=server.url)
        with Store(settings.data_path() / "node.sqlite") as store, pytest.raises(panel.PushError) as raised:
            panel.push_status(settings, store)
        assert TOKEN not in str(raised.value)
        assert other.seen == []
    finally:
        server.close()
        other.close()


def test_a_refusal_of_the_server_is_reported_without_the_token(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = _Server(status=401)
    try:
        monkeypatch.setenv("DEV_NODE_TEST_TOKEN", TOKEN)
        settings = _settings(tmp_path, url=server.url)
        with Store(settings.data_path() / "node.sqlite") as store, pytest.raises(panel.PushError) as raised:
            panel.push_status(settings, store)
        assert "401" in str(raised.value) and TOKEN not in str(raised.value)
    finally:
        server.close()
