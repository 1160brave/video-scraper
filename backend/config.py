"""视频爬取后端配置"""
import os
import json

BACKEND_PORT = int(os.getenv("VIDEO_SCRAPER_PORT", "8712"))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

SETTINGS_FILE = os.path.expanduser("~/.video_scraper_settings.json")

def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# 加载保存的下载路径，默认为用户下载目录下的 VideoScraper 目录
_saved_settings = load_settings()
DOWNLOAD_DIR = _saved_settings.get("download_dir", os.path.expanduser("~/Downloads/VideoScraper"))

# 用于存储 pywebview 窗口实例以支持原生对话框
active_window = None

