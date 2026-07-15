"""异步下载管理器 — 队列、并发控制、进度追踪"""
from __future__ import annotations
import asyncio
import os
import uuid
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import yt_dlp

from schemas import DownloadItem, TaskInfo
import config
from config import MAX_CONCURRENT_DOWNLOADS

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}


class DownloadTask:
    """单个下载任务"""
    def __init__(self, item: DownloadItem):
        self.task_id = uuid.uuid4().hex[:12]
        self.video_id = item.video_id
        self.title = item.title
        self.status = "queued"
        self.progress = 0.0
        self.speed: str | None = None
        self.eta: str | None = None
        self.downloaded_bytes = 0
        self.total_bytes: int | None = None
        self.file_path: str | None = None
        self.error: str | None = None
        self.item = item
        self._cancel_event = asyncio.Event()
        self._last_update_time = time.time()
        self._last_downloaded = 0

    def to_info(self) -> TaskInfo:
        total = int(self.total_bytes) if self.total_bytes else None
        downloaded = int(self.downloaded_bytes) if self.downloaded_bytes else 0
        return TaskInfo(
            task_id=self.task_id,
            video_id=self.video_id,
            format_id=self.item.format_id,
            title=self.title,
            status=self.status,
            progress=self.progress,
            speed=self.speed,
            eta=self.eta,
            downloaded_bytes=downloaded,
            total_bytes=total,
            file_path=self.file_path,
            error=self.error,
            url=self.item.url,
            thumbnail=self.item.thumbnail,
            webpage_url=self.item.webpage_url,
        )

    def cancel(self):
        self._cancel_event.set()
        self.status = "cancelled"


class DownloadManager:
    """异步下载管理器"""

    def __init__(self):
        self._tasks: dict[str, DownloadTask] = {}
        self._queue: asyncio.Queue[DownloadTask] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        self._running = False
        self._worker_task: asyncio.Task | None = None
        self._active_downloads: set[asyncio.Task] = set()

    def update_max_concurrent(self, limit: int):
        """动态更新最大并发下载数"""
        self._semaphore = asyncio.Semaphore(limit)

    async def add(self, item: DownloadItem) -> TaskInfo:
        task = DownloadTask(item)
        self._tasks[task.task_id] = task
        await self._queue.put(task)
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._process_queue())
        return task.to_info()

    async def add_batch(self, items: list[DownloadItem]) -> list[TaskInfo]:
        return [await self.add(item) for item in items]

    async def _process_queue(self):
        while self._running:
            task = await self._queue.get()
            worker = asyncio.create_task(self._execute_with_limit(task))
            self._active_downloads.add(worker)
            worker.add_done_callback(self._active_downloads.discard)
            self._queue.task_done()

    async def _execute_with_limit(self, task: DownloadTask):
        if task._cancel_event.is_set():
            return
        async with self._semaphore:
            if task._cancel_event.is_set():
                return
            await self._execute(task)

    async def _execute(self, task: DownloadTask):
        task.status = "downloading"
        try:
            if task.item.url:
                await self._download_direct(task)
            else:
                await self._download_ytdlp(task)
        except asyncio.CancelledError:
            task.status = "cancelled"
        except Exception as e:
            if task._cancel_event.is_set():
                task.status = "cancelled"
            else:
                task.status = "failed"
                task.error = _format_error(e)

    async def _download_direct(self, task: DownloadTask):
        url = task.item.url
        if not url:
            raise ValueError("无下载地址")

        ext = url.split("?")[0].split(".")[-1] if "." in url.split("?")[0] else "mp4"
        if len(ext) > 5:
            ext = "mp4"
        safe_title = _safe_filename(task.title)
        os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
        file_path = os.path.join(config.DOWNLOAD_DIR, f"{safe_title}.{ext}")
        # 避免重名
        file_path = _unique_path(file_path)
        task.file_path = file_path

        headers = _download_headers(url, task.item.webpage_url)
        async with httpx.AsyncClient(timeout=3600, headers=headers, follow_redirects=True) as client:
            async with client.stream("GET", url) as resp:
                resp.raise_for_status()
                total = int(resp.headers.get("content-length", 0)) or None
                task.total_bytes = total

                with open(file_path, "wb") as f:
                    downloaded = 0
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                        if task._cancel_event.is_set():
                            f.close()
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            return
                        f.write(chunk)
                        downloaded += len(chunk)
                        task.downloaded_bytes = downloaded
                        self._calc_progress(task)

        task.status = "completed"
        task.progress = 100

    async def _download_ytdlp(self, task: DownloadTask):
        if _requires_ffmpeg_merge(task.item.format_id) and not config.check_ffmpeg():
            raise RuntimeError("当前选择的格式需要 FFmpeg 合并音视频，请先在设置页安装 FFmpeg，或选择仅视频/单文件格式")

        safe_title = _safe_filename(task.title)
        os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
        outtmpl = os.path.join(config.DOWNLOAD_DIR, f"{safe_title}.%(ext)s")

        def progress_hook(d: dict):
            if task._cancel_event.is_set():
                raise Exception("cancelled")

            status = d.get("status", "")
            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                downloaded = d.get("downloaded_bytes", 0)
                task.downloaded_bytes = int(downloaded) if downloaded else 0
                task.total_bytes = int(total) if total else None
                task.speed = d.get("_speed_str") or d.get("speed_str")

                if total and total > 0:
                    task.progress = (downloaded / total) * 100

                eta = d.get("eta")
                if eta is not None:
                    m, s = divmod(int(eta), 60)
                    task.eta = f"{m}:{s:02d}"

            elif status == "finished":
                task.progress = 100
                task.file_path = d.get("filename") or outtmpl

        opts = {
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "format": task.item.format_id,
            "paths": {"home": config.DOWNLOAD_DIR},
            "continuedl": True,
            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 5,
            "extractor_retries": 3,
            "socket_timeout": 30,
            "nocheckcertificate": True,
            "http_headers": HEADERS,
        }

        # 动态融入 Cookie 设定；手动 Cookie 只合并 Header，不覆盖 User-Agent。
        cookie_opts = config.get_ytdlp_cookie_options()
        if "http_headers" in cookie_opts:
            opts["http_headers"] = {**opts["http_headers"], **cookie_opts.pop("http_headers")}
        opts.update(cookie_opts)

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, lambda: self._run_ytdlp(opts, task))
        except Exception as e:
            if task._cancel_event.is_set():
                task.status = "cancelled"
                # 清理部分下载文件
                if task.file_path and os.path.exists(task.file_path):
                    os.remove(task.file_path)
                return
            if _is_cookie_error(e):
                retry_opts = _without_cookie_options(opts)
                await loop.run_in_executor(None, lambda: self._run_ytdlp(retry_opts, task))
            else:
                raise

        # 查找下载的文件
        if not task.file_path or not os.path.exists(task.file_path):
            # 搜索可能的输出文件
            for f in os.listdir(config.DOWNLOAD_DIR):
                if f.startswith(safe_title) and not f.endswith(".part") and not f.endswith(".ytdl"):
                    task.file_path = os.path.join(config.DOWNLOAD_DIR, f)
                    break

        task.status = "completed"
        task.progress = 100

    @staticmethod
    def _run_ytdlp(opts: dict, task: DownloadTask):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([task.item.webpage_url or task.item.video_id])
        except Exception:
            if task._cancel_event.is_set():
                return
            raise

    def _calc_progress(self, task: DownloadTask):
        now = time.time()
        elapsed = now - task._last_update_time
        if elapsed >= 0.5:
            if task.total_bytes:
                task.progress = (task.downloaded_bytes / task.total_bytes) * 100
            speed_bytes = task.downloaded_bytes - task._last_downloaded
            if elapsed > 0:
                speed = speed_bytes / elapsed
                if speed > 1_000_000:
                    task.speed = f"{speed / 1_000_000:.1f}MB/s"
                elif speed > 1_000:
                    task.speed = f"{speed / 1_000:.0f}KB/s"
                else:
                    task.speed = f"{speed:.0f}B/s"
            if task.total_bytes and task.total_bytes > 0:
                remaining = task.total_bytes - task.downloaded_bytes
                if speed_bytes > 0:
                    eta_sec = remaining / (speed_bytes / elapsed)
                    m, s = divmod(int(eta_sec), 60)
                    task.eta = f"{m}:{s:02d}"
            task._last_update_time = now
            task._last_downloaded = task.downloaded_bytes

    def get_all(self) -> list[TaskInfo]:
        return [t.to_info() for t in self._tasks.values()]

    def get(self, task_id: str) -> TaskInfo | None:
        t = self._tasks.get(task_id)
        return t.to_info() if t else None

    async def retry(self, task_id: str) -> TaskInfo | None:
        t = self._tasks.get(task_id)
        if not t or t.status not in ("failed", "cancelled"):
            return None
        return await self.add(t.item)

    def cancel(self, task_id: str) -> bool:
        t = self._tasks.get(task_id)
        if t and t.status in ("queued", "downloading"):
            t.cancel()
            return True
        return False


def _safe_filename(name: str) -> str:
    """清理文件名中的非法字符"""
    unsafe = r'[<>:"/\\|?*\x00-\x1f]'
    cleaned = __import__("re").sub(unsafe, "_", name)
    return cleaned[:120].strip() or "video"


def _unique_path(path: str) -> str:
    """如果文件已存在，添加序号"""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"


def _format_error(error: Exception) -> str:
    """将底层异常转成面向用户的短错误信息"""
    message = str(error).strip()
    if _is_cookie_error(error):
        return (
            "下载失败：当前设置选择的浏览器 Cookie 不可用。"
            "请在下载设置里改用已登录的 Chrome/Safari，导入 cookies.txt，或关闭 Cookie 后重试。"
        )
    if "UNEXPECTED_EOF_WHILE_READING" in message or "EOF occurred in violation of protocol" in message:
        return "下载失败：SSL 连接被服务器中途断开，请重试，程序会尝试断点续传"
    if isinstance(error, httpx.HTTPStatusError):
        return f"下载失败：服务器返回 HTTP {error.response.status_code}"
    if isinstance(error, httpx.RequestError):
        return f"下载失败：网络请求异常（{error.__class__.__name__}）"
    return message or error.__class__.__name__


def _download_headers(url: str, webpage_url: str | None) -> dict[str, str]:
    headers = dict(HEADERS)
    if webpage_url:
        source = urlparse(webpage_url)
        target = urlparse(url)
        if source.scheme and source.netloc and webpage_url != url:
            headers["Referer"] = webpage_url
        if target.netloc.endswith("qpic.cn") and source.netloc:
            headers["Origin"] = f"{source.scheme}://{source.netloc}"
    return headers


def _is_cookie_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        "cookies database" in message
        or ("could not find" in message and "cookies" in message)
        or ("cookie" in message and "not found" in message)
    )


def _without_cookie_options(opts: dict) -> dict:
    retry_opts = dict(opts)
    retry_opts.pop("cookiesfrombrowser", None)
    retry_opts.pop("cookiefile", None)
    headers = dict(retry_opts.get("http_headers") or {})
    headers.pop("Cookie", None)
    retry_opts["http_headers"] = headers
    return retry_opts


def _requires_ffmpeg_merge(format_id: str) -> bool:
    return "+" in format_id


# 全局单例
manager = DownloadManager()
