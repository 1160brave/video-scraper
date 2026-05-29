"""通用网页视频解析器 — httpx + BeautifulSoup"""
from __future__ import annotations
import html as html_lib
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
    source_urls: set[str] = set()

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
            vurl = _normalize_media_url(vurl)
            if vurl in seen_urls:
                continue
            seen_urls.add(vurl)
            vi = _build_video_from_url(vurl, f"video_{i}", f"视频 {len(videos) + 1}", thumbnail, webpage_url=final_url)
            if vi:
                videos.append(vi)

    # 2. 从 <a> 和其他标签的 href 中找视频链接
    for tag in soup.find_all(["a", "source", "link"]):
        href = tag.get("href") or tag.get("src") or tag.get("data-src")
        if not href:
            continue
        full_url = _normalize_media_url(urljoin(final_url, str(href)))
        if full_url in seen_urls:
            continue

        parsed = urlparse(full_url)
        path_lower = parsed.path.lower()

        is_video = any(path_lower.endswith(ext) for ext in VIDEO_EXTENSIONS | STREAM_EXTENSIONS)
        if not is_video:
            continue

        seen_urls.add(full_url)
        title = tag.get("title") or tag.get("alt") or _extract_nearby_text(tag) or f"视频 {len(videos) + 1}"
        vi = _build_video_from_url(full_url, f"link_{len(videos)}", title, webpage_url=final_url)
        if vi:
            videos.append(vi)

    # 3. 从源码中查找视频 URL（包含 script 中的播放器配置）
    video_url_pattern = re.compile(
        r'https?://[^\s"\'<>]+\.(?:mp4|webm|mkv|mov|m3u8|mpd)(?:\?[^\s"\'<>]*)?',
        re.IGNORECASE,
    )

    for match in video_url_pattern.finditer(html):
        vurl = _normalize_media_url(match.group(0))
        if vurl in seen_urls:
            continue
        seen_urls.add(vurl)
        source_urls.add(vurl)

    videos.extend(_build_videos_from_urls(list(source_urls), final_url, len(videos)))

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
    webpage_url: str | None = None,
    filesize: int | None = None,
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
        resolution=_format_resolution_label(vurl),
        filesize=filesize,
        format_note=_format_resolution_label(vurl),
        is_direct_url=True,
        url=vurl,
    )

    return VideoInfo(
        id=video_id,
        title=title,
        thumbnail=thumbnail,
        webpage_url=webpage_url or vurl,
        formats=[fmt],
    )


def _build_videos_from_urls(urls: list[str], source_url: str, start_index: int = 0) -> list[VideoInfo]:
    """把同一微信 mpvideo 的不同清晰度地址合并成一个视频的多个格式"""
    mpvideo_groups: dict[str, list[str]] = {}
    standalone: list[str] = []

    for url in urls:
        key = _mpvideo_group_key(url)
        if key:
            mpvideo_groups.setdefault(key, []).append(url)
        else:
            standalone.append(url)

    videos: list[VideoInfo] = []
    for urls_in_group in mpvideo_groups.values():
        formats = []
        for url in sorted(urls_in_group, key=_mpvideo_quality_rank):
            size, _ = _sync_content_info(url, source_url)
            label = _format_resolution_label(url)
            formats.append(VideoFormat(
                format_id=url,
                ext="mp4",
                resolution=label,
                filesize=size,
                format_note=label,
                has_audio=True,
                has_video=True,
                is_direct_url=True,
                url=url,
            ))
        title = f"视频 {start_index + len(videos) + 1}"
        videos.append(VideoInfo(
            id=_mpvideo_group_key(urls_in_group[0]) or urls_in_group[0],
            title=title,
            webpage_url=source_url,
            formats=formats,
        ))

    for url in standalone:
        if any(url in group for group in mpvideo_groups.values()):
            continue
        size, _ = _sync_content_info(url, source_url)
        vi = _build_video_from_url(
            url,
            f"text_{start_index + len(videos)}",
            f"视频 {start_index + len(videos) + 1}",
            webpage_url=source_url,
            filesize=size,
        )
        if vi:
            videos.append(vi)

    return videos


def _normalize_media_url(url: str) -> str:
    return html_lib.unescape(url.replace("\\x26amp;", "&").replace("\\u0026", "&"))


def _mpvideo_group_key(url: str) -> str | None:
    parsed = urlparse(url)
    if "mpvideo.qpic.cn" not in parsed.netloc:
        return None
    filename = parsed.path.rsplit("/", 1)[-1]
    return filename.split(".f", 1)[0] if ".f" in filename else filename


def _mpvideo_quality_rank(url: str) -> int:
    match = re.search(r"\.f(\d+)\.mp4", urlparse(url).path)
    if not match:
        return 999999
    # 微信 mpvideo 常见 f10002 文件最大、清晰度最高；按编号升序排列。
    return int(match.group(1))


def _format_resolution_label(url: str) -> str | None:
    match = re.search(r"\.f(\d+)\.mp4", urlparse(url).path)
    if match:
        return f"f{match.group(1)}"
    return None


def _sync_content_info(url: str, referer: str | None = None) -> tuple[int | None, str | None]:
    headers = dict(HEADERS)
    if referer:
        headers["Referer"] = referer
    try:
        with httpx.Client(timeout=10, headers=headers, follow_redirects=True) as client:
            resp = client.head(url)
            resp.raise_for_status()
            content_length = resp.headers.get("content-length")
            content_type = resp.headers.get("content-type", "")
            size = int(content_length) if content_length else None
            return size, content_type
    except Exception:
        return None, None


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
