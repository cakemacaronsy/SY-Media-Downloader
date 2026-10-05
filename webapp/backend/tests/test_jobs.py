import importlib
import threading
import time

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "100")
    import main
    importlib.reload(main)
    return TestClient(main.app), main


def wait_for(c, job_id, pred, timeout=5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = c.get(f"/api/jobs/{job_id}").json()
        if pred(job):
            return job
        time.sleep(0.02)
    raise AssertionError(f"timed out; last state {job}")


def make_fake(gate: threading.Event, fail=False):
    """Fake YoutubeDL that reports a 2-part (video+audio) download, pausing halfway."""
    class FakeYDL:
        def __init__(self, opts): self.opts = opts
        def __enter__(self): return self
        def __exit__(self, *a): return False

        def extract_info(self, url, download):
            hook = self.opts["progress_hooks"][0]
            info = {"format_id": "137"}  # real yt-dlp strips requested_formats per part
            base = self.opts["outtmpl"].replace(".%(ext)s", "")
            hook({"status": "downloading", "filename": base + ".f137.mp4", "info_dict": info,
                  "downloaded_bytes": 50, "total_bytes": 100, "speed": 10.0, "eta": 5})
            gate.wait(5)
            if fail:
                raise RuntimeError("\x1b[0;31mERROR:\x1b[0m Video unavailable (caused by HTTPError('403'))")
            hook({"status": "finished", "filename": base + ".f137.mp4", "info_dict": info})
            hook({"status": "downloading", "filename": base + ".f140.m4a", "info_dict": info,
                  "downloaded_bytes": 10, "total_bytes": None, "total_bytes_estimate": 20})
            hook({"status": "finished", "filename": base + ".f140.m4a", "info_dict": info})
            self.opts["postprocessor_hooks"][0]({"status": "started", "postprocessor": "Merger"})
            path = base + ".mp4"
            open(path, "wb").write(b"video")
            return {"title": "Clip", "requested_downloads": [{"filepath": path}]}
    return FakeYDL


def test_job_reports_progress_then_result(env, monkeypatch):
    c, main = env
    gate = threading.Event()
    monkeypatch.setattr(main.yt_dlp, "YoutubeDL", make_fake(gate))

    r = c.post("/api/jobs", json={"url": "https://youtu.be/a", "format": "mp4"})
    assert r.status_code == 202
    job_id = r.json()["id"]

    mid = wait_for(c, job_id, lambda j: j["status"] == "downloading")
    assert mid["progress"] == 25.0  # half of part 1 of 2
    assert (mid["part"], mid["parts"], mid["eta"]) == (1, 2, 5)

    gate.set()
    done = wait_for(c, job_id, lambda j: j["status"] == "done")
    assert done["progress"] == 100.0
    assert done["result"]["title"] == "Clip"
    f = c.get(done["result"]["file"])
    assert f.status_code == 200 and f.content == b"video"


def test_job_error_is_reported_and_slot_released(env, monkeypatch):
    c, main = env
    gate = threading.Event()
    gate.set()
    monkeypatch.setattr(main.yt_dlp, "YoutubeDL", make_fake(gate, fail=True))
    for _ in range(main.MAX_CONCURRENT_DOWNLOADS + 2):
        job_id = c.post("/api/jobs", json={"url": "https://youtu.be/a"}).json()["id"]
        job = wait_for(c, job_id, lambda j: j["status"] == "error")
        assert job["error"] == "Video unavailable"


def test_busy_when_all_slots_taken(env, monkeypatch):
    c, main = env
    gate = threading.Event()
    monkeypatch.setattr(main.yt_dlp, "YoutubeDL", make_fake(gate))
    ids = [c.post("/api/jobs", json={"url": "https://youtu.be/a"}).json()["id"]
           for _ in range(main.MAX_CONCURRENT_DOWNLOADS)]
    assert c.post("/api/jobs", json={"url": "https://youtu.be/a"}).status_code == 503
    gate.set()
    for job_id in ids:
        wait_for(c, job_id, lambda j: j["status"] == "done")
    assert c.post("/api/jobs", json={"url": "https://youtu.be/a"}).status_code == 202


def test_job_validation_and_unknown_id(env):
    c, _ = env
    assert c.post("/api/jobs", json={"url": "ftp://x"}).status_code == 400
    assert c.get("/api/jobs/" + "0" * 32).status_code == 404


def test_single_file_progress(env, monkeypatch):
    c, main = env
    hook = main._make_progress_hook("x" * 32)
    main._jobs["x" * 32] = {"finished_at": None, "created_at": 0}
    hook({"status": "downloading", "filename": "/d/" + "a" * 32 + ".mp4",
          "downloaded_bytes": 30, "total_bytes": 100})
    assert main._jobs["x" * 32]["progress"] == 30.0
    assert main._jobs["x" * 32]["parts"] == 1
