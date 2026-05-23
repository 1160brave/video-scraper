# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[('backend', 'backend'), ('dist', 'dist')],
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
        'sse_starlette',
        'aiofiles',
        'fastapi',
        'starlette',
        'webview',
        'clr',       # pywebview Windows .NET 依赖 (WebView2 核心)
        'win32gui',  # pywebview Windows Win32 依赖
        'win32con',
        'win32api',
    ],
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
