<script setup lang="ts">
import { computed } from 'vue'
import FormatSelector from './FormatSelector.vue'
import type { VideoInfo } from '@/services/api'

const props = defineProps<{
  video: VideoInfo
  selectedFormat?: string
}>()

const emit = defineEmits<{
  selectFormat: [formatId: string]
  download: []
}>()

const duration = computed(() => {
  if (!props.video.duration) return ''
  const m = Math.floor(props.video.duration / 60)
  const s = Math.floor(props.video.duration % 60)
  return `${m}:${String(s).padStart(2, '0')}`
})

const thumbUrl = computed(() => props.video.thumbnail || '')
</script>

<template>
  <div class="video-card">
    <div class="thumb">
      <img v-if="thumbUrl" :src="thumbUrl" :alt="video.title" />
      <el-icon v-else :size="48"><VideoCamera /></el-icon>
      <span v-if="duration" class="duration">{{ duration }}</span>
    </div>
    <div class="info">
      <div class="title" :title="video.title">{{ video.title }}</div>
      <FormatSelector
        :formats="video.formats"
        :model-value="selectedFormat"
        @update:model-value="(fid: string) => emit('selectFormat', fid)"
      />
    </div>
    <div class="actions">
      <el-button type="primary" size="small" :disabled="!selectedFormat" @click="emit('download')">
        下载
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.video-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
}
.thumb {
  width: 160px;
  height: 90px;
  border-radius: 6px;
  overflow: hidden;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
}
.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.duration {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  font-size: 11px;
  padding: 1px 5px;
  border-radius: 3px;
}
.info {
  flex: 1;
  min-width: 0;
}
.title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.actions {
  flex-shrink: 0;
}
</style>
