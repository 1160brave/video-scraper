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
        # 加载已有设置进行合并，防止覆盖未提交的键
        existing = load_settings()
        existing.update(settings)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# 加载保存的配置，设置默认值
_saved_settings = load_settings()
DOWNLOAD_DIR = _saved_settings.get("download_dir", os.path.expanduser("~/Downloads/VideoScraper"))
COOKIE_MODE = _saved_settings.get("cookie_mode", "none")  # none, browser, file, manual
COOKIE_BROWSER = _saved_settings.get("cookie_browser", "chrome")  # chrome, edge, firefox, safari, etc.
COOKIE_MANUAL = _saved_settings.get("cookie_manual", "")  # 手动输入 Cookie 文本
COOKIE_FILE = _saved_settings.get("cookie_file", "")  # Netscape cookies 文件路径

# 用于存储 pywebview 窗口实例以支持原生对话框
active_window = None

def get_ytdlp_cookie_options() -> dict:
    """根据当前配置动态生成 yt-dlp 的 Cookie 选项"""
    opts = {}
    if COOKIE_MODE == "browser":
        if COOKIE_BROWSER:
            opts["cookiesfrombrowser"] = (COOKIE_BROWSER,)
    elif COOKIE_MODE == "file":
        if COOKIE_FILE and os.path.exists(COOKIE_FILE):
            opts["cookiefile"] = COOKIE_FILE
    elif COOKIE_MODE == "manual":
        if COOKIE_MANUAL and COOKIE_MANUAL.strip():
            # 传请求头 Cookie
            opts["http_headers"] = {
                "Cookie": COOKIE_MANUAL.strip()
            }
    return opts


