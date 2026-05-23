<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useDownloadStore } from '@/stores/download'
import DownloadItem from '@/components/DownloadItem.vue'

const store = useDownloadStore()

onMounted(() => {
  store.loadTasks()
  store.connectSSE()
})

onUnmounted(() => {
  store.disconnectSSE()
})
</script>

<template>
  <div class="downloads-view">
    <div class="header-section">
      <h2>下载管理</h2>
    </div>

    <div v-if="store.tasks.length === 0" class="state-box">
      <el-empty description="暂无下载任务，先去爬取视频吧" :image-size="160" />
    </div>

    <template v-else>
      <!-- 下载中 -->
      <section v-if="store.activeTasks.length > 0" class="section">
        <h3>下载中 ({{ store.activeTasks.length }})</h3>
        <div class="task-list">
          <DownloadItem
            v-for="task in store.activeTasks"
            :key="task.task_id"
            :task="task"
            @cancel="store.cancelTask(task.task_id)"
          />
        </div>
      </section>

      <!-- 已完成 -->
      <section v-if="store.completedTasks.length > 0" class="section">
        <h3>已完成 ({{ store.completedTasks.length }})</h3>
        <div class="task-list">
          <DownloadItem
            v-for="task in store.completedTasks"
            :key="task.task_id"
            :task="task"
            @cancel="() => {}"
          />
        </div>
      </section>

      <!-- 失败 -->
      <section v-if="store.failedTasks.length > 0" class="section">
        <h3>失败 ({{ store.failedTasks.length }})</h3>
        <div class="task-list">
          <DownloadItem
            v-for="task in store.failedTasks"
            :key="task.task_id"
            :task="task"
            @cancel="() => {}"
            @retry="store.retryTask(task)"
          />
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.downloads-view {
  max-width: 900px;
  margin: 0 auto;
}
h2 {
  font-size: 20px;
  margin: 0;
}
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.section {
  margin-bottom: 24px;
}
.section h3 {
  font-size: 15px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 500;
}
.state-box {
  margin-top: 60px;
}
.task-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
