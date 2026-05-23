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


@router.post("/api/tasks/{task_id}/open-folder")
async def open_task_folder(task_id: str):
    """在文件资源管理器中定位并选中文件"""
    import os
    import subprocess
    import platform
    
    task_info = manager.get(task_id)
    if not task_info:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    file_path = task_info.file_path
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail="本地视频文件已不存在，可能已被移动或删除")
        
    try:
        sys_type = platform.system()
        if sys_type == "Windows":
            # Windows explorer /select,路径 可以选中文件
            subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
        elif sys_type == "Darwin":
            # macOS open -R 路径 可以选中文件
            subprocess.run(['open', '-R', file_path])
        else:
            # Linux 打开父目录
            parent_dir = os.path.dirname(file_path)
            subprocess.run(['xdg-open', parent_dir])
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打开文件位置失败: {str(e)}")


@router.get("/api/settings")
async def get_settings():
    """获取当前下载目录"""
    import config
    return {"download_dir": config.DOWNLOAD_DIR}


@router.post("/api/settings/select-folder")
async def select_folder():
    """调起原生选择文件夹对话框"""
    import os
    import config
    import webview
    
    if not config.active_window:
        raise HTTPException(
            status_code=400,
            detail="当前未运行在桌面客户端模式下，无法触发文件夹选择器"
        )
    
    try:
        res = config.active_window.create_file_dialog(webview.FOLDER_DIALOG)
        if res and len(res) > 0:
            folder_path = res[0]
            # 统一为绝对路径
            folder_path = os.path.abspath(folder_path)
            config.DOWNLOAD_DIR = folder_path
            # 确保文件夹存在
            os.makedirs(folder_path, exist_ok=True)
            # 持久化保存
            config.save_settings({"download_dir": folder_path})
            return {"download_dir": folder_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调起文件夹选择器失败: {str(e)}")
        
    return {"download_dir": config.DOWNLOAD_DIR}


@router.post("/api/settings")
async def update_settings(payload: dict):
    """手动保存下载目录（文本框输入）"""
    import os
    import config
    
    folder_path = payload.get("download_dir")
    if not folder_path:
        raise HTTPException(status_code=400, detail="文件夹路径不能为空")
        
    folder_path = os.path.expanduser(folder_path.strip())
    folder_path = os.path.abspath(folder_path)
    
    try:
        os.makedirs(folder_path, exist_ok=True)
        config.DOWNLOAD_DIR = folder_path
        # 持久化保存
        config.save_settings({"download_dir": folder_path})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"非法的文件夹路径或无创建权限: {str(e)}")
        
    return {"download_dir": config.DOWNLOAD_DIR}

