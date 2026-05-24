<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, selectFolder, selectCookieFile, saveSettings } from '@/services/api'
import { ElMessage } from 'element-plus'

const downloadDir = ref('')
const maxConcurrent = ref(3)
const ffmpegInstalled = ref(false)

const cookieMode = ref<'none' | 'browser' | 'file' | 'manual'>('none')
const cookieBrowser = ref('chrome')
const cookieManual = ref('')
const cookieFile = ref('')

const loading = ref(false)
const saving = ref(false)

const loadSettings = async () => {
  loading.value = true
  try {
    const settings = await getSettings()
    downloadDir.value = settings.download_dir
    maxConcurrent.value = settings.max_concurrent || 3
    ffmpegInstalled.value = settings.ffmpeg_installed || false
    
    cookieMode.value = settings.cookie_mode || 'none'
    cookieBrowser.value = settings.cookie_browser || 'chrome'
    cookieManual.value = settings.cookie_manual || ''
    cookieFile.value = settings.cookie_file || ''
  } catch (error: any) {
    ElMessage.error('加载系统设置失败')
  } finally {
    loading.value = false
  }
}

const handleSelectFolder = async () => {
  try {
    const settings = await selectFolder()
    downloadDir.value = settings.download_dir
    ElMessage.success('成功更改视频下载目录')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '选择文件夹失败'
    ElMessage.error(errorDetail)
  }
}

const handleSelectCookieFile = async () => {
  try {
    const res = await selectCookieFile()
    cookieFile.value = res.cookie_file
    ElMessage.success('成功选择 Cookies 文件')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '选择文件失败'
    ElMessage.error(errorDetail)
  }
}

const handleSaveSettings = async () => {
  if (!downloadDir.value.trim()) {
    ElMessage.warning('视频下载保存路径不能为空')
    return
  }
  
  if (cookieMode.value === 'file' && !cookieFile.value.trim()) {
    ElMessage.warning('已选择使用 Cookies 文件，但文件路径为空')
    return
  }

  if (cookieMode.value === 'manual' && !cookieManual.value.trim()) {
    ElMessage.warning('已选择手动输入 Cookie，但文本内容为空')
    return
  }

  saving.value = true
  try {
    await saveSettings({
      download_dir: downloadDir.value,
      max_concurrent: maxConcurrent.value,
      cookie_mode: cookieMode.value,
      cookie_browser: cookieBrowser.value,
      cookie_manual: cookieManual.value,
      cookie_file: cookieFile.value,
    })
    ElMessage.success('系统设置已成功保存并应用')
  } catch (error: any) {
    const errorDetail = error.response?.data?.detail || error.message || '保存设置失败'
    ElMessage.error(errorDetail)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<template>
  <div class="settings-view" v-loading="loading">
    <div class="header-section">
      <h2>系统设置</h2>
      <el-button type="primary" size="large" :loading="saving" @click="handleSaveSettings">
        <el-icon><CircleCheck /></el-icon>
        &nbsp;保存全部设置
      </el-button>
    </div>

    <!-- 1. 下载保存设置 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="icon blue"><FolderOpened /></el-icon>
          <span class="title">下载管理设置</span>
        </div>
      </template>
      <div class="card-body">
        <!-- 视频保存路径 -->
        <div class="setting-item">
          <span class="item-label">视频保存路径</span>
          <div class="input-row">
            <el-input
              v-model="downloadDir"
              placeholder="请选择或手动输入视频保存路径"
              class="dir-input"
              clearable
            />
            <el-button type="primary" @click="handleSelectFolder">
              <el-icon><Folder /></el-icon>
              &nbsp;选择文件夹
            </el-button>
          </div>
          <p class="settings-tip">
            提示：下载视频时将自动保存到此绝对路径。支持新建文件夹或输入网络/绝对路径。
          </p>
        </div>

        <el-divider />

        <!-- 最大并发数 -->
        <div class="setting-item">
          <span class="item-label">最大并发下载数</span>
          <div class="concurrency-control">
            <el-slider v-model="maxConcurrent" :min="1" :max="10" show-input style="width: 320px;" />
            <span class="tip-text">（推荐设置为 1~5。并发量过高可能会导致视频站点临时对您的 IP 进行限流或拉黑）</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 2. Cookie 与鉴权设置 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="icon orange"><Key /></el-icon>
          <span class="title">Cookie 与登录凭证 (支持解析/下载高清或私密视频)</span>
        </div>
      </template>
      <div class="card-body cookie-settings">
        <el-radio-group v-model="cookieMode" class="cookie-radio-group">
          <el-radio-button value="none">不使用 Cookie</el-radio-button>
          <el-radio-button value="browser">从浏览器自动提取</el-radio-button>
          <el-radio-button value="manual">手动输入 Cookie 文本</el-radio-button>
          <el-radio-button value="file">载入 cookies.txt 文件</el-radio-button>
        </el-radio-group>

        <!-- 详细选项渲染 -->
        <div class="cookie-detail-box">
          <!-- 1. 不使用 Cookie -->
          <div v-if="cookieMode === 'none'" class="mode-desc">
            <p><strong>当前模式：不使用任何 Cookie 凭证</strong></p>
            <p class="tip-text">
              适合爬取并下载完全公开的、不需要登录即可访问的视频。
              解析部分高清晰度视频（如 B站 1080P/4K、YouTube 某些限制级视频）时可能会由于未登录而失败，或只能下载 360P/480P 极低画质。
            </p>
          </div>

          <!-- 2. 浏览器提取 -->
          <div v-else-if="cookieMode === 'browser'" class="mode-form">
            <p class="section-title"><strong>选择您已登录对应视频网站的本地浏览器：</strong></p>
            <div class="select-row">
              <el-select v-model="cookieBrowser" placeholder="请选择本地浏览器" style="width: 260px;">
                <el-option label="Google Chrome" value="chrome" />
                <el-option label="Microsoft Edge" value="edge" />
                <el-option label="Apple Safari" value="safari" />
                <el-option label="Mozilla Firefox" value="firefox" />
                <el-option label="Brave Browser" value="brave" />
                <el-option label="Opera" value="opera" />
                <el-option label="Chromium" value="chromium" />
              </el-select>
            </div>
            <p class="tip-text">
              <strong>✨ 极力推荐此方式！</strong> 启动视频爬取和下载时，后端解析引擎将自动从您选择的本地浏览器中安全、实时读取对应的网站 Cookie 凭证，<strong>无需用户手动复制或下载任何插件</strong>。
              <br/>
              <em>提示：请确保在进行解析/下载前，您已在所选浏览器中正常登录了对应的视频站点。Windows 无弹窗提示；macOS 可能会弹出钥匙串密码框以授权解密，请选择“始终允许”。</em>
            </p>
          </div>

          <!-- 3. 手动输入 -->
          <div v-else-if="cookieMode === 'manual'" class="mode-form">
            <p class="section-title"><strong>请在下方粘贴您的 Cookie 原始字符串：</strong></p>
            <el-input
              v-model="cookieManual"
              type="textarea"
              :rows="4"
              placeholder="例如：SESSDATA=xxx; jct=xxx; DedeUserID=xxx; ... 或直接从浏览器请求头 (Request Headers) 复制出的完整 Cookie"
            />
            <p class="tip-text">
              手动输入您获取到的特定视频站点的 Cookie 键值对字符串（支持多域名混合）。
              <br/>
              <em>获取方法：在浏览器中打开对应网站并登录，按 F12 打开开发者工具 → 切换到「网络(Network)」标签 → 刷新网页 → 点击任意当前域名的请求 → 在「请求头(Request Headers)」中找到 `Cookie` 项，复制其全部右侧的值并粘贴到上方。</em>
            </p>
          </div>

          <!-- 4. cookies.txt 文件 -->
          <div v-else-if="cookieMode === 'file'" class="mode-form">
            <p class="section-title"><strong>选择本地 Netscape 格式的 cookies.txt 文件：</strong></p>
            <div class="input-row">
              <el-input
                v-model="cookieFile"
                placeholder="请选择或手动输入 Netscape cookies.txt 文件绝对路径"
                class="dir-input"
                clearable
              />
              <el-button type="primary" @click="handleSelectCookieFile">
                <el-icon><Document /></el-icon>
                &nbsp;选择 Cookies 文件
              </el-button>
            </div>
            <p class="tip-text">
              Netscape（网景）格式的 cookies.txt 是传统的命令行工具最喜爱的鉴权方式。
              <br/>
              <em>获取方法：在您已登录视频网站的浏览器中安装如「Get cookies.txt LOCALLY」(Chrome/Edge 插件) 或类似插件，登录后点击插件一键“Export to txt”下载，然后在这里选择该文件即可。</em>
            </p>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 3. 系统环境与诊断 -->
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <el-icon class="icon green"><Cpu /></el-icon>
          <span class="title">系统诊断与依赖环境</span>
        </div>
      </template>
      <div class="card-body system-diagnostics">
        <div class="diagnostic-item">
          <span class="diag-label">FFmpeg 运行时状态</span>
          <div class="diag-status">
            <el-tag v-if="ffmpegInstalled" type="success" effect="dark" class="status-tag">
              <el-icon><CircleCheck /></el-icon>&nbsp;已检测到
            </el-tag>
            <el-tag v-else type="warning" effect="dark" class="status-tag">
              <el-icon><Warning /></el-icon>&nbsp;未检测到
            </el-tag>
            
            <span class="diag-desc">
              <span v-if="ffmpegInstalled">
                系统已安装并配置好 FFmpeg 环境。本工具已完美解锁 **音视频高清合成** 功能，支持无损合并并下载 1080P、2K、4K 及以上所有最高清晰度视频。
              </span>
              <span v-else class="warning-text">
                未检测到 FFmpeg 运行时。下载 YouTube/Bilibili 等高清视频时，由于视频和音频流是分离开的，<strong>缺少 FFmpeg 将无法合并，导致最高只能下载 720P/480P 画质的合并版视频</strong>。
              </span>
            </span>
          </div>
        </div>
        
        <!-- FFmpeg 安装指引 -->
        <div v-if="!ffmpegInstalled" class="ffmpeg-guide">
          <p class="guide-title"><strong>💡 如何快速安装 FFmpeg？</strong></p>
          <div class="guide-content">
            <div class="platform-column">
              <p class="guide-platform"><strong>🖥️ Windows 平台：</strong></p>
              <ol>
                <li>按下键盘 `Win + R` 键，输入 `cmd` 打开命令行。</li>
                <li>运行命令：<code>winget install Gyan.FFmpeg</code> 即可全自动安装并配好环境变量。</li>
                <li>或者访问 <a href="https://ffmpeg.org/download.html" target="_blank">FFmpeg 官网</a> 下载压缩包，解压后将 `bin` 路径手动加入到系统环境变量 `Path` 中。</li>
              </ol>
            </div>
            <div class="platform-column">
              <p class="guide-platform"><strong>🍏 macOS 平台：</strong></p>
              <ol>
                <li>打开终端 (Terminal)。</li>
                <li>如果您已安装 Homebrew，直接运行：<code>brew install ffmpeg</code> 即可一键极速配置完毕。</li>
                <li>安装完成后重启本视频爬取工具，此状态即可变为“已检测到”。</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <div class="bottom-action">
      <el-button type="success" size="large" :loading="saving" @click="handleSaveSettings" style="width: 200px;">
        <el-icon><Check /></el-icon>
        &nbsp;保存系统配置
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  max-width: 900px;
  margin: 0 auto;
}
h2 {
  font-size: 20px;
  margin: 0;
}
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.settings-card {
  margin-bottom: 24px;
  border-radius: 8px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-header .icon {
  font-size: 18px;
}
.card-header .icon.blue {
  color: #409eff;
}
.card-header .icon.orange {
  color: #e6a23c;
}
.card-header .icon.green {
  color: #67c23a;
}
.card-header .title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.card-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0;
}
.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.item-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}
.concurrency-control {
  display: flex;
  align-items: center;
  gap: 16px;
}
.input-row {
  display: flex;
  gap: 12px;
  width: 100%;
}
.dir-input {
  flex: 1;
}
.settings-tip {
  font-size: 12px;
  color: #909399;
  margin: 4px 0 0 0;
}
.cookie-settings {
  gap: 16px;
}
.cookie-radio-group {
  margin-bottom: 4px;
}
.cookie-detail-box {
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 6px;
  border: 1px dashed #dcdfe6;
}
.mode-desc p, .mode-form p {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}
.section-title {
  margin-bottom: 12px !important;
}
.select-row {
  margin-bottom: 12px;
}
.tip-text {
  font-size: 12px !important;
  color: #82848a !important;
  line-height: 1.6;
  margin: 8px 0 0 0 !important;
}
.system-diagnostics {
  gap: 16px;
}
.diagnostic-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.diag-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}
.diag-status {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.status-tag {
  flex-shrink: 0;
  padding: 6px 12px;
  font-size: 13px;
}
.diag-desc {
  font-size: 13px;
  color: #5a5e66;
  line-height: 1.6;
}
.warning-text {
  color: #e6a23c;
  font-weight: 500;
}
.ffmpeg-guide {
  padding: 16px;
  background-color: #fffaf0;
  border: 1px solid #fdf6ec;
  border-radius: 6px;
}
.guide-title {
  font-size: 13px;
  color: #e6a23c;
  margin: 0 0 12px 0;
}
.guide-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.guide-platform {
  font-size: 13px;
  color: #303133;
  margin: 0 0 8px 0;
}
.guide-content ol {
  margin: 0;
  padding-left: 18px;
  font-size: 12px;
  color: #606266;
  line-height: 1.7;
}
.guide-content ol code {
  background-color: #f4f4f5;
  color: #303133;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}
.guide-content a {
  color: #409eff;
  text-decoration: none;
}
.guide-content a:hover {
  text-decoration: underline;
}
.bottom-action {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  margin-bottom: 60px;
}
</style>
