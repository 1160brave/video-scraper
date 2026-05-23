"""通用网页视频解析器 — httpx + BeautifulSoup"""
from __future__ import annotations
import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from schemas import VideoInfo, VideoFormat
from config import REQUEST_TIMEOUT

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

VIDEO_EXTENSIONS = {".mp4", ".webm", ".mkv", ".mov", ".avi", ".flv", ".ts"}
STREAM_EXTENSIONS = {".m3u8", ".mpd"}


async def scrape_generic(url: str) -> tuple[list[VideoInfo], str | None]:
    """通用网页爬取：找 <video> 标签和视频链接"""
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers=HEADERS,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            html = resp.text
            final_url = str(resp.url)
    except httpx.TimeoutException:
        return [], "请求超时"
    except Exception as e:
        return [], f"请求失败: {e}"

    soup = BeautifulSoup(html, "lxml")
    videos: list[VideoInfo] = []
    seen_urls: set[str] = set()

    # 1. 从 <video> 标签提取
    for i, video_tag in enumerate(soup.find_all("video")):
        video_urls: list[str] = []

        # video 标签自身的 src
        src = video_tag.get("src")
        if src:
            video_urls.append(urljoin(final_url, str(src)))

        # <source> 子标签
        for source in video_tag.find_all("source"):
            src_attr = source.get("src") or source.get("data-src")
            if src_attr:
                video_urls.append(urljoin(final_url, str(src_attr)))

        poster = video_tag.get("poster", "")
        thumbnail = urljoin(final_url, poster) if poster else None

        for vurl in video_urls:
            if vurl in seen_urls:
                continue
            seen_urls.add(vurl)
            vi = _build_video_from_url(vurl, f"video_{i}", f"视频 {len(videos) + 1}", thumbnail)
            if vi:
                videos.append(vi)

    # 2. 从 <a> 和其他标签的 href 中找视频链接
    for tag in soup.find_all(["a", "source", "link"]):
        href = tag.get("href") or tag.get("src") or tag.get("data-src")
        if not href:
            continue
        full_url = urljoin(final_url, str(href))
        if full_url in seen_urls:
            continue

        parsed = urlparse(full_url)
        path_lower = parsed.path.lower()

        is_video = any(path_lower.endswith(ext) for ext in VIDEO_EXTENSIONS | STREAM_EXTENSIONS)
        if not is_video:
            continue

        seen_urls.add(full_url)
        title = tag.get("title") or tag.get("alt") or _extract_nearby_text(tag) or f"视频 {len(videos) + 1}"
        vi = _build_video_from_url(full_url, f"link_{len(videos)}", title)
        if vi:
            videos.append(vi)

    # 3. 从页面文本中查找视频 URL（正则匹配）
    video_url_pattern = re.compile(
        r'https?://[^\s"\'<>]+\.(?:mp4|webm|mkv|mov|m3u8|mpd)(?:\?[^\s"\'<>]*)?',
        re.IGNORECASE,
    )
    text = soup.get_text()
    # 也搜 script 和 style 之外的内容
    for script in soup.find_all(["script", "style"]):
        script.decompose()
    body_text = soup.get_text()

    for match in video_url_pattern.finditer(body_text):
        vurl = match.group(0)
        if vurl in seen_urls:
            continue
        seen_urls.add(vurl)
        vi = _build_video_from_url(vurl, f"text_{len(videos)}", f"视频 {len(videos) + 1}")
        if vi:
            videos.append(vi)

    if not videos:
        return [], "页面中未找到视频"

    return videos, None


async def _check_content_info(url: str) -> tuple[int | None, str | None]:
    """发送 HEAD 请求获取文件大小和 content-type"""
    try:
        async with httpx.AsyncClient(timeout=10, headers=HEADERS) as client:
            resp = await client.head(url, follow_redirects=True)
            content_length = resp.headers.get("content-length")
            content_type = resp.headers.get("content-type", "")
            size = int(content_length) if content_length else None
            return size, content_type
    except Exception:
        return None, None


def _build_video_from_url(
    vurl: str,
    video_id: str,
    title: str,
    thumbnail: str | None = None,
) -> VideoInfo | None:
    """从视频 URL 构建 VideoInfo（同步部分）"""
    parsed = urlparse(vurl)
    path = parsed.path.lower()

    ext = "mp4"
    for e in VIDEO_EXTENSIONS:
        if path.endswith(e):
            ext = e.lstrip(".")
            break
    for e in STREAM_EXTENSIONS:
        if path.endswith(e):
            ext = e.lstrip(".")
            break

    fmt = VideoFormat(
        format_id="direct",
        ext=ext,
        is_direct_url=True,
        url=vurl,
    )

    return VideoInfo(
        id=video_id,
        title=title,
        thumbnail=thumbnail,
        webpage_url=vurl,
        formats=[fmt],
    )


def _extract_nearby_text(tag) -> str | None:
    """从标签附近提取文本作为视频标题"""
    text = tag.get_text(strip=True)
    if text and len(text) < 100:
        return text
    parent = tag.parent
    if parent:
        text = parent.get_text(strip=True)
        if text and len(text) < 100:
            return text
    return None
