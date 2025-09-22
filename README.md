# Media Downloader

A powerful media downloader with graphical interface for downloading videos, audio, and images from YouTube, Facebook, Instagram, TikTok, Pinterest, and other platformz.

## 📋 Table of Contents

- [Features](#features)
- [Supported Platforms](#supported-platforms)
- [Installation](#installation)
- [Usage](#usage)
- [GUI Interface](#gui-interface)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **Multi-Platform Support**: Download from YouTube, Facebook, Instagram, TikTok, Pinterest, and more
- **Multiple Format Options**: 
  - Video: MP4, AVI, MKV, WEBM
  - Audio: MP3, M4A, WAV, FLAC
  - Images: JPG, PNG, GIF, WEBP
- **Quality Selection**: Choose from available quality options (144p to 4K)
- **Batch Download**: Download multiple files simultaneously
- **Playlist Support**: Download entire YouTube playlists
- **Subtitle Download**: Extract subtitles when available
- **Thumbnail Extraction**: Save video thumbnails
- **Progress Tracking**: Real-time download progress
- **Download History**: Keep track of downloaded files
- **Dark/Light Theme**: User-friendly interface themes

## 🌐 Supported Platforms

| Platform | Video | Audio | Images | Playlists |
|----------|-------|-------|---------|-----------|
| YouTube | ✅ | ✅ | ✅ | ✅ |
| Facebook | ✅ | ✅ | ✅ | ❌ |
| Instagram | ✅ | ✅ | ✅ | ❌ |
| TikTok | ✅ | ✅ | ❌ | ❌ |
| Pinterest | ❌ | ❌ | ✅ | ✅ |
| Twitter/X | ✅ | ✅ | ✅ | ❌ |
| Reddit | ✅ | ✅ | ✅ | ❌ |
| Vimeo | ✅ | ✅ | ✅ | ❌ |

## 📥 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- FFmpeg (for video/audio conversion)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/media-downloader.git
cd media-downloader
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install FFmpeg

#### Windows
1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to PATH

#### macOS
```bash
brew install ffmpeg
```

#### Linux
```bash
sudo apt update
sudo apt install ffmpeg
```

## 🚀 Usage

### Command Line Interface

```bash
# Basic usage
python downloader.py <URL>

# Specify format
python downloader.py <URL> --format mp4

# Specify quality
python downloader.py <URL> --quality 720p

# Audio only
python downloader.py <URL> --audio-only

# Download playlist
python downloader.py <PLAYLIST_URL> --playlist

# Batch download from file
python downloader.py --batch urls.txt
```

### Graphical User Interface

```bash
python gui.py
```

## 🖥️ GUI Interface

### Main Window Components

1. **URL Input Field**: Paste media URLs
2. **Platform Detector**: Auto-detects the platform
3. **Format Selector**: Choose output format
4. **Quality Selector**: Select video quality
5. **Download Location**: Choose save directory
6. **Download Button**: Start download
7. **Progress Bar**: Track download progress
8. **Download Queue**: Manage multiple downloads

### Settings Panel

- **General Settings**
  - Default download location
  - Maximum concurrent downloads
  - Auto-start downloads
  - Check for updates

- **Video Settings**
  - Default video format
  - Default quality
  - Subtitle preferences
  - Thumbnail download

- **Audio Settings**
  - Default audio format
  - Bitrate preferences
  - Metadata embedding

- **Advanced Settings**
  - Proxy configuration
  - Rate limiting
  - Cookie management
  - User agent

## 📚 API Documentation

### Core Classes

#### `Downloader`
Main class for handling downloads.

```python
from downloader import Downloader

dl = Downloader()
dl.download(url, format='mp4', quality='720p')
```

#### `PlatformDetector`
Detects and validates URLs.

```python
from detector import PlatformDetector

detector = PlatformDetector()
platform = detector.detect(url)
```

#### `FormatConverter`
Handles format conversion.

```python
from converter import FormatConverter

converter = FormatConverter()
converter.convert(input_file, output_format)
```

### Example Usage

```python
import asyncio
from downloader import MediaDownloader

async def main():
    downloader = MediaDownloader()
    
    # Download single video
    await downloader.download_video(
        url="https://youtube.com/watch?v=...",
        format="mp4",
        quality="1080p",
        output_path="./downloads"
    )
    
    # Download audio only
    await downloader.download_audio(
        url="https://youtube.com/watch?v=...",
        format="mp3",
        bitrate="320k"
    )
    
    # Download playlist
    await downloader.download_playlist(
        url="https://youtube.com/playlist?list=...",
        format="mp4",
        quality="best"
    )

asyncio.run(main())
```

## ⚙️ Configuration

### config.json

```json
{
  "general": {
    "download_path": "./downloads",
    "max_concurrent": 3,
    "auto_start": true,
    "check_updates": true
  },
  "video": {
    "default_format": "mp4",
    "default_quality": "1080p",
    "download_subtitles": true,
    "download_thumbnail": true,
    "merge_format": true
  },
  "audio": {
    "default_format": "mp3",
    "default_bitrate": "320k",
    "embed_metadata": true,
    "extract_audio": true
  },
  "network": {
    "proxy": null,
    "rate_limit": "10M",
    "retry_attempts": 3,
    "timeout": 30
  },
  "platforms": {
    "youtube": {
      "use_cookies": false,
      "age_limit": null
    },
    "instagram": {
      "username": null,
      "password": null
    }
  }
}
```

## 🛠️ Development

### Project Structure

```
media-downloader/
├── src/
│   ├── core/
│   │   ├── downloader.py
│   │   ├── detector.py
│   │   ├── converter.py
│   │   └── utils.py
│   ├── platforms/
│   │   ├── youtube.py
│   │   ├── facebook.py
│   │   ├── instagram.py
│   │   ├── tiktok.py
│   │   └── pinterest.py
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── settings.py
│   │   ├── widgets/
│   │   └── themes/
│   └── config/
│       ├── settings.py
│       └── constants.py
├── tests/
├── docs/
├── requirements.txt
├── setup.py
├── README.md
└── LICENSE
```

### Requirements.txt

```txt
# Core dependencies
yt-dlp>=2024.1.0
pytube>=15.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# GUI dependencies
PyQt6>=6.6.0
# or
tkinter>=8.6
customtkinter>=5.2.0

# Media processing
ffmpeg-python>=0.2.0
Pillow>=10.2.0
mutagen>=1.47.0

# Async support
aiohttp>=3.9.0
asyncio>=3.4.3

# Utils
python-dotenv>=1.0.0
colorama>=0.4.6
tqdm>=4.66.0
validators>=0.22.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.23.0
pytest-cov>=4.1.0
```

### Building Executable

#### Windows
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico gui.py
```

#### macOS
```bash
pip install py2app
python setup.py py2app
```

#### Linux
```bash
pip install pyinstaller
pyinstaller --onefile --windowed gui.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Coding Standards

- Follow PEP 8
- Add docstrings to all functions
- Write unit tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Users are responsible for complying with applicable laws and respecting copyright. Always ensure you have permission to download content.

## 🐛 Known Issues

- Instagram may require login for some content
- TikTok watermark removal is limited
- Some Facebook videos require authentication
- Rate limiting on certain platforms

## 📮 Support

- Create an [Issue](https://github.com/yourusername/media-downloader/issues)
- Join our [Discord](https://discord.gg/yourdiscord)
- Email: support@yourdomain.com

## 🔄 Changelog

### v1.0.0 (2024-01-01)
- Initial release
- Basic YouTube download support
- Simple GUI interface

### v1.1.0 (2024-02-01)
- Added Facebook, Instagram support
- Playlist download feature
- Improved GUI with themes

### v1.2.0 (2024-03-01)
- Added TikTok, Pinterest support
- Batch download feature
- Settings persistence

---

Made with ❤️ by [Your Name]
