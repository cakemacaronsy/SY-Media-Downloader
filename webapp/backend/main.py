import glob
import logging
import os
import re
import tempfile
import threading
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Optional
from urllib.parse import quote

import yt_dlp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from helpers import (
    STORED_FILE_RE,
    build_ydl_format,
    clean_filename,
    detect_platform,
    is_http_url,
    media_type_for,
    AUDIO_FORMATS,
    VIDEO_FORMATS,
)

load_dotenv()
log = logging.getLogger("sy-downloader")

# --- Configuration (all via environment; see .env.example) -------------------
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
MAX_DOWNLOAD_SIZE_MB = int(os.getenv("MAX_DOWNLOAD_SIZE", "500"))
MAX_DURATION_SECONDS = int(os.getenv("MAX_DURATION_SECONDS", "3600"))
FILE_TTL_SECONDS = int(os.getenv("FILE_TTL_SECONDS", "900"))
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "5"))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
ALLOW_ANY_URL = os.getenv("ALLOW_ANY_URL", "false").lower() == "true"
TRUST_PROXY = os.getenv("TRUST_PROXY", "true").lower() == "true"  # read X-Forwarded-For (Railway/Render)
TRUST_PROXY_HOPS = max(1, int(os.getenv("TRUST_PROXY_HOPS", "1")))  # proxies between client and app
COOKIES_FILE = os.getenv("COOKIES_FILE")  # Netscape-format cookies.txt for Facebook/Instagram
COOKIES_CONTENT = os.getenv("COOKIES_CONTENT")  # same, pasted as an env var secret
COOKIE_PLATFORMS = {"facebook", "instagram"}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_slots = threading.BoundedSemaphore(MAX_CONCURRENT_DOWNLOADS)
_hits: dict = defaultdict(deque)
_hits_lock = threading.Lock()


@lru_cache(maxsize=1)
def _cookies_path() -> Optional[str]:
    if COOKIES_FILE and os.path.isfile(COOKIES_FILE):
        return COOKIES_FILE
    if COOKIES_CONTENT:
        path = os.path.join(tempfile.gettempdir(), "sy-cookies.txt")
        with open(path, "w") as f:
            f.write(COOKIES_CONTENT)
        os.chmod(path, 0o600)
        return path
    return None


def _sweep_loop():
    """Delete downloaded files older than FILE_TTL_SECONDS so the disk can't fill up."""
    while True:
        cutoff = time.time() - FILE_TTL_SECONDS
        for path in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
            try:
                if os.path.isfile(path) and os.path.getmtime(path) < cutoff:
                    os.remove(path)
            except OSError:
                pass
        with _jobs_lock:
            for job_id in [k for k, j in _jobs.items() if (j["finished_at"] or j["created_at"] + 6 * 3600) < cutoff]:
                del _jobs[job_id]
        time.sleep(60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    threading.Thread(target=_sweep_loop, daemon=True).start()
    yield


app = FastAPI(title="SY Media Downloader API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4"
    resolution: str = "best"


def _client_ip(request: Request) -> str:
    if TRUST_PROXY:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            # Clients can prepend fake entries; only the ones our own proxies appended
            # (counted from the right) are trustworthy.
            parts = [p.strip() for p in fwd.split(",") if p.strip()]
            if parts:
                return parts[-min(TRUST_PROXY_HOPS, len(parts))]
    return request.client.host if request.client else "unknown"


def _check_rate_limit(ip: str):
    now = time.time()
    with _hits_lock:
        q = _hits[ip]
        while q and q[0] < now - 60:
            q.popleft()
        if len(q) >= RATE_LIMIT_PER_MINUTE:
            raise HTTPException(429, "Too many requests. Please wait a minute and try again.")
        q.append(now)
        if len(_hits) > 10_000:  # bound memory: drop idle IPs
            for k in [k for k, v in _hits.items() if not v]:
                del _hits[k]


def _error_text(exc: Exception) -> str:
    text = re.sub(r"\x1b\[[0-9;]*m", "", str(exc))  # strip ANSI colours from yt-dlp
    text = re.sub(r"^ERROR:\s*", "", text)
    text = re.sub(r"\s*\(caused by .*$", "", text, flags=re.S)  # drop nested exception repr
    return text[:300]


class DownloadFailed(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message


def _validate(body: DownloadRequest):
    url = body.url.strip()
    fmt = body.format.lower()
    if not is_http_url(url):
        raise HTTPException(400, "Please enter a valid http(s) URL.")
    if fmt not in VIDEO_FORMATS + AUDIO_FORMATS:
        raise HTTPException(400, f"Unsupported format: {fmt}")
    platform = detect_platform(url)
    if platform == "unknown" and not ALLOW_ANY_URL:
        raise HTTPException(400, "This site is not supported.")
    return url, fmt, platform


def _admit(request: Request):
    """Rate limit and reserve a download slot. Caller must release _slots."""
    _check_rate_limit(_client_ip(request))
    if not _slots.acquire(blocking=False):
        raise HTTPException(503, "Server is busy. Please try again shortly.")


def _perform_download(file_id, url, fmt, resolution, platform, progress_hooks=(), pp_hooks=()) -> dict:
    """Run yt-dlp and return the API result. Raises DownloadFailed; never leaves partial files."""
    try:
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s"),
            "quiet": True,
            "noprogress": True,
            "noplaylist": True,
            "max_filesize": MAX_DOWNLOAD_SIZE_MB * 1024 * 1024,
            # `<=?` lets through media whose duration is unknown (many social posts);
            # live streams are refused outright since they never end.
            "match_filter": yt_dlp.utils.match_filter_func(f"duration <=? {MAX_DURATION_SECONDS} & !is_live"),
            "progress_hooks": list(progress_hooks),
            "postprocessor_hooks": list(pp_hooks),
            **build_ydl_format(fmt, resolution),
        }
        if platform in COOKIE_PLATFORMS:
            cookies = _cookies_path()
            if cookies:
                ydl_opts["cookiefile"] = cookies

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)  # single pass: metadata + download
        if not info:
            raise DownloadFailed(422, "Video was skipped (too long or too large).")
        title = info.get("title") or "download"
        downloads = info.get("requested_downloads") or []
        path = downloads[0].get("filepath") if downloads else None
        if not path or not os.path.exists(path):
            matches = glob.glob(os.path.join(DOWNLOAD_DIR, f"{file_id}.*"))
            path = matches[0] if matches else None
        if not path:
            raise DownloadFailed(422, "Nothing was downloaded: the video is live, longer than "
                                      f"{MAX_DURATION_SECONDS // 60} min, or larger than {MAX_DOWNLOAD_SIZE_MB} MB.")
    except Exception as e:
        if not isinstance(e, DownloadFailed):
            log.exception("download failed for %s", url)
            e = DownloadFailed(500, _error_text(e))
        for leftover in glob.glob(os.path.join(DOWNLOAD_DIR, f"{file_id}.*")):
            try:
                os.remove(leftover)
            except OSError:
                pass
        raise e

    stored = os.path.basename(path)
    ext = stored.rsplit(".", 1)[-1]
    return {
        "file": f"/api/file/{stored}?name={quote(clean_filename(title) + '.' + ext)}",
        "title": title,
        "platform": platform,
        "format": ext,
    }


# Plain `def` (not `async def`): FastAPI runs it in a worker thread, so a slow
# yt-dlp download no longer blocks the event loop (and /health).
@app.post("/api/download")
def download_video(body: DownloadRequest, request: Request):
    """Synchronous download: the response arrives when the file is ready."""
    url, fmt, platform = _validate(body)
    _admit(request)
    try:
        return _perform_download(uuid.uuid4().hex, url, fmt, body.resolution, platform)
    except DownloadFailed as e:
        if e.status == 500:
            return JSONResponse(status_code=500, content={"error": e.message})
        raise HTTPException(e.status, e.message)
    finally:
        _slots.release()


# --- Background jobs with progress ------------------------------------------
# Job state lives in this process's memory, so run a single uvicorn worker.
_jobs: dict = {}
SPLIT_PART_RE = re.compile(r"^[0-9a-f]{32}\.f[^.]+\.[a-z0-9]+$")
_jobs_lock = threading.Lock()


def _update_job(job_id: str, **fields):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is not None:
            job.update(fields)


def _make_progress_hook(job_id: str):
    seen_files: list = []
    best = {"progress": 0.0}

    def hook(d):
        try:  # an exception here would abort the download
            fname = d.get("filename") or ""
            # yt-dlp names the pieces of a video+audio download "<id>.f<format_id>.<ext>"
            # (and drops requested_formats from the hook's info_dict), so infer it here.
            parts = 2 if SPLIT_PART_RE.match(os.path.basename(fname)) else 1
            if fname not in seen_files:
                seen_files.append(fname)
            part = min(seen_files.index(fname), parts - 1)

            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                done = d.get("downloaded_bytes") or 0
                fields = {
                    "status": "downloading", "part": part + 1, "parts": parts,
                    "downloaded_bytes": done, "total_bytes": total,
                    "speed": d.get("speed"), "eta": d.get("eta"),
                }
                if total:
                    best["progress"] = max(best["progress"], (part + min(done / total, 1)) / parts * 100)
                    fields["progress"] = round(best["progress"], 1)
                _update_job(job_id, **fields)
            elif d.get("status") == "finished":
                best["progress"] = max(best["progress"], (part + 1) / parts * 100)
                _update_job(job_id, progress=round(best["progress"], 1), speed=None, eta=None)
        except Exception:
            log.debug("progress hook error", exc_info=True)

    return hook


def _make_pp_hook(job_id: str):
    def hook(d):
        if d.get("status") == "started":
            _update_job(job_id, status="processing", progress=100.0, speed=None, eta=None)
    return hook


def _run_job(job_id, url, fmt, resolution, platform):
    try:
        result = _perform_download(
            job_id, url, fmt, resolution, platform,
            progress_hooks=[_make_progress_hook(job_id)],
            pp_hooks=[_make_pp_hook(job_id)],
        )
        _update_job(job_id, status="done", progress=100.0, result=result, finished_at=time.time())
    except DownloadFailed as e:
        _update_job(job_id, status="error", error=e.message, finished_at=time.time())
    except Exception as e:  # defensive: a job must never stay "running" forever
        log.exception("job %s crashed", job_id)
        _update_job(job_id, status="error", error=_error_text(e), finished_at=time.time())
    finally:
        _slots.release()


@app.post("/api/jobs", status_code=202)
def create_job(body: DownloadRequest, request: Request):
    """Start a download in the background; poll GET /api/jobs/{id} for progress."""
    url, fmt, platform = _validate(body)
    _admit(request)
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        _jobs[job_id] = {
            "id": job_id, "status": "queued", "progress": 0.0, "platform": platform,
            "part": 0, "parts": 1, "downloaded_bytes": 0, "total_bytes": None,
            "speed": None, "eta": None, "result": None, "error": None,
            "created_at": time.time(), "finished_at": None,
        }
    try:
        threading.Thread(target=_run_job, args=(job_id, url, fmt, body.resolution, platform), daemon=True).start()
    except Exception:
        _slots.release()
        with _jobs_lock:
            _jobs.pop(job_id, None)
        raise
    return {"id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Job not found (it may have expired).")
        return {k: v for k, v in job.items() if k not in ("created_at", "finished_at")}


@app.get("/api/file/{filename}")
def get_file(filename: str, name: Optional[str] = None):
    if not STORED_FILE_RE.match(filename):
        raise HTTPException(404, "File not found")
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(404, "File not found")

    ext = filename.rsplit(".", 1)[-1]
    download_name = f"{clean_filename(name.rsplit('.', 1)[0])}.{ext}" if name else filename
    return FileResponse(
        path=file_path,
        media_type=media_type_for(filename) or "application/octet-stream",
        filename=download_name,  # sets Content-Disposition: attachment
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {"status": "healthy", "service": "SY Media Downloader API"}


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SY Media Downloader API",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health",
    }
