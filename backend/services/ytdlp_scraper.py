"""yt-dlp 视频信息提取器"""
from __future__ import annotations
import yt_dlp
from yt_dlp.utils import DownloadError, UnsupportedError

from schemas import VideoInfo, VideoFormat


def extract_formats(info: dict) -> list[VideoFormat]:
    """将 yt-dlp 返回的格式列表转为我们的 VideoFormat 模型"""
    formats: list[VideoFormat] = []

    # 只取视频格式（排除纯音频）
    for fmt in info.get("formats", []):
        vcodec = fmt.get("vcodec", "none")
        acodec = fmt.get("acodec", "none")

        has_video = (vcodec and vcodec != "none") or not acodec or acodec == "none"
        has_audio = (acodec and acodec != "none") or not vcodec or vcodec == "none"

        # 跳过纯音频和纯视频无音频的格式（除非是唯一的）
        if not has_video and has_audio:
            continue

        format_id = fmt.get("format_id", "")
        resolution = fmt.get("resolution") or fmt.get("format_note")
        ext = fmt.get("ext", "")

        filesize_raw = fmt.get("filesize") or fmt.get("filesize_approx")
        filesize = int(filesize_raw) if filesize_raw else None

        formats.append(VideoFormat(
            format_id=format_id,
            ext=ext,
            resolution=resolution,
            filesize=filesize,
            format_note=fmt.get("format_note"),
            vcodec=vcodec if vcodec != "none" else None,
            acodec=acodec if acodec != "none" else None,
            has_audio=has_audio,
            has_video=has_video,
        ))

    # 去重（按 resolution + ext）
    seen = set()
    unique: list[VideoFormat] = []
    for f in formats:
        key = (f.resolution, f.ext, f.filesize)
        if key not in seen:
            seen.add(key)
            unique.append(f)

    # 按分辨率从高到低排序
    def sort_key(f: VideoFormat) -> int:
        if not f.resolution:
            return 0
        try:
            return int(f.resolution.replace("p", "").replace("i", ""))
        except ValueError:
            return 0

    unique.sort(key=sort_key, reverse=True)
    return unique


def scrape_with_ytdlp(url: str) -> tuple[list[VideoInfo], str | None]:
    """使用 yt-dlp 提取视频信息，返回 (videos, error)"""
    import config
    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "youtube_include_dash_manifest": False,
    }
    
    # 动态融入 Cookie 设定
    opts.update(config.get_ytdlp_cookie_options())

    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except UnsupportedError:
            return [], None
        except DownloadError as e:
            return [], str(e)
        except Exception as e:
            return [], f"yt-dlp 解析失败: {e}"

    if info is None:
        return [], "无法获取页面信息"

    # 判断是否为播放列表
    entries = info.get("entries")
    if entries:
        # 播放列表：取所有视频
        video_infos = []
        for i, entry in enumerate(entries):
            if entry is None:
                continue
            vi = _build_video_info(entry, i)
            if vi:
                video_infos.append(vi)
        return video_infos, None

    # 单个视频
    vi = _build_video_info(info, 0)
    if vi:
        return [vi], None
    return [], "未能解析出视频信息"


def _build_video_info(info: dict, index: int) -> VideoInfo | None:
    """从 yt-dlp info dict 构建 VideoInfo"""
    video_id = info.get("id") or info.get("display_id") or str(index)
    title = info.get("title") or info.get("fulltitle") or f"视频 {index + 1}"
    thumbnail = info.get("thumbnail")
    duration = info.get("duration")
    webpage_url = info.get("webpage_url", "")

    formats = extract_formats(info)

    # 如果没有离散格式，但有直接 URL，创建一个默认格式
    if not formats:
        direct_url = info.get("url")
        ext = info.get("ext", "mp4")
        if direct_url:
            formats.append(VideoFormat(
                format_id="direct",
                ext=ext,
                resolution=info.get("resolution"),
                filesize=info.get("filesize"),
                format_note=info.get("format_note"),
                has_audio=True,
                has_video=True,
                is_direct_url=True,
                url=direct_url,
            ))

    if not formats:
        return None

    return VideoInfo(
        id=video_id,
        title=title,
        thumbnail=thumbnail,
        duration=duration,
        webpage_url=webpage_url,
        formats=formats,
    )
