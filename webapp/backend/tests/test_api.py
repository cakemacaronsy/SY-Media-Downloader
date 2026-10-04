import importlib
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    import main
    importlib.reload(main)
    return TestClient(main.app), main, tmp_path


def test_rejects_non_http_and_unsupported(client):
    c, _, _ = client
    assert c.post("/api/download", json={"url": "file:///etc/passwd"}).status_code == 400
    assert c.post("/api/download", json={"url": "https://example.com/v"}).status_code == 400
    assert c.post("/api/download", json={"url": "https://youtu.be/a", "format": "exe"}).status_code == 400


def test_download_success_uses_uuid_name_and_friendly_download_name(client, monkeypatch):
    c, main, tmp = client

    class FakeYDL:
        def __init__(self, opts): self.opts = opts
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def extract_info(self, url, download):
            path = self.opts["outtmpl"].replace("%(ext)s", "mp4")
            open(path, "wb").write(b"x")
            return {"title": "My Video: Part/1", "requested_downloads": [{"filepath": path}]}

    monkeypatch.setattr(main.yt_dlp, "YoutubeDL", FakeYDL)
    r = c.post("/api/download", json={"url": "https://youtu.be/abc", "format": "mp4"})
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "My Video: Part/1"
    f = c.get(body["file"])
    assert f.status_code == 200
    assert "My_Video_Part1.mp4" in f.headers["content-disposition"]
    assert f.headers["content-disposition"].startswith("attachment")


def test_file_endpoint_rejects_non_uuid_names(client):
    c, _, tmp = client
    (tmp / "secret.txt").write_text("nope")
    assert c.get("/api/file/secret.txt").status_code == 404
    assert c.get("/api/file/..%2Fmain.py").status_code == 404


def test_rate_limit(client, monkeypatch):
    c, main, _ = client

    def boom(*a, **k): raise RuntimeError("fail")
    monkeypatch.setattr(main.yt_dlp, "YoutubeDL", boom)
    codes = [c.post("/api/download", json={"url": "https://youtu.be/a"}).status_code for _ in range(5)]
    assert codes[:3] == [500, 500, 500] and codes[3:] == [429, 429]


def test_health(client):
    assert client[0].get("/health").json()["status"] == "healthy"
