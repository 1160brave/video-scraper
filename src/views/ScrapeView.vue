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
  return store.result.videos.filter(v => store.isVideoSelected(v.id) && store.getSelectedFormat(v.id))
})

const totalFormats = computed(() =>
  store.result?.videos.reduce((sum, video) => sum + video.formats.length, 0) ?? 0
)

const allSelected = computed(() =>
  Boolean(store.result?.videos.length) && selectedVideos.value.length === store.result?.videos.length
)

async function handleScrape(url: string) {
  await store.scrape(url)
}

async function handleDownloadSelected() {
  const items = selectedVideos.value.map(buildDownloadItem)
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
  try {
    await downloadStore.addDownloads([buildDownloadItem(v)])
    router.push('/downloads')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '提交下载任务失败'
    ElMessage.error(errorDetail)
  }
}

function buildDownloadItem(v: NonNullable<typeof store.result>['videos'][number]): DownloadItem {
  const selectedFormat = store.getSelectedFormat(v.id)!
  const fmt = v.formats.find(f => f.format_id === selectedFormat)
  return {
    video_id: v.id,
    format_id: selectedFormat,
    title: v.title,
    url: fmt?.is_direct_url ? fmt.url : null,
    thumbnail: v.thumbnail,
    webpage_url: v.webpage_url,
  }
}
</script>

<template>
  <div class="scrape-view">
    <header class="page-header">
      <div>
        <span class="eyebrow">Scrape</span>
        <h1>解析视频并加入下载队列</h1>
        <p>把链接交给解析器，选择需要的视频与格式，统一提交到下载管理。</p>
      </div>
      <el-button v-if="store.result" plain @click="store.clearResult">
        <el-icon><RefreshLeft /></el-icon>
        清空结果
      </el-button>
    </header>

    <UrlInput :loading="store.status === 'loading'" @scrape="handleScrape" />

    <!-- idle -->
    <div v-if="store.status === 'idle'" class="state-box">
      <div class="empty-panel">
        <el-icon><Link /></el-icon>
        <strong>等待链接</strong>
        <span>输入公开视频页面、播放列表或媒体直链后开始解析。</span>
      </div>
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
          <span class="source-pill">{{ store.result.platform }}</span>
          <div class="source-text">
            <span class="page-title">{{ store.result.page_title || store.result.source_url }}</span>
            <span class="count">{{ store.result.videos.length }} 个视频 · {{ totalFormats }} 个格式</span>
          </div>
        </div>
        <div class="results-actions">
          <el-button-group>
            <el-button plain :disabled="allSelected" @click="store.selectAllVideos">全选</el-button>
            <el-button plain :disabled="selectedVideos.length === 0" @click="store.clearVideoSelection">取消选择</el-button>
          </el-button-group>
          <el-button
            type="primary"
            :disabled="selectedVideos.length === 0"
            :loading="downloadStore.submitting"
            @click="handleDownloadSelected"
          >
            <el-icon><Download /></el-icon>
            下载选中 ({{ selectedVideos.length }})
          </el-button>
        </div>
      </div>

      <div class="selection-bar">
        <span>已选择 {{ selectedVideos.length }} / {{ store.result.videos.length }} 个视频</span>
        <el-progress
          :percentage="Math.round((selectedVideos.length / store.result.videos.length) * 100)"
          :show-text="false"
          :stroke-width="6"
        />
      </div>

      <div class="video-list">
        <VideoCard
          v-for="video in store.result.videos"
          :key="video.id"
          :video="video"
          :selected-format="store.getSelectedFormat(video.id)"
          :selected="store.isVideoSelected(video.id)"
          @select-format="(fid: string) => store.selectFormat(video.id, fid)"
          @toggle-selected="(selected: boolean) => store.setVideoSelected(video.id, selected)"
          @download="handleDownloadOne(video.id)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.scrape-view {
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.eyebrow {
  display: inline-block;
  margin-bottom: 8px;
  color: var(--brand);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.page-header h1 {
  margin: 0;
  color: var(--text-main);
  font-size: 28px;
  line-height: 1.3;
}

.page-header p {
  margin-top: 6px;
  color: var(--text-muted);
  font-size: 13px;
}

.state-box {
  margin-top: 18px;
}

.empty-panel {
  display: grid;
  place-items: center;
  min-height: 300px;
  padding: 42px 24px;
  color: var(--text-muted);
  text-align: center;
  background: var(--surface);
  border: 1px dashed var(--border-strong);
  border-radius: 16px;
}

.empty-panel .el-icon {
  margin-bottom: 14px;
  color: #98a2b3;
  font-size: 42px;
}

.empty-panel strong {
  color: var(--text-main);
  font-size: 16px;
}

.empty-panel span {
  margin-top: 6px;
  font-size: 13px;
}
.results {
  margin-top: 18px;
}
.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding: 14px;
  background: var(--surface);
  border-radius: 14px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow-soft);
}
.results-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  overflow: hidden;
}

.source-pill {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  color: #1d4ed8;
  font-size: 12px;
  font-weight: 700;
  background: var(--brand-soft);
  border-radius: 999px;
}

.source-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.results-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.selection-bar {
  display: grid;
  grid-template-columns: auto minmax(160px, 1fr);
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  padding: 10px 12px;
  color: var(--text-secondary);
  font-size: 13px;
  background: var(--brand-soft);
  border: 1px solid #bfdbfe;
  border-radius: 12px;
}

.page-title {
  font-size: 14px;
  color: var(--text-main);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.count {
  font-size: 12px;
  color: var(--text-muted);
  white-space: nowrap;
}
.video-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (max-width: 720px) {
  .page-header,
  .results-header {
    align-items: stretch;
    flex-direction: column;
  }

  .results-actions,
  .selection-bar {
    align-items: stretch;
    grid-template-columns: 1fr;
    flex-direction: column;
  }

  .results-info {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
