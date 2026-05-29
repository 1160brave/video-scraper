<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useDownloadStore } from '@/stores/download'
import DownloadItem from '@/components/DownloadItem.vue'
import type { TaskInfo } from '@/services/api'
import { ElMessage } from 'element-plus'

const store = useDownloadStore()
type StatusFilter = 'all' | 'active' | 'completed' | 'failed'
const statusFilter = ref<StatusFilter>('all')

const taskStats = computed(() => [
  { label: '全部', value: store.tasks.length, type: 'default', filter: 'all' },
  { label: '下载中', value: store.activeTasks.length, type: 'primary', filter: 'active' },
  { label: '已完成', value: store.completedTasks.length, type: 'success', filter: 'completed' },
  { label: '失败/取消', value: store.failedTasks.length, type: 'warning', filter: 'failed' },
] satisfies Array<{ label: string; value: number; type: string; filter: StatusFilter }>)

const filteredTasks = computed(() => {
  if (statusFilter.value === 'active') return store.activeTasks
  if (statusFilter.value === 'completed') return store.completedTasks
  if (statusFilter.value === 'failed') return store.failedTasks
  return store.tasks
})

const filterOptions = computed(() => taskStats.value.map(stat => ({
  label: `${stat.label} ${stat.value}`,
  value: stat.filter,
})))

onMounted(() => {
  store.loadTasks()
  store.connectSSE()
})

onUnmounted(() => {
  store.disconnectSSE()
})

async function handleRetry(task: TaskInfo) {
  try {
    await store.retryTask(task)
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '重试任务失败'
    ElMessage.error(errorDetail)
  }
}
</script>

<template>
  <div class="downloads-view">
    <div class="header-section">
      <div>
        <span class="eyebrow">Queue</span>
        <h2>下载队列</h2>
        <p>按状态筛选任务，快速处理失败、取消和已完成的视频。</p>
      </div>
      <el-button plain @click="store.loadTasks">
        <el-icon><Refresh /></el-icon>
        刷新
      </el-button>
    </div>

    <div v-if="store.tasks.length > 0" class="queue-panel">
      <div class="stats-row">
        <button
          v-for="stat in taskStats"
          :key="stat.label"
          class="stat-item"
          :class="{ active: statusFilter === stat.filter }"
          type="button"
          @click="statusFilter = stat.filter"
        >
          <span class="stat-label">{{ stat.label }}</span>
          <strong :class="`stat-${stat.type}`">{{ stat.value }}</strong>
        </button>
      </div>

      <div class="filter-row">
        <span>状态筛选</span>
        <el-radio-group v-model="statusFilter" size="large">
          <el-radio-button
            v-for="option in filterOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <div v-if="store.tasks.length === 0" class="state-box">
      <el-empty description="暂无下载任务，先去爬取视频吧" :image-size="160" />
    </div>

    <template v-else>
      <section class="section">
        <div class="section-title">
          <h3>任务列表</h3>
          <span>{{ filteredTasks.length }} 个任务</span>
        </div>
        <div v-if="filteredTasks.length > 0" class="task-list">
          <DownloadItem
            v-for="task in filteredTasks"
            :key="task.task_id"
            :task="task"
            @cancel="store.cancelTask(task.task_id)"
            @retry="handleRetry(task)"
          />
        </div>
        <el-empty v-else description="当前筛选下暂无任务" :image-size="120" />
      </section>
    </template>
  </div>
</template>

<style scoped>
.downloads-view {
  margin: 0 auto;
}
h2 {
  color: var(--text-main);
  font-size: 28px;
  margin: 0;
}

.eyebrow {
  display: inline-block;
  margin-bottom: 8px;
  color: var(--brand);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.header-section p {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 13px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 20px;
  gap: 16px;
}

.queue-panel {
  padding: 14px;
  margin-bottom: 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  box-shadow: var(--shadow-soft);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.stat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 70px;
  padding: 14px;
  background: var(--surface-soft);
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  text-align: left;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.stat-item:hover,
.stat-item.active {
  border-color: #93c5fd;
  background: #eff6ff;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 600;
}

.stat-item strong {
  font-size: 28px;
  line-height: 1;
}

.stat-primary {
  color: var(--brand);
}

.stat-success {
  color: var(--success);
}

.stat-warning {
  color: var(--warning);
}

.filter-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.filter-row > span {
  color: var(--text-muted);
  font-size: 12px;
  font-weight: 700;
}

.section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title h3 {
  font-size: 15px;
  color: var(--text-secondary);
  margin: 0;
  font-weight: 700;
}

.section-title span {
  color: var(--text-muted);
  font-size: 12px;
}
.state-box {
  margin-top: 18px;
  padding: 42px 24px;
  background: var(--surface);
  border: 1px dashed var(--border-strong);
  border-radius: 16px;
}
.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

@media (max-width: 720px) {
  .header-section {
    align-items: stretch;
    flex-direction: column;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .filter-row {
    align-items: stretch;
    flex-direction: column;
    justify-content: stretch;
    overflow-x: auto;
  }
}
</style>
