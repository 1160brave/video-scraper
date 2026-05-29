<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useDownloadStore } from '@/stores/download'

const route = useRoute()
const downloadStore = useDownloadStore()
const activeMenu = computed(() => route.path)
const activeCount = computed(() => downloadStore.activeTasks.length)
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-mark">
          <el-icon :size="21"><VideoCameraFilled /></el-icon>
        </div>
        <div>
          <span>视频爬取工具</span>
          <small>批量解析与下载</small>
        </div>
      </div>
      <div class="sidebar-label">工作区</div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="transparent"
        text-color="#98a2b3"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/">
          <el-icon><Search /></el-icon>
          <span>视频爬取</span>
        </el-menu-item>
        <el-menu-item index="/downloads">
          <el-icon><Download /></el-icon>
          <span>下载管理</span>
          <el-badge
            v-if="activeCount > 0"
            :value="activeCount"
            :max="99"
            class="menu-badge"
          />
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Tools /></el-icon>
          <span>下载设置</span>
        </el-menu-item>
      </el-menu>
      <div class="sidebar-foot">
        <span>本地任务</span>
        <strong>{{ downloadStore.tasks.length }}</strong>
      </div>
    </aside>
    <main class="main-content">
      <div class="content-inner">
        <router-view />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  background: var(--app-bg);
}

.sidebar {
  width: 248px;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  padding: 18px 14px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 8px 20px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}

.logo-mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  color: #fff;
  background: #2563eb;
  border-radius: 10px;
}

.logo small {
  display: block;
  margin-top: 3px;
  color: #98a2b3;
  font-size: 11px;
  font-weight: 500;
}

.sidebar-label {
  margin: 8px 8px 10px;
  color: #667085;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.sidebar :deep(.el-menu) {
  border-right: none;
  background: transparent;
}

.sidebar :deep(.el-menu-item) {
  height: 44px;
  margin-bottom: 6px;
  border-radius: 10px;
  padding-left: 12px !important;
  color: #98a2b3;
}

.sidebar :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.06);
}

.sidebar :deep(.el-menu-item.is-active) {
  background: var(--sidebar-active);
  box-shadow: inset 3px 0 0 #60a5fa;
}

.menu-badge {
  margin-left: auto;
  margin-right: 4px;
}

.sidebar-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding: 12px;
  color: #98a2b3;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.sidebar-foot strong {
  color: #fff;
  font-size: 16px;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding: 32px;
}

.content-inner {
  width: min(1180px, 100%);
  margin: 0 auto;
}

@media (max-width: 760px) {
  .app-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    padding: 10px;
  }

  .logo {
    padding: 12px 16px;
  }

  .sidebar-label,
  .sidebar-foot,
  .logo small {
    display: none;
  }

  .sidebar :deep(.el-menu) {
    display: flex;
  }

  .sidebar :deep(.el-menu-item) {
    flex: 1;
    justify-content: center;
  }

  .main-content {
    padding: 16px;
  }
}
</style>
