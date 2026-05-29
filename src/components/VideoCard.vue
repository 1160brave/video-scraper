<script setup lang="ts">
import { computed } from 'vue'
import FormatSelector from './FormatSelector.vue'
import type { VideoInfo } from '@/services/api'

const props = defineProps<{
  video: VideoInfo
  selectedFormat?: string
  selected: boolean
}>()

const emit = defineEmits<{
  selectFormat: [formatId: string]
  toggleSelected: [selected: boolean]
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
  <div class="video-card" :class="{ selected }">
    <div class="select-zone">
      <el-checkbox
        class="select-check"
        :model-value="selected"
        @update:model-value="(value: string | number | boolean) => emit('toggleSelected', Boolean(value))"
      />
      <div class="thumb" @click="emit('toggleSelected', !selected)">
        <img v-if="thumbUrl" :src="thumbUrl" :alt="video.title" />
        <el-icon v-else :size="34"><VideoCamera /></el-icon>
        <span v-if="duration" class="duration">{{ duration }}</span>
      </div>
    </div>
    <div class="info">
      <div class="title" :title="video.title">{{ video.title }}</div>
      <div class="meta">
        <span>{{ video.formats.length }} 个格式</span>
        <span v-if="video.duration">{{ duration }}</span>
      </div>
      <FormatSelector
        :formats="video.formats"
        :model-value="selectedFormat"
        @update:model-value="(fid: string) => emit('selectFormat', fid)"
      />
    </div>
    <div class="actions">
      <el-button type="primary" size="small" :disabled="!selectedFormat" @click="emit('download')">
        <el-icon><Download /></el-icon>
        下载
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.video-card {
  display: grid;
  grid-template-columns: minmax(170px, 220px) minmax(0, 1fr) auto;
  align-items: center;
  gap: 16px;
  padding: 14px;
  background: var(--surface);
  border-radius: 14px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-soft);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.video-card:hover {
  border-color: #c6e2ff;
  box-shadow: 0 8px 24px rgba(31, 45, 61, 0.06);
}

.video-card.selected {
  border-color: #93c5fd;
  background: var(--surface);
}

.select-zone {
  display: flex;
  align-items: center;
  gap: 12px;
}

.select-check {
  flex-shrink: 0;
}

.thumb {
  width: 150px;
  height: 84px;
  border-radius: 10px;
  overflow: hidden;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  cursor: pointer;
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
  color: var(--text-main);
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  color: var(--text-muted);
  font-size: 12px;
}

.actions {
  flex-shrink: 0;
}

@media (max-width: 720px) {
  .video-card {
    align-items: stretch;
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .select-zone {
    align-items: flex-start;
  }

  .select-check {
    align-self: flex-start;
  }

  .thumb {
    width: 100%;
    height: auto;
    aspect-ratio: 16 / 9;
  }

  .actions {
    display: flex;
    justify-content: flex-end;
  }
}
</style>
