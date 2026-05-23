<script setup lang="ts">
import { computed } from 'vue'
import type { VideoFormat } from '@/services/api'

const props = defineProps<{
  formats: VideoFormat[]
  modelValue?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [formatId: string]
}>()

const grouped = computed(() => {
  const groups: Record<string, VideoFormat[]> = {}
  for (const f of props.formats) {
    const key = f.format_note || f.resolution || f.ext || '默认'
    if (!groups[key]) groups[key] = []
    groups[key].push(f)
  }
  return Object.entries(groups)
})

function formatSize(bytes: number | null): string {
  if (!bytes) return ''
  if (bytes > 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)}GB`
  if (bytes > 1_000_000) return `${(bytes / 1_000_000).toFixed(0)}MB`
  return `${(bytes / 1000).toFixed(0)}KB`
}

function label(f: VideoFormat): string {
  const parts = [f.format_note || f.resolution, f.ext, formatSize(f.filesize)].filter(Boolean)
  return parts.join(' · ')
}
</script>

<template>
  <div class="format-selector">
    <el-select
      :model-value="modelValue"
      size="small"
      placeholder="选择格式"
      style="width: 220px"
      @update:model-value="(v: string) => emit('update:modelValue', v)"
    >
      <el-option-group
        v-for="[group, formats] in grouped"
        :key="group"
        :label="group"
      >
        <el-option
          v-for="fmt in formats"
          :key="fmt.format_id"
          :label="label(fmt)"
          :value="fmt.format_id"
        />
      </el-option-group>
    </el-select>
  </div>
</template>
