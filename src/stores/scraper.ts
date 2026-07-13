// 爬取状态管理
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { getSettings, scrapeUrl, type ScrapeResponse, type VideoFormat } from '@/services/api'

export const useScraperStore = defineStore('scraper', () => {
  const url = ref('')
  const status = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
  const result = ref<ScrapeResponse | null>(null)
  const error = ref<string | null>(null)
  const selectedFormats = reactive<Record<string, string>>({})
  const selectedVideos = reactive<Record<string, boolean>>({})
  const ffmpegInstalled = ref(true)
  let scrapeRequestId = 0

  async function scrape(inputUrl: string) {
    const requestId = ++scrapeRequestId
    url.value = inputUrl.trim()
    status.value = 'loading'
    error.value = null
    result.value = null
    // clear selections
    Object.keys(selectedFormats).forEach(k => delete selectedFormats[k])
    Object.keys(selectedVideos).forEach(k => delete selectedVideos[k])

    try {
      try {
        const settings = await getSettings()
        ffmpegInstalled.value = settings.ffmpeg_installed
      } catch {
        ffmpegInstalled.value = true
      }

      const data = await scrapeUrl(url.value)
      if (requestId !== scrapeRequestId) return

      result.value = data
      if (data.error) {
        status.value = 'error'
        error.value = data.error
      } else if (data.videos.length === 0) {
        status.value = 'error'
        error.value = '未找到任何视频'
      } else {
        status.value = 'success'
        // auto-select best format for each video
        for (const video of data.videos) {
          const best = [...video.formats].sort((a, b) => formatScore(b, ffmpegInstalled.value) - formatScore(a, ffmpegInstalled.value))[0]
          if (best) {
            selectedFormats[video.id] = best.format_id
            selectedVideos[video.id] = true
          }
        }
      }
    } catch (e: any) {
      if (requestId !== scrapeRequestId) return
      status.value = 'error'
      error.value = e?.message || '爬取失败，请检查链接或网络'
    }
  }

  function selectFormat(videoId: string, formatId: string) {
    selectedFormats[videoId] = formatId
    selectedVideos[videoId] = true
  }

  function getSelectedFormat(videoId: string): string | undefined {
    return selectedFormats[videoId]
  }

  function setVideoSelected(videoId: string, selected: boolean) {
    selectedVideos[videoId] = selected
  }

  function isVideoSelected(videoId: string): boolean {
    return selectedVideos[videoId] ?? false
  }

  function selectAllVideos() {
    for (const video of result.value?.videos ?? []) {
      if (selectedFormats[video.id]) {
        selectedVideos[video.id] = true
      }
    }
  }

  function clearVideoSelection() {
    Object.keys(selectedVideos).forEach(k => {
      selectedVideos[k] = false
    })
  }

  function clearResult() {
    status.value = 'idle'
    result.value = null
    error.value = null
    Object.keys(selectedFormats).forEach(k => delete selectedFormats[k])
    Object.keys(selectedVideos).forEach(k => delete selectedVideos[k])
  }

  return {
    url,
    status,
    result,
    error,
    ffmpegInstalled,
    selectedFormats,
    selectedVideos,
    scrape,
    selectFormat,
    getSelectedFormat,
    setVideoSelected,
    isVideoSelected,
    selectAllVideos,
    clearVideoSelection,
    clearResult,
  }
})

function formatScore(format: VideoFormat, canMerge: boolean): number {
  const resolution = format.resolution || format.format_note || ''
  const height = Number(resolution.match(/(\d{3,4})p?/)?.[1] || 0)
  const extensionBonus = format.ext === 'mp4' ? 100 : 0
  const avBonus = format.has_audio && format.has_video ? 1000 : 0
  const directBonus = format.is_direct_url ? 20 : 0
  const mergePenalty = !canMerge && format.format_id.includes('+') ? -10_000 : 0
  return avBonus + height + extensionBonus + directBonus + mergePenalty
}
