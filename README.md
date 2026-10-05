# SY Media Downloader

A small web app for downloading video and audio from YouTube, TikTok, Twitter/X, Reddit, Vimeo, Pinterest, Facebook and Instagram. A React frontend talks to a FastAPI backend that wraps [yt-dlp](https://github.com/yt-dlp/yt-dlp) and FFmpeg.

## Features

- Paste a URL; the platform is detected from the hostname
- Live progress bar with size, speed and time remaining
- Video: MP4 (H.264/AAC where available, plays in QuickTime), WEBM, MKV, AVI
- Audio: MP3, M4A, WAV, FLAC
- Resolution ceiling from 144p to 4K ("720p" means *up to* 720p)
- In-browser preview for MP4, WEBM, MP3, M4A and WAV
- Dark / light theme

Not implemented: playlists, batch downloads, subtitles, download history, desktop GUI.

## Project layout

```
webapp/
  backend/            FastAPI + yt-dlp API
    main.py           endpoints, rate limiting, cleanup
    helpers.py        platform detection, format selection (pure, unit tested)
    tests/            pytest suite
  frontend/           React (Create React App)
Dockerfile            backend image (includes FFmpeg)
```

## Run locally

Requirements: Python 3.11+, Node 18+, FFmpeg on your `PATH`.

```bash
# Backend (http://localhost:8000, API docs at /docs)
cd webapp/backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend (http://localhost:3000), in a second terminal
cd webapp/frontend
npm install
npm start
```

Run the backend tests:

```bash
cd webapp/backend
pip install -r requirements-dev.txt
pytest
```

## API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/jobs` | Body `{"url", "format", "resolution"}`. Starts a background download, returns `202 {id}`. |
| `GET` | `/api/jobs/{id}` | `status` (`queued` / `downloading` / `processing` / `done` / `error`), `progress` 0–100, `downloaded_bytes`, `total_bytes`, `speed`, `eta`, and `result` (same shape as below) when done. |
| `POST` | `/api/download` | Synchronous variant: same body, responds when finished with `{file, title, platform, format}`. |
| `GET` | `/api/file/{id}.{ext}?name=...` | Serves the file as an attachment named after the video. |
| `GET` | `/health` | Health check. |

Errors return `{"error": ...}` (download failures) or `{"detail": ...}` (validation `400`, rate limit `429`, busy `503`).

## Configuration

Backend settings are environment variables; see [`webapp/backend/.env.example`](webapp/backend/.env.example).

| Variable | Default | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated frontend origins for CORS |
| `MAX_DOWNLOAD_SIZE` | `500` | Max file size in MB |
| `MAX_DURATION_SECONDS` | `3600` | Longer videos are refused |
| `FILE_TTL_SECONDS` | `900` | Downloaded files are deleted after this |
| `RATE_LIMIT_PER_MINUTE` | `5` | Download requests per client IP |
| `MAX_CONCURRENT_DOWNLOADS` | `2` | Extra requests get `503` |
| `ALLOW_ANY_URL` | `false` | Let yt-dlp try sites outside the supported list |
| `TRUST_PROXY` / `TRUST_PROXY_HOPS` | `true` / `1` | Read the client IP from `X-Forwarded-For` behind N proxies |
| `COOKIES_FILE` or `COOKIES_CONTENT` | unset | Netscape `cookies.txt` used for Facebook and Instagram |

The frontend reads `REACT_APP_API_URL` at build time (see `webapp/frontend/.env.production`).

## Deployment notes

- Build the backend with the `Dockerfile`; it installs FFmpeg and listens on `$PORT`.
- Run a single uvicorn worker: job progress is kept in process memory.
- YouTube and others frequently block requests from cloud/datacenter IPs, so a hosted backend may fail where a local one works.
- Instagram and most Facebook videos need logged-in cookies (`COOKIES_CONTENT`). Treat that file as a password.
- Downloading content may violate a platform's terms of service or copyright. Only download media you have the right to.

## License

MIT, see [LICENSE](LICENSE).
