"""视频爬取后端配置"""
import os

BACKEND_PORT = int(os.getenv("VIDEO_SCRAPER_PORT", "8712"))
DOWNLOAD_DIR = os.path.expanduser(os.getenv("DOWNLOAD_DIR", "~/Downloads/VideoScraper"))
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
