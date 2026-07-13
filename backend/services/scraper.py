"""爬取编排器：先 yt-dlp，失败则通用爬取"""
from __future__ import annotations
import asyncio
from urllib.parse import urlparse

from schemas import ScrapeResponse, VideoFormat, VideoInfo
from services.ytdlp_scraper import scrape_with_ytdlp
from services.generic_scraper import scrape_generic

DIRECT_MEDIA_EXTS = {".mp4", ".webm", ".mkv", ".mov", ".avi", ".flv", ".m3u8", ".mpd", ".ts"}


def _is_direct_media(url: str) -> bool:
    """检查是否为直接媒体文件 URL"""
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in DIRECT_MEDIA_EXTS)


async def scrape_url(url: str) -> ScrapeResponse:
    """爬取 URL，返回统一的 ScrapeResponse"""
    # 直接媒体 URL 跳过 yt-dlp
    if _is_direct_media(url):
        return ScrapeResponse(
            source_url=url,
            platform="generic",
            page_title=None,
            videos=[_build_direct_media_video(url)],
            error=None,
        )

    # 1. 先尝试 yt-dlp（同步调用，但 yt-dlp 内部有网络请求）
    yt_videos, yt_error = await asyncio.to_thread(scrape_with_ytdlp, url)

    if yt_videos:
        return ScrapeResponse(
            source_url=url,
            platform=_detect_platform(url, yt_videos),
            page_title=yt_videos[0].title if yt_videos else None,
            videos=yt_videos,
        )

    # 2. yt-dlp 失败，回退到通用爬取
    gen_videos, gen_error = await scrape_generic(url)
    error = gen_error if not gen_videos else None
    if not gen_videos and yt_error:
        error = f"{yt_error}；通用网页解析也未找到视频"

    return ScrapeResponse(
        source_url=url,
        platform="generic",
        page_title=None,
        videos=gen_videos,
        error=error,
    )


def _detect_platform(url: str, videos: list[VideoInfo]) -> str:
    """根据 URL 判断平台"""
    domain_map = {
        "bilibili.com": "bilibili",
        "youtube.com": "youtube",
        "youtu.be": "youtube",
        "douyin.com": "douyin",
        "tiktok.com": "tiktok",
        "vimeo.com": "vimeo",
        "dailymotion.com": "dailymotion",
        "twitter.com": "twitter",
        "x.com": "twitter",
        "instagram.com": "instagram",
        "weibo.com": "weibo",
    }
    for domain, platform in domain_map.items():
        if domain in url:
            return platform
    return "generic"


def _build_direct_media_video(url: str) -> VideoInfo:
    """为直接媒体文件 URL 构建一个无需页面解析的下载项"""
    parsed = urlparse(url)
    filename = parsed.path.rsplit("/", 1)[-1] or "video"
    title = filename.rsplit(".", 1)[0] or "video"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "mp4"
    if ext not in {e.lstrip(".") for e in DIRECT_MEDIA_EXTS}:
        ext = "mp4"

    return VideoInfo(
        id=url,
        title=title,
        webpage_url=url,
        formats=[
            VideoFormat(
                format_id="direct",
                ext=ext,
                is_direct_url=True,
                url=url,
            )
        ],
    )
