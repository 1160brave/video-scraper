# 视频爬取工具

桌面端视频爬取应用，支持 B站/YouTube 等视频平台和任意网页中的视频。

## 功能

- 输入链接 → 自动识别视频（支持 1000+ 视频平台 + 任意网页）
- 展示视频列表（缩略图、标题、分辨率、格式）
- 选择清晰度 → 一键下载
- 实时进度、多任务管理

## 运行

```bash
# 安装前端依赖
npm install

# 编译前端
npm run build

# 安装后端依赖
pip install -r backend/requirements.txt

# 启动
python run.py
```

## 下载打包版

前往 [Releases](https://github.com/1160brave/video-scraper/releases) 或 [Actions](https://github.com/1160brave/video-scraper/actions) 下载对应平台版本：

- **Windows** — `视频爬取工具-win64.zip`
- **macOS** — `视频爬取工具.app`

打包版无需安装 Python，解压即用。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Element Plus + TypeScript |
| 后端 | Python FastAPI |
| 爬虫 | yt-dlp + httpx + BeautifulSoup |
| 桌面壳 | pywebview |
| 打包 | PyInstaller |
