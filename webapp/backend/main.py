from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import mimetypes
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import FileResponse, JSONResponse

import yt_dlp
import uuid
import re

app = FastAPI(title="SY Media Downloader API")

# Get allowed origins from environment variable for production
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

# Configure CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Use environment variable
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    url: str
    format: str
    resolution: str = 'best'

def detect_platform(url):
    """Detect which platform the URL belongs to"""
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'facebook.com' in url or 'fb.watch' in url:
        return 'facebook'
    elif 'instagram.com' in url:
        return 'instagram'
    elif 'tiktok.com' in url:
        return 'tiktok'
    elif 'twitter.com' in url or 'x.com' in url:
        return 'twitter'
    elif 'reddit.com' in url:
        return 'reddit'
    elif 'vimeo.com' in url:
        return 'vimeo'
    elif 'pinterest.com' in url:
        return 'pinterest'
    else:
        return 'generic'

def clean_filename(title):
    """Clean a string to make it suitable for a filename"""
    # Remove invalid characters
    cleaned = re.sub(r'[\\/*?:"<>|]', '', title)
    # Replace spaces with underscores
    cleaned = re.sub(r'\s+', '_', cleaned)
    # Limit length
    if len(cleaned) > 100:
        cleaned = cleaned[:100]
    return cleaned

@app.post("/api/download")
async def download_video(request: DownloadRequest):
    url = request.url
    fmt = request.format
    resolution = request.resolution
    
    # Detect which platform we're downloading from
    platform = detect_platform(url)
    
    # First extract info without downloading to get the title
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', 'video')
            clean_title = clean_filename(video_title)
    except Exception:
        # If we can't get the title, use a UUID as fallback
        clean_title = str(uuid.uuid4())
    
    output_template = os.path.join(DOWNLOAD_DIR, f"{clean_title}.%(ext)s")
    ydl_opts = {
        'outtmpl': output_template,
        'format': 'bestvideo+bestaudio/best' if fmt == 'mp4' else 'bestaudio/best',
        'merge_output_format': fmt,
        'quiet': True,
        'noplaylist': True,
        'postprocessors': [],
    }
    
    # Determine if this is an audio or video format
    audio_formats = ['mp3', 'm4a', 'wav', 'flac']
    video_formats = ['mp4', 'webm', 'mkv', 'avi']
    
    is_audio = fmt in audio_formats
    
    # Handle resolution for video formats
    if not is_audio and resolution != 'best':
        if resolution == '2160':
            res_filter = '[height>=2160]'
        elif resolution == '1440':
            res_filter = '[height>=1440][height<2160]'
        elif resolution == '1080':
            res_filter = '[height>=1080][height<1440]'
        elif resolution == '720':
            res_filter = '[height>=720][height<1080]'
        elif resolution == '480':
            res_filter = '[height>=480][height<720]'
        elif resolution == '360':
            res_filter = '[height>=360][height<480]'
        elif resolution == '240':
            res_filter = '[height>=240][height<360]'
        elif resolution == '144':
            res_filter = '[height>=144][height<240]'
        else:
            res_filter = ''
    else:
        res_filter = ''
    
    # Add format-specific options
    if is_audio:
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio',
            'preferredcodec': fmt,
            'preferredquality': '192',
        })
        
        # For WAV and FLAC, use higher quality
        if fmt in ['wav', 'flac']:
            ydl_opts['postprocessors'][-1]['preferredquality'] = '320'
            
    else:  # Video formats
        if fmt == 'mp4':
            # Ensure QuickTime compatibility with H.264 video and AAC audio
            if resolution != 'best':
                ydl_opts['format'] = f'bestvideo[ext=mp4][vcodec^=avc]{res_filter}+bestaudio[ext=m4a]/best[ext=mp4]/best'
            else:
                ydl_opts['format'] = 'bestvideo[ext=mp4][vcodec^=avc]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            # Add a postprocessor to ensure QuickTime compatibility
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            })
            # Force H.264 encoding for QuickTime compatibility
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegVideoRemuxer',
                'preferedformat': 'mp4',
            })
        elif fmt == 'webm':
            if resolution != 'best':
                ydl_opts['format'] = f'bestvideo[ext=webm]{res_filter}+bestaudio[ext=webm]/best[ext=webm]'
            else:
                ydl_opts['format'] = 'bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]'
        elif fmt == 'mkv':
            # MKV is a container that can hold any codec
            if resolution != 'best':
                ydl_opts['format'] = f'bestvideo{res_filter}+bestaudio/best'
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mkv'
        elif fmt == 'avi':
            # For QuickTime compatibility with AVI
            if resolution != 'best':
                ydl_opts['format'] = f'bestvideo{res_filter}+bestaudio/best'
            else:
                ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            ydl_opts['merge_output_format'] = 'avi'
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'avi',
            })
            
    # Add platform-specific options
    if platform == 'youtube':
        # YouTube-specific options
        pass  # Default options work well
    elif platform == 'facebook':
        # Facebook requires some special handling
        ydl_opts['cookiesfrombrowser'] = ('chrome',)
    elif platform == 'instagram':
        # Instagram requires cookies
        ydl_opts['cookiesfrombrowser'] = ('chrome',)
    elif platform == 'tiktok':
        # TikTok specific options
        pass
    elif platform == 'twitter':
        # Twitter/X specific options
        pass
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Get the actual filename from yt-dlp info
            if fmt == 'mp3' or fmt == 'm4a' or fmt == 'wav' or fmt == 'flac':
                ext = fmt
            else:
                ext = info.get('ext', fmt)
                
            filename = f"{clean_title}.{ext}"
            file_path = os.path.join(DOWNLOAD_DIR, filename)
            
            if not os.path.exists(file_path):
                # fallback: try to find the file with any extension
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(clean_title + "."):
                        file_path = os.path.join(DOWNLOAD_DIR, f)
                        filename = f
                        break
                        
            # Return the file path, title and platform for display
            return {
                "file": f"/api/file/{filename}",
                "title": video_title,
                "platform": platform
            }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/file/{filename}")
def get_file(filename: str):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    
    if not os.path.exists(file_path):
        return JSONResponse(
            status_code=404,
            content={"error": "File not found"}
        )
    
    # Get the correct content type based on file extension
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        # Video formats
        if filename.endswith('.mp4'):
            content_type = "video/mp4"
        elif filename.endswith('.webm'):
            content_type = "video/webm"
        elif filename.endswith('.mkv'):
            content_type = "video/x-matroska"
        elif filename.endswith('.avi'):
            content_type = "video/x-msvideo"
        # Audio formats
        elif filename.endswith('.mp3'):
            content_type = "audio/mpeg"
        elif filename.endswith('.m4a'):
            content_type = "audio/mp4"
        elif filename.endswith('.wav'):
            content_type = "audio/wav"
        elif filename.endswith('.flac'):
            content_type = "audio/flac"
        else:
            content_type = "application/octet-stream"
    
    # Return the file with the appropriate content type and as an attachment
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename
    )
