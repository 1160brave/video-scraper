"""Pydantic 请求/响应数据模型"""
from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    url: str


class VideoFormat(BaseModel):
    format_id: str
    ext: str = ""
    resolution: str | None = None
    filesize: int | None = None
    format_note: str | None = None
    vcodec: str | None = None
    acodec: str | None = None
    has_audio: bool = True
    has_video: bool = True
    is_direct_url: bool = False
    url: str | None = None


class VideoInfo(BaseModel):
    id: str
    title: str
    thumbnail: str | None = None
    duration: float | None = None
    webpage_url: str = ""
    formats: list[VideoFormat] = []


class ScrapeResponse(BaseModel):
    source_url: str
    platform: str = "generic"
    page_title: str | None = None
    videos: list[VideoInfo] = []
    error: str | None = None


class DownloadItem(BaseModel):
    video_id: str
    format_id: str
    title: str
    url: str | None = None
    thumbnail: str | None = None
    webpage_url: str = ""


class DownloadRequest(BaseModel):
    downloads: list[DownloadItem]


class TaskInfo(BaseModel):
    task_id: str
    video_id: str
    title: str
    status: str = "queued"
    progress: float = 0
    speed: str | None = None
    eta: str | None = None
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    file_path: str | None = None
    error: str | None = None
