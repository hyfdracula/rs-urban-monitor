<template>
  <div class="gee-config-page" :class="{ mobile: isMobile }">
    <div class="config-card">
      <h2>🌍 GEE 账号配置</h2>
      <p class="desc">配置 Google Earth Engine 服务账号，解锁自动模式</p>

      <!-- Step 1: Register -->
      <div class="step-item" :class="{ done: hasKey }">
        <div class="step-num">1</div>
        <div class="step-body">
          <h4>注册 Google Earth Engine</h4>
          <p>需要 Google 账号，注册后可获得免费 GEE 使用权限</p>
          <a href="https://code.earthengine.google.com/register" target="_blank" class="step-link">
            <el-button size="small" type="primary" plain>前往注册</el-button>
          </a>
        </div>
      </div>

      <!-- Step 2: Service Account -->
      <div class="step-item" :class="{ done: hasKey }">
        <div class="step-num">2</div>
        <div class="step-body">
          <h4>创建服务账号</h4>
          <p>在 Google Cloud Console 创建服务账号并启用 Earth Engine API</p>
          <a href="https://console.cloud.google.com/apis/library/earthengine.googleapis.com" target="_blank" class="step-link">
            <el-button size="small" type="primary" plain>打开 Google Cloud</el-button>
          </a>
          <div class="tutorial-links">
            <a href="https://developers.google.com/earth-engine/guides/service_account" target="_blank">📖 官方教程</a>
          </div>
        </div>
      </div>

      <!-- Step 3: Upload Key -->
      <div class="step-item" :class="{ done: hasKey }">
        <div class="step-num">3</div>
        <div class="step-body">
          <h4>上传密钥文件</h4>
          <p>上传服务账号的 JSON 密钥文件（仅保存在本地浏览器中）</p>

          <div v-if="!hasKey" class="key-upload">
            <el-upload
              drag
              :auto-upload="false"
              :on-change="onKeyChange"
              accept=".json"
              :limit="1"
              :show-file-list="false"
              class="key-upload-area"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">拖拽 .json 密钥文件到此处</div>
              <div class="upload-hint">或点击选择文件</div>
            </el-upload>
          </div>

          <!-- Connected status -->
          <div v-else class="connected-box">
            <div class="connected-row">
              <el-icon color="#69DB7C"><CircleCheck /></el-icon>
              <span class="connected-label">已配置</span>
              <span class="connected-email">{{ accountEmail }}</span>
            </div>
            <div class="quota-bar">
              <div class="quota-label">
                <span>剩余配额</span>
                <span class="quota-value">{{ quotaUsed.toLocaleString() }} / {{ quotaTotal.toLocaleString() }} 秒</span>
              </div>
              <div class="quota-track">
                <div class="quota-fill" :style="{ width: quotaPercent + '%' }" />
              </div>
            </div>
            <el-button size="small" type="danger" text @click="removeKey">
              移除密钥
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- How it works -->
    <div class="info-card">
      <h3>💡 工作原理</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-icon">🔐</span>
          <div>
            <span class="info-title">密钥安全</span>
            <span class="info-desc">密钥仅保存在你的浏览器本地，不会上传到任何服务器</span>
          </div>
        </div>
        <div class="info-item">
          <span class="info-icon">⚡</span>
          <div>
            <span class="info-title">自动模式</span>
            <span class="info-desc">配置后即可使用自动模式，一键完成数据处理全流程</span>
          </div>
        </div>
        <div class="info-item">
          <span class="info-icon">📊</span>
          <div>
            <span class="info-title">免费配额</span>
            <span class="info-desc">GEE 免费版提供充足计算资源，适合学术研究使用</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { UploadFilled, CircleCheck } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const isMobile = ref(false)
const hasKey = ref(false)
const accountEmail = ref('')
const quotaUsed = ref(0)
const quotaTotal = ref(18000)

const quotaPercent = computed(() => {
  if (quotaTotal.value === 0) return 0
  return Math.round((quotaUsed.value / quotaTotal.value) * 100)
})

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadKeyFromStorage()
})

function loadKeyFromStorage() {
  try {
    const stored = localStorage.getItem('gee_service_account')
    if (stored) {
      const data = JSON.parse(stored)
      hasKey.value = true
      accountEmail.value = data.client_email || '未知账号'
      quotaUsed.value = data.quotaUsed || 2800
    }
  } catch {
    // no valid key
  }
}

function onKeyChange(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const keyData = JSON.parse(e.target.result)

      // Validate it looks like a service account key
      if (!keyData.client_email || !keyData.private_key) {
        ElMessage.error('无效的服务账号密钥文件，请检查是否为正确的 JSON 密钥')
        return
      }

      // Store in localStorage (browser only, never sent to server)
      const storeData = {
        client_email: keyData.client_email,
        project_id: keyData.project_id || '',
        private_key: keyData.private_key,
        quotaUsed: 2800,
        savedAt: new Date().toISOString(),
      }

      localStorage.setItem('gee_service_account', JSON.stringify(storeData))
      hasKey.value = true
      accountEmail.value = keyData.client_email
      quotaUsed.value = 2800

      ElMessage.success(`服务账号 ${keyData.client_email} 配置成功`)
    } catch {
      ElMessage.error('JSON 解析失败，请检查文件格式')
    }
  }
  reader.readAsText(file.raw)
}

function removeKey() {
  localStorage.removeItem('gee_service_account')
  hasKey.value = false
  accountEmail.value = ''
  quotaUsed.value = 0
  ElMessage.success('密钥已移除')
}
</script>

<style scoped>
.gee-config-page {
  height: 100%;
  overflow-y: auto;
  padding: 40px;
  background: #0d0d0d;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.config-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 32px;
  max-width: 520px;
  width: 100%;
}

.config-card h2 {
  color: #ddd;
  margin: 0 0 6px;
}

.desc {
  color: #888;
  font-size: 13px;
  margin: 0 0 24px;
}

/* Steps */
.step-item {
  display: flex;
  gap: 14px;
  padding: 16px 0;
  border-bottom: 1px solid #2a2a2a;
}

.step-item:last-child {
  border-bottom: none;
}

.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #2a2a2a;
  color: #888;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-item.done .step-num {
  background: rgba(105, 219, 124, 0.15);
  color: #69DB7C;
}

.step-body h4 {
  color: #ddd;
  margin: 0 0 4px;
  font-size: 14px;
}

.step-body p {
  color: #888;
  font-size: 12px;
  margin: 0 0 10px;
}

.step-link {
  text-decoration: none;
}

.tutorial-links {
  margin-top: 6px;
}

.tutorial-links a {
  color: #4DABF7;
  font-size: 12px;
  text-decoration: none;
}

.tutorial-links a:hover {
  text-decoration: underline;
}

/* Key upload */
.key-upload-area {
  border: 1px dashed #444;
  border-radius: 8px;
  background: #222;
  width: 100%;
}

.key-upload-area:hover { border-color: #666; }
.upload-icon { font-size: 28px; color: #555; }
.upload-text { color: #aaa; margin-top: 6px; font-size: 13px; }
.upload-hint { color: #555; font-size: 12px; margin-top: 4px; }

/* Connected */
.connected-box {
  background: rgba(105, 219, 124, 0.06);
  border: 1px solid rgba(105, 219, 124, 0.2);
  border-radius: 8px;
  padding: 14px;
}

.connected-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.connected-label {
  color: #69DB7C;
  font-size: 14px;
  font-weight: 500;
}

.connected-email {
  color: #888;
  font-size: 13px;
  margin-left: auto;
}

.quota-bar { margin-bottom: 10px; }
.quota-label {
  display: flex;
  justify-content: space-between;
  color: #888;
  font-size: 12px;
  margin-bottom: 6px;
}
.quota-value { color: #bbb; }

.quota-track {
  height: 6px;
  background: #333;
  border-radius: 3px;
  overflow: hidden;
}

.quota-fill {
  height: 100%;
  background: #4DABF7;
  border-radius: 3px;
  transition: width 0.5s;
}

/* Info card */
.info-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  max-width: 520px;
  width: 100%;
}

.info-card h3 {
  color: #ccc;
  margin: 0 0 16px;
  font-size: 15px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.info-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.info-icon { font-size: 20px; }

.info-title {
  color: #ddd;
  font-size: 13px;
  font-weight: 500;
  display: block;
}

.info-desc {
  color: #888;
  font-size: 12px;
  display: block;
  margin-top: 2px;
}

/* Mobile */
@media (max-width: 767px) {
  .gee-config-page {
    padding: 16px;
    gap: 16px;
  }

  .config-card,
  .info-card {
    max-width: 100%;
    padding: 20px;
    border-radius: 8px;
  }
}
</style>
