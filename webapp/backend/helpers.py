"""Pure helpers for the downloader API (no network, easy to unit test)."""
import re
from typing import Optional
from urllib.parse import urlparse

VIDEO_FORMATS = ("mp4", "webm", "mkv", "avi")
AUDIO_FORMATS = ("mp3", "m4a", "wav", "flac")
RESOLUTIONS = ("2160", "1440", "1080", "720", "480", "360", "240", "144")

# platform name -> registrable domains (matched against the URL hostname)
PLATFORM_DOMAINS = {
    "youtube": ("youtube.com", "youtu.be"),
    "facebook": ("facebook.com", "fb.watch"),
    "instagram": ("instagram.com",),
    "tiktok": ("tiktok.com",),
    "twitter": ("twitter.com", "x.com"),
    "reddit": ("reddit.com", "redd.it"),
    "vimeo": ("vimeo.com",),
    "pinterest": ("pinterest.com", "pin.it"),
}

# Files are stored as <uuid4>.<ext>; anything else is rejected by /api/file.
STORED_FILE_RE = re.compile(r"^[0-9a-f]{32}\.[a-z0-9]{2,5}$")


def detect_platform(url: str) -> str:
    """Return the platform for a URL, or 'unknown'. Matches on hostname, not substrings."""
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return "unknown"
    for platform, domains in PLATFORM_DOMAINS.items():
        if any(host == d or host.endswith("." + d) for d in domains):
            return platform
    return "unknown"


def is_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.hostname)


def clean_filename(title: str, max_len: int = 100) -> str:
    """Make a title safe for use as a download filename."""
    cleaned = re.sub(r'[\\/*?:"<>|\x00-\x1f]', "", title or "")
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._")
    return cleaned[:max_len] or "download"


def build_ydl_format(fmt: str, resolution: str) -> dict:
    """Translate (format, resolution) into yt-dlp options.

    Resolution is a *ceiling* (height<=N) so a video that tops out below the
    requested size still downloads instead of failing.
    """
    opts: dict = {}
    if fmt in AUDIO_FORMATS:
        opts["format"] = "bestaudio/best"
        pp = {"key": "FFmpegExtractAudio", "preferredcodec": fmt}
        if fmt in ("mp3", "m4a"):  # bitrate is meaningless for lossless wav/flac
            pp["preferredquality"] = "192"
        opts["postprocessors"] = [pp]
        return opts

    h = f"[height<={resolution}]" if resolution in RESOLUTIONS else ""
    if fmt == "mp4":
        # H.264 + AAC where available so the file plays in QuickTime
        opts["format"] = (
            f"bestvideo[ext=mp4][vcodec^=avc]{h}+bestaudio[ext=m4a]"
            f"/best[ext=mp4]{h}/bestvideo{h}+bestaudio/best{h}"
        )
        opts["merge_output_format"] = "mp4"
    elif fmt == "webm":
        opts["format"] = f"bestvideo[ext=webm]{h}+bestaudio[ext=webm]/best[ext=webm]{h}/best{h}"
        opts["merge_output_format"] = "webm"
    elif fmt == "mkv":
        opts["format"] = f"bestvideo{h}+bestaudio/best{h}"
        opts["merge_output_format"] = "mkv"
    elif fmt == "avi":
        opts["format"] = f"bestvideo{h}+bestaudio/best{h}"
        opts["postprocessors"] = [{"key": "FFmpegVideoConvertor", "preferedformat": "avi"}]
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    return opts


def media_type_for(filename: str) -> Optional[str]:
    return {
        "mp4": "video/mp4", "webm": "video/webm", "mkv": "video/x-matroska",
        "avi": "video/x-msvideo", "mp3": "audio/mpeg", "m4a": "audio/mp4",
        "wav": "audio/wav", "flac": "audio/flac",
    }.get(filename.rsplit(".", 1)[-1].lower())
