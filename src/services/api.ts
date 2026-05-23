// API 服务层
import axios from 'axios'

// 前端与后端同源（由 FastAPI 直接提供静态文件），使用相对路径
const BASE_URL = ''

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

// ---- 类型定义 ----

export interface VideoFormat {
  format_id: string
  ext: string
  resolution: string | null
  filesize: number | null
  format_note: string | null
  vcodec: string | null
  acodec: string | null
  has_audio: boolean
  has_video: boolean
  is_direct_url: boolean
  url: string | null
}

export interface VideoInfo {
  id: string
  title: string
  thumbnail: string | null
  duration: number | null
  webpage_url: string
  formats: VideoFormat[]
}

export interface ScrapeResponse {
  source_url: string
  platform: string
  page_title: string | null
  videos: VideoInfo[]
  error: string | null
}

export interface DownloadItem {
  video_id: string
  format_id: string
  title: string
  url: string | null
  thumbnail: string | null
  webpage_url: string
}

export interface DownloadRequest {
  downloads: DownloadItem[]
}

export interface TaskInfo {
  task_id: string
  video_id: string
  title: string
  status: 'queued' | 'downloading' | 'completed' | 'failed' | 'cancelled'
  progress: number
  speed: string | null
  eta: string | null
  downloaded_bytes: number
  total_bytes: number | null
  file_path: string | null
  error: string | null
}

// ---- API 方法 ----

export async function scrapeUrl(url: string): Promise<ScrapeResponse> {
  const { data } = await api.post<ScrapeResponse>('/api/scrape', { url })
  return data
}

export async function startDownload(downloads: DownloadItem[]): Promise<{ tasks: TaskInfo[] }> {
  const { data } = await api.post<{ tasks: TaskInfo[] }>('/api/download', { downloads })
  return data
}

export async function getTasks(): Promise<TaskInfo[]> {
  const { data } = await api.get<TaskInfo[]>('/api/tasks')
  return data
}

export async function cancelTask(taskId: string): Promise<void> {
  await api.delete(`/api/tasks/${taskId}`)
}

export function createSSEConnection(): EventSource {
  return new EventSource(`${BASE_URL}/api/tasks/stream`)
}

export { BASE_URL }
