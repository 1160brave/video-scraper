<script setup lang="ts">
import { ref } from 'vue'

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
  emit('scrape', trimmed)
}
</script>

<template>
  <div class="url-input">
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
      {{ loading ? '爬取中...' : '开始爬取' }}
    </el-button>
  </div>
</template>

<style scoped>
.url-input {
  display: flex;
  gap: 12px;
}
.url-input .el-input {
  flex: 1;
}
</style>
