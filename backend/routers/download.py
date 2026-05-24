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
    """获取当前下载及 Cookie 配置"""
    import config
    return {
        "download_dir": config.DOWNLOAD_DIR,
        "cookie_mode": config.COOKIE_MODE,
        "cookie_browser": config.COOKIE_BROWSER,
        "cookie_manual": config.COOKIE_MANUAL,
        "cookie_file": config.COOKIE_FILE,
        "max_concurrent": config.MAX_CONCURRENT_DOWNLOADS,
        "ffmpeg_installed": config.check_ffmpeg(),
    }


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


@router.post("/api/settings/select-cookie-file")
async def select_cookie_file():
    """调起原生选择 Cookies.txt 文件对话框"""
    import os
    import config
    import webview
    
    if not config.active_window:
        raise HTTPException(
            status_code=400,
            detail="当前未运行在桌面客户端模式下，无法触发文件选择器"
        )
        
    try:
        # pywebview create_file_dialog 返回选择的文件路径列表或 None
        res = config.active_window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=("Cookies Text File (*.txt)", "*.txt")
        )
        if res and len(res) > 0:
            file_path = res[0]
            file_path = os.path.abspath(file_path)
            config.COOKIE_FILE = file_path
            config.save_settings({"cookie_file": file_path})
            return {"cookie_file": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调起文件选择器失败: {str(e)}")
        
    return {"cookie_file": config.COOKIE_FILE}


@router.post("/api/settings")
async def update_settings(payload: dict):
    """保存下载及 Cookie 配置"""
    import os
    import config
    
    # 1. 尝试修改下载路径（如果包含）
    if "download_dir" in payload:
        folder_path = payload["download_dir"]
        if folder_path:
            folder_path = os.path.expanduser(folder_path.strip())
            folder_path = os.path.abspath(folder_path)
            try:
                os.makedirs(folder_path, exist_ok=True)
                config.DOWNLOAD_DIR = folder_path
                config.save_settings({"download_dir": folder_path})
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"非法的文件夹路径或无创建权限: {str(e)}")
    
    # 2. 尝试修改 Cookie 与并发数设置
    updates = {}
    if "cookie_mode" in payload:
        mode = payload["cookie_mode"]
        if mode in ("none", "browser", "file", "manual"):
            config.COOKIE_MODE = mode
            updates["cookie_mode"] = mode
            
    if "cookie_browser" in payload:
        browser = payload["cookie_browser"]
        config.COOKIE_BROWSER = browser
        updates["cookie_browser"] = browser
        
    if "cookie_manual" in payload:
        manual = payload["cookie_manual"]
        config.COOKIE_MANUAL = manual
        updates["cookie_manual"] = manual
        
    if "cookie_file" in payload:
        file_path = payload["cookie_file"]
        if file_path:
            file_path = os.path.expanduser(file_path.strip())
            file_path = os.path.abspath(file_path)
        config.COOKIE_FILE = file_path
        updates["cookie_file"] = file_path

    if "max_concurrent" in payload:
        try:
            val = int(payload["max_concurrent"])
            if 1 <= val <= 10:
                config.MAX_CONCURRENT_DOWNLOADS = val
                updates["max_concurrent"] = val
                # 动态刷新后台队列的并发控制
                manager.update_max_concurrent(val)
        except Exception:
            pass
        
    if updates:
        config.save_settings(updates)
        
    return {
        "download_dir": config.DOWNLOAD_DIR,
        "cookie_mode": config.COOKIE_MODE,
        "cookie_browser": config.COOKIE_BROWSER,
        "cookie_manual": config.COOKIE_MANUAL,
        "cookie_file": config.COOKIE_FILE,
        "max_concurrent": config.MAX_CONCURRENT_DOWNLOADS,
        "ffmpeg_installed": config.check_ffmpeg(),
    }

