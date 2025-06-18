# Utility functions for downloader project

def ensure_dir_exists(path):
    import os
    if not os.path.exists(path):
        os.makedirs(path)
