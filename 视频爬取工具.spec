# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = [
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
    'clr',       # pywebview Windows .NET 依赖 (WebView2 核心)
    'win32gui',  # pywebview Windows Win32 依赖
    'win32con',
    'win32api',
]
hiddenimports += collect_submodules('fastapi')
hiddenimports += collect_submodules('starlette')
hiddenimports += collect_submodules('uvicorn')
hiddenimports += collect_submodules('sse_starlette')

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('backend', 'backend'), ('dist', 'dist')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'numpy', 'pandas', 'matplotlib', 'PIL'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='视频爬取工具',
)
app = BUNDLE(
    coll,
    name='视频爬取工具.app',
    icon=None,
    bundle_identifier=None,
)
