#!/usr/bin/env python3
"""桌面启动器 — 启动后端 + 打开桌面窗口"""
import sys
import os
import traceback
import datetime

# =====================================================================
# 0. 解决 console=False 时 sys.stdout/sys.stderr 为 None 导致 uvicorn 等库报错的问题
# =====================================================================
class DummyWriter:
    def write(self, *args, **kwargs):
        pass
    def flush(self):
        pass
    def isatty(self):
        return False

class DummyReader:
    def read(self, *args, **kwargs):
        return ""
    def readline(self, *args, **kwargs):
        return ""

if sys.stdout is None:
    sys.stdout = DummyWriter()
if sys.stderr is None:
    sys.stderr = DummyWriter()
if sys.stdin is None:
    sys.stdin = DummyReader()

# =====================================================================
# 1. 崩溃/异常日志记录与弹窗系统
# =====================================================================
def show_error_message(title, message):
    """根据操作系统，使用系统原生弹窗显示错误信息（避免依赖 GUI 库如 tkinter）"""
    if sys.platform == "win32":
        try:
            import ctypes
            # MB_ICONERROR (0x10) | MB_SETFOREGROUND (0x10000)
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10 | 0x10000)
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            # 使用 AppleScript 显示警告弹窗
            applescript = f'display dialog "{message}" with title "{title}" buttons {{"确定"}} default button "确定" with icon stop'
            subprocess.run(["osascript", "-e", applescript], capture_output=True)
        except Exception:
            pass
    else:
        # Linux/其他平台回退
        print(f"[{title}] {message}", file=sys.stderr)

def write_crash_log(error_type, error_msg):
    """将详细错误日志写入到本地文件，方便排查"""
    # 优先写入到 EXE 同级目录，如果是只读目录则写入到用户家目录
    if getattr(sys, 'frozen', False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_file = os.path.join(log_dir, "crash_error.log")
    
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("=========================================\n")
            f.write(f"           CRASH LOG ({error_type})       \n")
            f.write("=========================================\n")
            f.write(f"时间 (Time): {datetime.datetime.now()}\n")
            f.write(f"系统 (Platform): {sys.platform}\n")
            f.write(f"Python 版本: {sys.version}\n")
            f.write(f"是否打包 (Frozen): {getattr(sys, 'frozen', False)}\n")
            f.write(f"执行文件 (Executable): {sys.executable}\n")
            f.write("-----------------------------------------\n")
            f.write(error_msg)
            f.write("\n=========================================\n")
        return log_file
    except Exception:
        # 如果 EXE 目录无写入权限（例如在 C:\\Program Files），回退到家目录
        home_log = os.path.join(os.path.expanduser("~"), "video_scraper_crash.log")
        try:
            with open(home_log, "w", encoding="utf-8") as f:
                f.write(error_msg)
            return home_log
        except Exception:
            return "无法创建日志文件"

def global_exception_handler(exctype, value, tb):
    """全局未捕获异常的拦截器"""
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    log_file = write_crash_log("UnhandledException", error_msg)
    
    friendly_msg = (
        f"程序运行中发生未捕获的错误，无法继续运行！\n\n"
        f"【错误原因】\n{exctype.__name__}: {value}\n\n"
        f"【日志路径】\n{log_file}\n\n"
        f"请将上述日志文件反馈给开发人员进行修复。"
    )
    show_error_message("启动失败", friendly_msg)

# 注册全局异常捕获
sys.excepthook = global_exception_handler

# =====================================================================
# 2. 正常运行模块加载
# =====================================================================
import time
import threading
import socket

# 确保 backend 在 sys.path 中
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

# 静态导入，帮助 PyInstaller 在打包时自动识别并关联 backend 依赖，防止 ModuleNotFoundError
try:
    import config
    from config import BACKEND_PORT
    import fastapi.middleware.cors
    import fastapi.responses
    import fastapi.staticfiles
    import starlette.middleware.cors
    import starlette.responses
    import starlette.staticfiles
    import sse_starlette.sse
except Exception as e:
    # 显式捕获导入 backend config 的错误
    raise RuntimeError(f"加载后端依赖失败，请检查 backend 文件夹和 Python 依赖是否完整。\n详细错误: {e}")

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
    # 检查前端静态目录是否存在
    dist_dir = os.path.join(BASE_DIR, "dist")
    if not os.path.exists(dist_dir) or not os.path.isdir(dist_dir):
        error_msg = (
            f"未找到前端编译文件目录：\n{dist_dir}\n\n"
            f"【解决方法】\n"
            f"打包或运行前，请先在项目根目录下执行以下命令编译前端：\n"
            f"1. npm install\n"
            f"2. npm run build\n"
            f"然后再重新运行或进行打包。"
        )
        write_crash_log("MissingFrontendBuild", error_msg)
        show_error_message("前端文件缺失", error_msg)
        sys.exit(1)

    port = find_free_port()

    # 捕获子线程 uvicorn 的异常
    server_exception = None

    def run_server():
        nonlocal server_exception
        try:
            # 引入 uvicorn
            import uvicorn
            # 动态导入 backend.main 以确保 sys.path 生效
            import main as backend_main
            
            # 使用直接传入 app 对象，而不是字符串 "main:app"，这在 PyInstaller 环境中更加稳定
            uvicorn.run(
                backend_main.app,
                host="127.0.0.1",
                port=port,
                log_level="warning",
            )
        except Exception as e:
            server_exception = traceback.format_exc()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    server_url = f"http://127.0.0.1:{port}"
    print(f"后端已启动: {server_url}")

    # 等待后端就绪
    if not wait_for_server(f"{server_url}/api/health"):
        if server_exception:
            error_msg = (
                f"后端服务器（FastAPI/Uvicorn）启动失败！\n\n"
                f"【异常堆栈】\n{server_exception}"
            )
        else:
            error_msg = (
                f"后端服务连接超时（15秒）！\n\n"
                f"可能的原因：\n"
                f"1. 端口 {port} 绑定失败或被占用。\n"
                f"2. 缺少第三方 Python 依赖模块。\n"
                f"3. 操作系统防火墙或安全软件拦截。"
            )
        write_crash_log("ServerStartTimeout", error_msg)
        show_error_message("服务启动超时", error_msg)
        sys.exit(1)

    # 打开桌面窗口
    try:
        import webview
    except Exception as e:
        error_msg = f"加载 GUI 库 (pywebview) 失败，请检查依赖是否打包完整。\n详细错误: {e}"
        write_crash_log("WebviewImportError", error_msg)
        show_error_message("GUI 初始化失败", error_msg)
        sys.exit(1)

    try:
        window = webview.create_window(
            title="视频爬取工具",
            url=server_url,
            width=1200,
            height=800,
            min_size=(900, 600),
            resizable=True,
            fullscreen=False,
        )

        # 将窗口实例暴露给后端 API 接口，用于调起原生文件夹选择对话框
        config.active_window = window

        webview.start(debug=False)
        print("应用已退出")
    except Exception as e:
        error_msg = (
            f"打开桌面窗口发生异常！\n\n"
            f"【错误信息】\n{type(e).__name__}: {e}\n\n"
            f"【排查建议】\n"
            f"Windows 平台可能由于缺少 WebView2 运行时或 pythonnet 依赖导致。\n"
            f"详细堆栈已写入日志。"
        )
        write_crash_log("WebviewRenderError", traceback.format_exc())
        show_error_message("窗口创建失败", error_msg)
        sys.exit(1)


if __name__ == "__main__":
    main()
