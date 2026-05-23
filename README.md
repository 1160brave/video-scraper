<p align="center">
  <h1 align="center">视频爬取工具 — Video Scraper & Downloader</h1>
  <p align="center">
    全平台视频数据采集下载工具 · 支持 1000+ 网站 · 跨平台桌面应用
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/platform-Windows%20%7C%20macOS-blue" alt="platform">
    <img src="https://img.shields.io/badge/python-3.13+-green" alt="python">
    <img src="https://img.shields.io/badge/license-MIT-brightgreen" alt="license">
    <img src="https://img.shields.io/badge/sites-1000%2B-orange" alt="sites">
  </p>
</p>

---

## 简介

**视频爬取工具** 是一款开源免费的跨平台桌面端视频下载器，基于 yt-dlp 构建的现代化 GUI 应用。支持从 **B站、YouTube、抖音、TikTok、Twitter、Instagram** 等 1000+ 网站爬取视频、批量下载。只需粘贴链接，自动解析视频地址、清晰度、格式，选择后一键下载到本地。

> A free & open-source cross-platform desktop video scraper and downloader. Built on yt-dlp with modern GUI. Supports batch downloading from YouTube, Bilibili, TikTok, Douyin, Twitter, Instagram and 1000+ sites. Just paste a link, pick a format, and download.

## 功能亮点

- **全平台爬取** — 支持 B站、YouTube、抖音/TikTok、微博、Twitter/X、Instagram 等 1000+ 视频网站
- **通用网页视频采集** — 任意网页中的 `<video>` 标签、`.mp4` / `.webm` / `.m3u8` 链接自动发现
- **智能格式选择** — 自动解析可用的分辨率（4K/1080p/720p）和编码格式
- **批量下载** — 多视频同时下载，实时显示进度、速度、剩余时间
- **无依赖运行** — 打包后无需安装 Python 环境，解压即用
- **跨平台** — Windows / macOS 双平台支持

## 快速开始

### 源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/1160brave/video-scraper.git
cd video-scraper

# 2. 安装前端依赖 & 编译
npm install && npm run build

# 3. 安装 Python 后端依赖
pip install -r backend/requirements.txt

# 4. 启动桌面应用
python run.py
```

### 下载打包版（推荐）

无需安装 Python，下载即用：

| 平台 | 下载 |
|------|------|
| Windows | [视频爬取工具-win64.zip](https://github.com/1160brave/video-scraper/actions) |
| macOS | 视频爬取工具.app |

下载方式：前往 [Actions](https://github.com/1160brave/video-scraper/actions) → 选择最新一次构建 → 底部 Artifacts 下载对应平台版本。

## 使用教程

1. **粘贴链接** — 输入任意视频页面 URL（B站/YouTube/网页均可）
2. **点击爬取** — 自动解析页面中的视频列表
3. **选择格式** — 每个视频可选分辨率（1080p / 720p / 480p 等）
4. **点击下载** — 开始下载，实时查看进度

## 支持的网站

**视频平台：** Bilibili、YouTube、抖音、TikTok、Twitter/X、Instagram、微博、Vimeo、Dailymotion、优酷、爱奇艺、腾讯视频 ...

**任意网页：** 自动发现页面中的 `<video>` 标签、`.mp4` / `.webm` / `.mkv` / `.m3u8` 等媒体文件

完整支持列表见 [yt-dlp 官方文档](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)（1000+ 站点）。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 UI | Vue 3 + Element Plus + TypeScript |
| 后端 | Python FastAPI + yt-dlp + httpx + BeautifulSoup |
| 桌面壳 | pywebview（Windows: Edge WebView2 / macOS: WebKit） |
| 打包 | PyInstaller |
| CI/CD | GitHub Actions（自动构建 Windows / macOS） |

## 项目结构

```
video-scraper/
├── src/                  # Vue 3 前端源码
│   ├── views/            # 页面（爬取页、下载管理页）
│   ├── components/       # 组件（视频卡片、格式选择器、进度条）
│   ├── stores/           # Pinia 状态管理
│   └── services/         # API 请求层
├── backend/              # Python 后端
│   ├── services/         # 爬虫服务（yt-dlp + 通用爬虫）
│   ├── routers/          # API 路由
│   └── schemas/          # 数据模型
├── .github/workflows/    # CI 自动构建
├── run.py                # 桌面启动入口
└── build.spec            # PyInstaller 打包配置
```

## 常见问题

**Q: 为什么有些视频下载失败？**
A: 部分平台需要 cookie 登录。yt-dlp 支持传入 cookies 文件，可在 `backend/config.py` 中配置。

**Q: macOS 打包版打不开？**
A: 在「系统设置 → 隐私与安全性」中允许未签名的应用运行，或执行 `xattr -cr 视频爬取工具.app`。

**Q: 下载的视频在哪？**
A: 默认保存在 `~/Downloads/VideoScraper/`，可在 `backend/config.py` 中修改路径。
