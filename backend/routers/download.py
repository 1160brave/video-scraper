"""下载 API — REST + SSE"""
import asyncio
import json

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from schemas import DownloadRequest, TaskInfo
from services.download_manager import manager

router = APIRouter()


@router.post("/api/download")
async def start_download(req: DownloadRequest) -> dict:
    """提交下载任务"""
    if not req.downloads:
        raise HTTPException(status_code=400, detail="下载列表为空")
    tasks = await manager.add_batch(list(req.downloads))
    return {"tasks": [t.model_dump() for t in tasks]}


@router.get("/api/tasks")
async def get_tasks() -> list[TaskInfo]:
    """获取所有下载任务"""
    return manager.get_all()


@router.get("/api/tasks/stream")
async def stream_tasks():
    """SSE 实时推送下载进度"""
    async def generate():
        while True:
            tasks = manager.get_all()
            yield {
                "event": "message",
                "data": json.dumps([t.model_dump() for t in tasks], ensure_ascii=False),
            }
            await asyncio.sleep(0.5)

    return EventSourceResponse(generate())


@router.delete("/api/tasks/{task_id}")
async def cancel_task(task_id: str):
    """取消下载"""
    if manager.cancel(task_id):
        return {"status": "cancelled"}
    raise HTTPException(status_code=404, detail="任务不存在或已完成")
