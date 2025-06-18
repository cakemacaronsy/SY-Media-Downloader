class PlatformDetector:
    """Detects and validates URLs."""
    def __init__(self):
        pass

    def detect(self, url):
        if "youtube.com" in url:
            return "YouTube"
        elif "facebook.com" in url:
            return "Facebook"
        elif "instagram.com" in url:
            return "Instagram"
        elif "tiktok.com" in url:
            return "TikTok"
        elif "pinterest.com" in url:
            return "Pinterest"
        elif "twitter.com" in url or "x.com" in url:
            return "Twitter/X"
        elif "reddit.com" in url:
            return "Reddit"
        elif "vimeo.com" in url:
            return "Vimeo"
        else:
            return "Unknown"
