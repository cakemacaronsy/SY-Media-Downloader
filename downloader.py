from src.core.downloader import Downloader

if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else None
    if url:
        dl = Downloader()
        dl.download(url)
    else:
        print("Usage: python downloader.py <URL>")
