<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSettings, selectFolder, selectCookieFile, saveSettings } from '@/services/api'
import { ElMessage } from 'element-plus'

const downloadDir = ref('')
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
          <span class="title">下载保存设置</span>
        </div>
      </template>
      <div class="card-body">
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
              <strong>✨ 极力推荐此方式！</strong> 启动视频爬取和下载时，后端解析引擎将自动从您选择 the 本地浏览器中安全、实时读取对应的网站 Cookie 凭证，<strong>无需用户手动复制或下载任何插件</strong>。
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
.card-header .title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
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
.bottom-action {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  margin-bottom: 60px;
}
</style>
