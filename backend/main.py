"""FastAPI 应用入口 — 同时提供 API 和前端静态文件"""
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from config import BACKEND_PORT, DOWNLOAD_DIR
from routers.scrape import router as scrape_router
from routers.download import router as download_router

# 前端静态文件路径（开发: src 目录 / 生产: dist 目录）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "dist")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(title="视频爬取工具", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(scrape_router)
app.include_router(download_router)


@app.get("/api/health")
async def health():
    try:
        import yt_dlp
        version = yt_dlp.version.__version__
    except Exception:
        version = "unknown"
    return {"status": "ok", "yt_dlp_version": version}


# 静态文件 + SPA fallback（必须在 API 路由之后注册）
if os.path.isdir(STATIC_DIR):
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        """SPA fallback: 非 API 路径返回前端 index.html"""
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    # 挂载 assets 目录
    assets_dir = os.path.join(STATIC_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=BACKEND_PORT)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    args = parser.parse_args()
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
