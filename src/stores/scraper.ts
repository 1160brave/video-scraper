// 爬取状态管理
import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import { scrapeUrl, type ScrapeResponse, type VideoInfo } from '@/services/api'

export const useScraperStore = defineStore('scraper', () => {
  const url = ref('')
  const status = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
  const result = ref<ScrapeResponse | null>(null)
  const error = ref<string | null>(null)
  const selectedFormats = reactive<Record<string, string>>({})

  async function scrape(inputUrl: string) {
    url.value = inputUrl
    status.value = 'loading'
    error.value = null
    result.value = null
    // clear selections
    Object.keys(selectedFormats).forEach(k => delete selectedFormats[k])

    try {
      const data = await scrapeUrl(inputUrl)
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
          const best = video.formats.find(f => f.has_audio && f.has_video && f.ext === 'mp4')
            ?? video.formats.find(f => f.has_audio && f.has_video)
            ?? video.formats[0]
          if (best) {
            selectedFormats[video.id] = best.format_id
          }
        }
      }
    } catch (e: any) {
      status.value = 'error'
      error.value = e?.message || '爬取失败，请检查链接或网络'
    }
  }

  function selectFormat(videoId: string, formatId: string) {
    selectedFormats[videoId] = formatId
  }

  function getSelectedFormat(videoId: string): string | undefined {
    return selectedFormats[videoId]
  }

  function clearResult() {
    status.value = 'idle'
    result.value = null
    error.value = null
    Object.keys(selectedFormats).forEach(k => delete selectedFormats[k])
  }

  return { url, status, result, error, selectedFormats, scrape, selectFormat, getSelectedFormat, clearResult }
})
