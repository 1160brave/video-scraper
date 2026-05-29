<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import ProgressBar from './ProgressBar.vue'
import type { TaskInfo } from '@/services/api'
import { openFolder } from '@/services/api'

const props = defineProps<{
  task: TaskInfo
}>()

const emit = defineEmits<{
  cancel: []
  retry: []
 }>()

const statusType = computed(() => {
  switch (props.task.status) {
    case 'completed': return 'success'
    case 'failed': return 'danger'
    case 'downloading': return ''
    case 'cancelled': return 'warning'
    default: return 'info'
  }
})

const statusText = computed(() => {
  const map: Record<string, string> = {
    queued: '排队中',
    downloading: '下载中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
  }
  return map[props.task.status] || props.task.status
})

const showProgress = computed(() =>
  props.task.status === 'downloading' || props.task.status === 'queued'
)

const canCancel = computed(() =>
  props.task.status === 'downloading' || props.task.status === 'queued'
)

function formatBytes(bytes: number): string {
  if (!bytes) return '0B'
  if (bytes > 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)}GB`
  if (bytes > 1_000_000) return `${(bytes / 1_000_000).toFixed(0)}MB`
  return `${(bytes / 1000).toFixed(0)}KB`
}

const sizeInfo = computed(() => {
  const d = formatBytes(props.task.downloaded_bytes)
  if (props.task.total_bytes) {
    return `${d} / ${formatBytes(props.task.total_bytes)}`
  }
  return d
})

async function handleOpenFile() {
  try {
    await openFolder(props.task.task_id)
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '打开文件位置失败'
    ElMessage.error(errorDetail)
  }
}
</script>

<template>
  <div class="download-item" :class="`status-${task.status}`">
    <div class="item-main">
      <div class="item-icon">
        <el-icon v-if="task.status === 'completed'" color="#67c23a" :size="22"><CircleCheckFilled /></el-icon>
        <el-icon v-else-if="task.status === 'failed'" color="#f56c6c" :size="22"><CircleCloseFilled /></el-icon>
        <el-icon v-else-if="task.status === 'downloading'" color="#409eff" :size="22"><VideoCameraFilled /></el-icon>
        <el-icon v-else-if="task.status === 'cancelled'" color="#e6a23c" :size="22"><CircleClose /></el-icon>
        <el-icon v-else color="#909399" :size="22"><Clock /></el-icon>
      </div>
      <div class="item-info">
        <div class="item-title-row">
          <div class="item-title">{{ task.title }}</div>
          <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
        </div>
        <div class="item-meta">
          <span v-if="showProgress" class="size">{{ sizeInfo }}</span>
          <span v-if="task.speed" class="speed">{{ task.speed }}</span>
          <span v-if="task.eta" class="eta">剩余 {{ task.eta }}</span>
          <span v-if="!showProgress && task.file_path" class="path">{{ task.file_path }}</span>
        </div>
        <ProgressBar
          v-if="showProgress"
          :progress="task.progress"
          :status="task.status"
        />
        <div v-if="task.error" class="error-msg">{{ task.error }}</div>
      </div>
    </div>
    <div class="item-actions">
      <el-button
        v-if="canCancel"
        size="small"
        type="warning"
        @click="emit('cancel')"
      >取消</el-button>
      <el-button
        v-if="task.status === 'completed' && task.file_path"
        size="small"
        @click="handleOpenFile"
      >打开位置</el-button>
      <el-button
        v-if="task.status === 'failed' || task.status === 'cancelled'"
        size="small"
        type="primary"
        @click="emit('retry')"
      >重试</el-button>
    </div>
  </div>
</template>

<style scoped>
.download-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px;
  background: var(--surface);
  border-radius: 14px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-soft);
}
.item-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}
.item-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  margin-top: 1px;
  background: var(--surface-soft);
  border-radius: 10px;
  flex-shrink: 0;
}
.item-info {
  flex: 1;
  min-width: 0;
}
.item-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}

.item-title {
  color: var(--text-main);
  font-size: 14px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.error-msg {
  color: var(--danger);
  font-size: 12px;
  margin-top: 4px;
  overflow-wrap: anywhere;
}
.path {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-actions {
  flex-shrink: 0;
  display: flex;
  gap: 8px;
}

@media (max-width: 720px) {
  .download-item {
    align-items: stretch;
    flex-direction: column;
  }

  .item-actions {
    justify-content: flex-end;
  }

  .item-meta {
    align-items: flex-start;
    flex-wrap: wrap;
  }

  .item-title-row {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
