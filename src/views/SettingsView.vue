<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, selectFolder, saveSettings } from '@/services/api'
import { ElMessage } from 'element-plus'

const downloadDir = ref('')
const saving = ref(false)

const loadSettings = async () => {
  try {
    const settings = await getSettings()
    downloadDir.value = settings.download_dir
  } catch (error: any) {
    console.error('获取下载设置失败:', error)
  }
}

const handleSelectFolder = async () => {
  try {
    const settings = await selectFolder()
    downloadDir.value = settings.download_dir
    ElMessage.success('成功更改视频下载路径')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '选择文件夹失败'
    ElMessage.error(errorDetail)
  }
}

const handleSaveSettings = async () => {
  if (!downloadDir.value.trim()) {
    ElMessage.warning('路径不能为空')
    return
  }
  saving.value = true
  try {
    const settings = await saveSettings(downloadDir.value)
    downloadDir.value = settings.download_dir
    ElMessage.success('下载路径保存成功')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '保存路径失败'
    ElMessage.error(errorDetail)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div class="settings-view">
    <div class="header-section">
      <h2>系统设置</h2>
    </div>

    <!-- 下载目录设置卡片 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="settings-header">
          <el-icon class="folder-icon"><FolderOpened /></el-icon>
          <span class="settings-title">视频保存路径</span>
        </div>
      </template>
      <div class="settings-body">
        <div class="input-row">
          <el-input
            v-model="downloadDir"
            placeholder="请选择或手动输入视频保存路径"
            class="dir-input"
            clearable
          />
          <el-button type="primary" class="select-btn" @click="handleSelectFolder">
            <el-icon><Folder /></el-icon>
            &nbsp;选择文件夹
          </el-button>
          <el-button type="success" class="save-btn" @click="handleSaveSettings" :loading="saving">
            保存修改
          </el-button>
        </div>
        <p class="settings-tip">
          提示：下载视频时将自动保存到此路径下。您可以使用网络共享路径或本地绝对路径。
        </p>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.settings-view {
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
  margin-bottom: 24px;
}
.settings-card {
  border-radius: 8px;
  background-color: #fafafa;
}
.settings-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.folder-icon {
  font-size: 18px;
  color: #409eff;
}
.settings-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.settings-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.input-row {
  display: flex;
  gap: 12px;
  width: 100%;
}
.dir-input {
  flex: 1;
}
.select-btn {
  flex-shrink: 0;
}
.save-btn {
  flex-shrink: 0;
}
.settings-tip {
  font-size: 12px;
  color: #909399;
  margin: 4px 0 0 0;
}
</style>
