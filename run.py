#!/usr/bin/env python3
"""桌面启动器 — 启动后端 + 打开桌面窗口"""
import sys
import os
import time
import threading
import socket

import uvicorn
import webview

# 确保 backend 在 sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from config import BACKEND_PORT

API_URL = f"http://127.0.0.1:{BACKEND_PORT}"


def find_free_port() -> int:
    """找一个空闲端口"""
    port = BACKEND_PORT
    for offset in range(10):
        test_port = port + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", test_port)) != 0:
                return test_port
    return port


def wait_for_server(url: str, timeout: int = 15) -> bool:
    """等待服务器就绪"""
    import urllib.request
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.urlopen(url, timeout=2)
            if req.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    port = find_free_port()

    # 启动 uvicorn 在独立线程
    def run_server():
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    server_url = f"http://127.0.0.1:{port}"
    print(f"后端已启动: {server_url}")

    if not wait_for_server(f"{server_url}/api/health"):
        print("后端启动超时，请检查是否正常编译了前端文件 (npm run build)")
        sys.exit(1)

    # 打开桌面窗口
    window = webview.create_window(
        title="视频爬取工具",
        url=server_url,
        width=1200,
        height=800,
        min_size=(900, 600),
        resizable=True,
        fullscreen=False,
    )

    webview.start(debug=False)
    print("应用已退出")


if __name__ == "__main__":
    main()
