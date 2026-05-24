"""异步下载管理器 — 队列、并发控制、进度追踪"""
from __future__ import annotations
import asyncio
import os
import uuid
import time
from pathlib import Path

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
            title=self.title,
            status=self.status,
            progress=self.progress,
            speed=self.speed,
            eta=self.eta,
            downloaded_bytes=downloaded,
            total_bytes=total,
            file_path=self.file_path,
            error=self.error,
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
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                if self._queue.empty() and self._running:
                    continue
                else:
                    break

            async with self._semaphore:
                if task._cancel_event.is_set():
                    continue
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
                task.error = str(e)

    async def _download_direct(self, task: DownloadTask):
        url = task.item.url
        if not url:
            raise ValueError("无下载地址")

        ext = url.split("?")[0].split(".")[-1] if "." in url.split("?")[0] else "mp4"
        if len(ext) > 5:
            ext = "mp4"
        safe_title = _safe_filename(task.title)
        file_path = os.path.join(config.DOWNLOAD_DIR, f"{safe_title}.{ext}")
        # 避免重名
        file_path = _unique_path(file_path)
        task.file_path = file_path

        async with httpx.AsyncClient(timeout=3600, headers=HEADERS, follow_redirects=True) as client:
            async with client.stream("GET", url) as resp:
                total = int(resp.headers.get("content-length", 0)) or None
                task.total_bytes = total

                with open(file_path, "wb") as f:
                    downloaded = 0
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 256):
                        if task._cancel_event.is_set():
                            f.close()
                            os.remove(file_path)
                            return
                        f.write(chunk)
                        downloaded += len(chunk)
                        task.downloaded_bytes = downloaded
                        self._calc_progress(task)

        task.status = "completed"
        task.progress = 100

    async def _download_ytdlp(self, task: DownloadTask):
        safe_title = _safe_filename(task.title)
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
        }

        # 动态融入 Cookie 设定
        opts.update(config.get_ytdlp_cookie_options())

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
    return cleaned[:120].strip()


def _unique_path(path: str) -> str:
    """如果文件已存在，添加序号"""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"


# 全局单例
manager = DownloadManager()
