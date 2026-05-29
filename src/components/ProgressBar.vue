<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  progress: number
  status: string
}>()

const color = computed(() => {
  if (props.status === 'completed') return '#67c23a'
  if (props.status === 'failed') return '#f56c6c'
  if (props.status === 'cancelled') return '#909399'
  return '#409eff'
})

const safeProgress = computed(() => {
  if (!Number.isFinite(props.progress)) return 0
  return Math.min(100, Math.max(0, Math.round(props.progress)))
})
</script>

<template>
  <div class="progress-bar">
    <el-progress
      :percentage="safeProgress"
      :color="color"
      :stroke-width="6"
      :show-text="true"
    />
  </div>
</template>
