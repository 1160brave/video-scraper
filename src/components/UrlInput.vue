<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  scrape: [url: string]
}>()

const url = ref('')

function handleSubmit() {
  const trimmed = url.value.trim()
  if (!trimmed) return
  if (!isValidUrl(trimmed)) {
    ElMessage.warning('请输入完整的视频链接，例如 https://example.com/video')
    return
  }
  emit('scrape', trimmed)
}

function isValidUrl(value: string): boolean {
  try {
    const parsed = new URL(value)
    return ['http:', 'https:'].includes(parsed.protocol)
  } catch {
    return false
  }
}
</script>

<template>
  <div class="url-input">
    <div class="input-meta">
      <span>URL</span>
      <small>页面链接 / 播放列表 / 直链媒体</small>
    </div>
    <el-input
      v-model="url"
      placeholder="输入视频页面链接，支持 B站/YouTube/任意网页..."
      size="large"
      clearable
      :disabled="loading"
      @keyup.enter="handleSubmit"
    >
      <template #prefix>
        <el-icon><Link /></el-icon>
      </template>
    </el-input>
    <el-button
      type="primary"
      size="large"
      :loading="loading"
      :disabled="!url.trim()"
      @click="handleSubmit"
    >
      <el-icon v-if="!loading"><Search /></el-icon>
      {{ loading ? '爬取中...' : '开始爬取' }}
    </el-button>
  </div>
</template>

<style scoped>
.url-input {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  box-shadow: var(--shadow-soft);
}

.input-meta {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.input-meta span {
  color: var(--text-main);
  font-size: 13px;
  font-weight: 700;
}

.input-meta small {
  color: var(--text-muted);
  font-size: 12px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.url-input .el-input {
  flex: 1;
}

.url-input .el-button {
  min-width: 124px;
}

@media (max-width: 720px) {
  .url-input {
    grid-template-columns: 1fr;
  }

  .input-meta small {
    white-space: normal;
  }

  .url-input .el-button {
    width: 100%;
  }
}
</style>
