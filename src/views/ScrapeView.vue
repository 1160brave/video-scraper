<script setup lang="ts">
import { useScraperStore } from '@/stores/scraper'
import { useDownloadStore } from '@/stores/download'
import { useRouter } from 'vue-router'
import { computed } from 'vue'
import UrlInput from '@/components/UrlInput.vue'
import VideoCard from '@/components/VideoCard.vue'
import type { DownloadItem } from '@/services/api'
import { ElMessage } from 'element-plus'

const store = useScraperStore()
const downloadStore = useDownloadStore()
const router = useRouter()

const selectedVideos = computed(() => {
  if (!store.result) return []
  return store.result.videos.filter(v => store.getSelectedFormat(v.id))
})

async function handleScrape(url: string) {
  await store.scrape(url)
}

async function handleDownloadSelected() {
  const items: DownloadItem[] = selectedVideos.value.map(v => {
    const fmt = v.formats.find(f => f.format_id === store.getSelectedFormat(v.id))
    return {
      video_id: v.id,
      format_id: store.getSelectedFormat(v.id)!,
      title: v.title,
      url: fmt?.is_direct_url ? fmt.url : null,
      thumbnail: v.thumbnail,
      webpage_url: v.webpage_url,
    }
  })
  try {
    await downloadStore.addDownloads(items)
    router.push('/downloads')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '提交下载任务失败'
    ElMessage.error(errorDetail)
  }
}

async function handleDownloadOne(videoId: string) {
  const v = store.result?.videos.find(x => x.id === videoId)
  if (!v) return
  const fmt = v.formats.find(f => f.format_id === store.getSelectedFormat(v.id))
  const items: DownloadItem[] = [{
    video_id: v.id,
    format_id: store.getSelectedFormat(v.id)!,
    title: v.title,
    url: fmt?.is_direct_url ? fmt.url : null,
    thumbnail: v.thumbnail,
    webpage_url: v.webpage_url,
  }]
  try {
    await downloadStore.addDownloads(items)
    router.push('/downloads')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '提交下载任务失败'
    ElMessage.error(errorDetail)
  }
}
</script>

<template>
  <div class="scrape-view">
    <UrlInput :loading="store.status === 'loading'" @scrape="handleScrape" />

    <!-- idle -->
    <div v-if="store.status === 'idle'" class="state-box">
      <el-empty description="输入视频链接，开始爬取" :image-size="160" />
    </div>

    <!-- loading -->
    <div v-if="store.status === 'loading'" class="state-box">
      <el-skeleton :rows="3" animated />
      <el-skeleton :rows="3" animated style="margin-top: 16px" />
    </div>

    <!-- error -->
    <div v-if="store.status === 'error'" class="state-box">
      <el-result icon="error" :title="store.error || '爬取失败'">
        <template #extra>
          <el-button type="primary" @click="handleScrape(store.url)">重试</el-button>
        </template>
      </el-result>
    </div>

    <!-- success -->
    <div v-if="store.status === 'success' && store.result" class="results">
      <div class="results-header">
        <div class="results-info">
          <el-tag size="small">{{ store.result.platform }}</el-tag>
          <span class="page-title">{{ store.result.page_title || store.result.source_url }}</span>
          <span class="count">共 {{ store.result.videos.length }} 个视频</span>
        </div>
        <el-button
          type="primary"
          :disabled="selectedVideos.length === 0"
          :loading="downloadStore.submitting"
          @click="handleDownloadSelected"
        >
          下载选中 ({{ selectedVideos.length }})
        </el-button>
      </div>

      <div class="video-list">
        <VideoCard
          v-for="video in store.result.videos"
          :key="video.id"
          :video="video"
          :selected-format="store.getSelectedFormat(video.id)"
          @select-format="(fid: string) => store.selectFormat(video.id, fid)"
          @download="handleDownloadOne(video.id)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrape-view {
  max-width: 900px;
  margin: 0 auto;
}
.state-box {
  margin-top: 60px;
}
.results {
  margin-top: 20px;
}
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 8px;
}
.results-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  overflow: hidden;
}
.page-title {
  font-size: 14px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.count {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}
.video-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
