"""Pydantic 请求/响应数据模型"""
from pydantic import BaseModel, Field, field_validator


class ScrapeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value.startswith(("http://", "https://")):
            raise ValueError("请输入完整的 http(s) 视频链接")
        return value


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
    formats: list[VideoFormat] = Field(default_factory=list)


class ScrapeResponse(BaseModel):
    source_url: str
    platform: str = "generic"
    page_title: str | None = None
    videos: list[VideoInfo] = Field(default_factory=list)
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

    @field_validator("downloads")
    @classmethod
    def validate_downloads(cls, value: list[DownloadItem]) -> list[DownloadItem]:
        if not value:
            raise ValueError("下载列表为空")
        return value


class TaskInfo(BaseModel):
    task_id: str
    video_id: str
    format_id: str = ""
    title: str
    status: str = "queued"
    progress: float = 0
    speed: str | None = None
    eta: str | None = None
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    file_path: str | None = None
    error: str | None = None
    url: str | None = None
    thumbnail: str | None = None
    webpage_url: str = ""
