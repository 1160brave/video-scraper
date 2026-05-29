// 下载状态管理
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  startDownload,
  getTasks,
  cancelTask as apiCancelTask,
  retryTask as apiRetryTask,
  createSSEConnection,
  type TaskInfo,
  type DownloadItem,
} from '@/services/api'

export const useDownloadStore = defineStore('download', () => {
  const tasks = ref<TaskInfo[]>([])
  const submitting = ref(false)
  let eventSource: EventSource | null = null

  const activeTasks = computed(() => tasks.value.filter(t => t.status === 'queued' || t.status === 'downloading'))
  const completedTasks = computed(() => tasks.value.filter(t => t.status === 'completed'))
  const failedTasks = computed(() => tasks.value.filter(t => t.status === 'failed' || t.status === 'cancelled'))

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
    submitting.value = true
    try {
      await startDownload(items)
      await loadTasks()
      connectSSE()
    } finally {
      submitting.value = false
    }
  }

  async function cancelTask(taskId: string) {
    try {
      await apiCancelTask(taskId)
      await loadTasks()
    } catch { /* ignore */ }
  }

  async function retryTask(task: TaskInfo) {
    await apiRetryTask(task.task_id)
    await loadTasks()
    connectSSE()
  }

  return { tasks, submitting, activeTasks, completedTasks, failedTasks, loadTasks, connectSSE, disconnectSSE, addDownloads, cancelTask, retryTask }
})
