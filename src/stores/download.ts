// 下载状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  startDownload,
  getTasks,
  cancelTask as apiCancelTask,
  createSSEConnection,
  type TaskInfo,
  type DownloadItem,
} from '@/services/api'

export const useDownloadStore = defineStore('download', () => {
  const tasks = ref<TaskInfo[]>([])
  let eventSource: EventSource | null = null

  const activeTasks = computed(() => tasks.value.filter(t => t.status === 'queued' || t.status === 'downloading'))
  const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed'))
  const failedTasks = computed(() => tasks.value.filter(t => t.status === 'failed'))

  async function loadTasks() {
    try {
      tasks.value = await getTasks()
    } catch {
      // backend might not be ready
    }
  }

  function connectSSE() {
    disconnectSSE()
    try {
      eventSource = createSSEConnection()
      eventSource.onmessage = (event) => {
        try {
          const updated = JSON.parse(event.data) as TaskInfo[]
          tasks.value = updated
        } catch { /* ignore malformed */ }
      }
      eventSource.onerror = () => {
        // EventSource will auto-reconnect
      }
    } catch { /* ignore */ }
  }

  function disconnectSSE() {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
  }

  async function addDownloads(items: DownloadItem[]) {
    if (items.length === 0) return
    await startDownload(items)
    await loadTasks()
    connectSSE()
  }

  async function cancelTask(taskId: string) {
    try {
      await apiCancelTask(taskId)
      await loadTasks()
    } catch { /* ignore */ }
  }

  async function retryTask(task: TaskInfo) {
    await addDownloads([{
      video_id: task.video_id,
      format_id: '',
      title: task.title,
      url: null,
      thumbnail: null,
      webpage_url: '',
    }])
  }

  return { tasks, activeTasks, completedTasks, failedTasks, loadTasks, connectSSE, disconnectSSE, addDownloads, cancelTask, retryTask }
})
