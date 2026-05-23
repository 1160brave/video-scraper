<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import ProgressBar from './ProgressBar.vue'
import type { TaskInfo } from '@/services/api'

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

function formatBytes(bytes: number): string {
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

function handleOpenFile() {
  if (props.task.file_path) {
    // 在 webview 环境下显示文件路径
    ElMessage.success(`文件已保存至: ${props.task.file_path}`)
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
        <el-icon v-else color="#909399" :size="22"><Clock /></el-icon>
      </div>
      <div class="item-info">
        <div class="item-title">{{ task.title }}</div>
        <div class="item-meta">
          <el-tag :type="statusType" size="small">{{ statusText }}</el-tag>
          <span v-if="showProgress" class="size">{{ sizeInfo }}</span>
          <span v-if="task.speed" class="speed">{{ task.speed }}</span>
          <span v-if="task.eta" class="eta">剩余 {{ task.eta }}</span>
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
        v-if="task.status === 'downloading'"
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
        v-if="task.status === 'failed'"
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
  padding: 14px 16px;
  background: #fff;
  border-radius: 8px;
}
.item-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}
.item-icon {
  margin-top: 2px;
  flex-shrink: 0;
}
.item-info {
  flex: 1;
  min-width: 0;
}
.item-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.error-msg {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}
.item-actions {
  flex-shrink: 0;
}
</style>
