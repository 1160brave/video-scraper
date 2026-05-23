# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 — 支持 macOS .app 和 Windows .exe"""

import sys
from pathlib import Path

BASE = Path(SPECPATH)
IS_MAC = sys.platform == 'darwin'
IS_WIN = sys.platform == 'win32'

a = Analysis(
    ['run.py'],
    pathex=[str(BASE)],
    binaries=[],
    datas=[
        (str(BASE / 'backend'), 'backend'),
        (str(BASE / 'backend' / 'routers'), 'backend/routers'),
        (str(BASE / 'backend' / 'services'), 'backend/services'),
        (str(BASE / 'backend' / 'schemas'), 'backend/schemas'),
        (str(BASE / 'dist'), 'dist'),
    ],
    hiddenimports=[
        'uvicorn.loops.auto',
        'uvicorn.loops.select',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.lifespan.on',
        'uvicorn.logging',
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.downloader',
        'httpx',
        'bs4',
        'lxml',
        'fastapi',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'fastapi.responses',
        'starlette',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.staticfiles',
        'starlette.responses',
        'sse_starlette',
        'sse_starlette.sse',
        'aiofiles',
        'webview',
        'clr',       # pywebview Windows 依赖
        'win32gui',  # pywebview Windows 依赖
        'win32con',
        'win32api',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
    ],
)

pyz = PYZ(a.pure)

if IS_MAC:
    # macOS: 打包为 .app
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='视频爬取工具',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        target_architecture=None,
    )
    app = BUNDLE(
        exe,
        name='视频爬取工具.app',
        icon=None,
        bundle_identifier='com.video-scraper.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleName': '视频爬取工具',
        },
    )
else:
    # Windows: 打包为单个 .exe
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name='视频爬取工具',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        icon=None,
        target_architecture='x86_64',
    )
