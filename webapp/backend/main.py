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
COOKIES_FILE = os.getenv("COOKIES_FILE")  # Netscape-format cookies.txt for Facebook/Instagram
COOKIES_CONTENT = os.getenv("COOKIES_CONTENT")  # same, pasted as an env var secret
COOKIE_PLATFORMS = {"facebook", "instagram"}

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

_slots = threading.BoundedSemaphore(MAX_CONCURRENT_DOWNLOADS)
_hits: dict = defaultdict(deque)
_hits_lock = threading.Lock()


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
            return fwd.split(",")[0].strip()
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
    return text[:300]


# Plain `def` (not `async def`): FastAPI runs it in a worker thread, so a slow
# yt-dlp download no longer blocks the event loop (and /health).
@app.post("/api/download")
def download_video(body: DownloadRequest, request: Request):
    url = body.url.strip()
    fmt = body.format.lower()

    if not is_http_url(url):
        raise HTTPException(400, "Please enter a valid http(s) URL.")
    if fmt not in VIDEO_FORMATS + AUDIO_FORMATS:
        raise HTTPException(400, f"Unsupported format: {fmt}")
    platform = detect_platform(url)
    if platform == "unknown" and not ALLOW_ANY_URL:
        raise HTTPException(400, "This site is not supported.")

    _check_rate_limit(_client_ip(request))
    if not _slots.acquire(blocking=False):
        raise HTTPException(503, "Server is busy. Please try again shortly.")

    file_id = uuid.uuid4().hex
    ydl_opts = {
        "outtmpl": os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s"),
        "quiet": True,
        "noplaylist": True,
        "max_filesize": MAX_DOWNLOAD_SIZE_MB * 1024 * 1024,
        "match_filter": yt_dlp.utils.match_filter_func(f"duration <= {MAX_DURATION_SECONDS}"),
        **build_ydl_format(fmt, body.resolution),
    }
    if platform in COOKIE_PLATFORMS:
        cookies = _cookies_path()
        if cookies:
            ydl_opts["cookiefile"] = cookies

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)  # single pass: metadata + download
        if not info:
            raise HTTPException(422, "Video was skipped (too long or too large).")
        title = info.get("title") or "download"
        downloads = info.get("requested_downloads") or []
        path = downloads[0].get("filepath") if downloads else None
        if not path or not os.path.exists(path):
            matches = glob.glob(os.path.join(DOWNLOAD_DIR, f"{file_id}.*"))
            path = matches[0] if matches else None
        if not path:
            raise HTTPException(422, "Nothing was downloaded (file may exceed the size limit).")
    except HTTPException:
        raise
    except Exception as e:
        log.exception("download failed for %s", url)
        for leftover in glob.glob(os.path.join(DOWNLOAD_DIR, f"{file_id}.*")):
            os.remove(leftover)
        return JSONResponse(status_code=500, content={"error": _error_text(e)})
    finally:
        _slots.release()

    stored = os.path.basename(path)
    ext = stored.rsplit(".", 1)[-1]
    return {
        "file": f"/api/file/{stored}?name={quote(clean_filename(title) + '.' + ext)}",
        "title": title,
        "platform": platform,
        "format": ext,
    }


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
