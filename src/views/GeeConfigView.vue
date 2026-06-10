<template>
  <div class="gee-config-page" :class="{ mobile: isMobile }">
    <div class="config-card">
      <h2>🌍 GEE 账号配置</h2>
      <p class="desc">配置 Google Earth Engine 服务账号，解锁自动模式</p>

      <!-- Step 1 -->
      <div class="step-item" :class="{ done: keyStatus === 'valid' }">
        <div class="step-num">1</div>
        <div class="step-body">
          <h4>注册 Google Earth Engine</h4>
          <p>需要 Google 账号，注册后可获得免费 GEE 使用权限</p>
          <a href="https://code.earthengine.google.com/register" target="_blank" rel="noopener noreferrer">
            <el-button size="small" type="primary" plain>前往注册</el-button>
          </a>
        </div>
      </div>

      <!-- Step 2 -->
      <div class="step-item" :class="{ done: keyStatus === 'valid' }">
        <div class="step-num">2</div>
        <div class="step-body">
          <h4>创建服务账号</h4>
          <p>在 Google Cloud Console 创建服务账号并启用 Earth Engine API</p>
          <div class="btn-row">
            <a href="https://console.cloud.google.com/apis/library/earthengine.googleapis.com" target="_blank" rel="noopener noreferrer">
              <el-button size="small" type="primary" plain>打开 Google Cloud</el-button>
            </a>
            <button class="tutorial-btn" @click="showTutorial = true">📖 密钥获取教程</button>
          </div>
        </div>
      </div>

      <!-- Step 3 -->
      <div class="step-item" :class="{ done: keyStatus === 'valid' }">
        <div class="step-num">3</div>
        <div class="step-body">
          <h4>上传密钥文件</h4>
          <p>上传服务账号的 JSON 密钥文件</p>

          <!-- No key: show upload -->
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

          <!-- Has key: show status -->
          <div v-else class="connected-box">
            <div class="connected-row">
              <el-icon v-if="keyStatus === 'valid'" color="#69DB7C"><CircleCheck /></el-icon>
              <el-icon v-else-if="keyStatus === 'invalid'" color="#FF6B6B"><CircleClose /></el-icon>
              <el-icon v-else color="#FFD43B"><Clock /></el-icon>
              <span class="connected-label" :class="keyStatus">
                {{ statusLabel }}
              </span>
              <span class="connected-email">{{ accountEmail }}</span>
            </div>

            <!-- Verify button -->
            <div v-if="keyStatus !== 'valid'" class="verify-row">
              <el-button
                size="small"
                type="primary"
                :loading="verifying"
                @click="verifyKey"
              >
                {{ verifying ? '验证中...' : '验证密钥' }}
              </el-button>
              <span v-if="keyStatus === 'invalid'" class="verify-hint">密钥无效，请重新上传</span>
            </div>

            <!-- Quota -->
            <div v-if="keyStatus === 'valid'" class="quota-bar">
              <div class="quota-label">
                <span>今日使用</span>
                <span class="quota-value">{{ quotaInfo }}</span>
              </div>
            </div>

            <el-button size="small" type="danger" text @click="removeKey" :loading="removing">
              删除密钥
            </el-button>
          </div>
        </div>
      </div>

      <!-- Info -->
      <div class="info-box">
        <div class="info-item">
          <span>🔐</span>
          <span>密钥保存在后端服务器，前端不存储敏感信息</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Tutorial Dialog -->
  <GeeTutorialDialog v-model="showTutorial" />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { UploadFilled, CircleCheck, CircleClose, Clock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { saveGeeKey, verifyGeeKey, getGeeKeyStatus, deleteGeeKey, getSystemQuota } from '../api'
import GeeTutorialDialog from '../components/dialog/GeeTutorialDialog.vue'

const isMobile = ref(false)
const hasKey = ref(false)
const showTutorial = ref(false)
const keyStatus = ref(null) // null | 'unverified' | 'valid' | 'invalid'
const accountEmail = ref('')
const quotaUsed = ref(0)
const verifying = ref(false)
const removing = ref(false)

const statusLabel = computed(() => {
  const map = { unverified: '未验证', valid: '已验证', invalid: '验证失败' }
  return map[keyStatus.value] || '未知'
})

const quotaInfo = computed(() => {
  if (!quotaUsed.value && quotaUsed.value !== 0) return 'GEE 无硬性配额限制'
  return `今日 ${quotaUsed.value} 次`
})

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  loadStatus()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

async function loadStatus() {
  try {
    const data = await getGeeKeyStatus()
    hasKey.value = data.has_key
    keyStatus.value = data.status
    accountEmail.value = data.service_account || ''

    if (data.has_key) {
      try {
        const q = await getSystemQuota()
        quotaUsed.value = q.used_today || 0
      } catch {
        quotaUsed.value = 0
      }
    }
  } catch {
    hasKey.value = false
    keyStatus.value = null
  }
}

async function onKeyChange(file) {
  const reader = new FileReader()
  reader.onload = async (e) => {
    try {
      const keyData = JSON.parse(e.target.result)
      if (!keyData.client_email || !keyData.private_key) {
        ElMessage.error('无效的服务账号密钥文件')
        return
      }

      await saveGeeKey(keyData.client_email, keyData)
      hasKey.value = true
      keyStatus.value = 'unverified'
      accountEmail.value = keyData.client_email
      ElMessage.success('密钥上传成功')

      await verifyKey()
    } catch (err) {
      ElMessage.error(err.response?.data?.detail || '上传失败')
    }
  }
  reader.readAsText(file.raw)
}

async function verifyKey() {
  verifying.value = true
  try {
    const data = await verifyGeeKey()
    keyStatus.value = data.status
    if (data.success) {
      ElMessage.success('GEE 密钥验证成功！')
      window.dispatchEvent(new CustomEvent('gee-status-changed'))
    } else {
      ElMessage.error(data.message || '验证失败')
    }
  } catch (err) {
    keyStatus.value = 'invalid'
    ElMessage.error(err.response?.data?.message || '验证失败')
  }
  verifying.value = false
}

async function removeKey() {
  removing.value = true
  try {
    await deleteGeeKey()
    hasKey.value = false
    keyStatus.value = null
    accountEmail.value = ''
    quotaUsed.value = 0
    ElMessage.success('密钥已删除')
    window.dispatchEvent(new CustomEvent('gee-status-changed'))
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '删除失败')
  }
  removing.value = false
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
  margin: 0 0 18px;
}

/* Steps */
.step-item {
  display: flex;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid #2a2a2a;
}

.step-item:last-of-type {
  border-bottom: none;
}

.step-num {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #2a2a2a;
  color: #888;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-item.done .step-num {
  background: rgba(105, 219, 124, 0.15);
  color: #69DB7C;
}

.step-body h4 {
  color: #ddd;
  margin: 0 0 3px;
  font-size: 13px;
}

.step-body p {
  color: #888;
  font-size: 12px;
  margin: 0 0 8px;
}

.btn-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tutorial-btn {
  color: #4DABF7;
  font-size: 12px;
  cursor: pointer;
  background: none;
  border: none;
  padding: 0;
  transition: color 0.2s;
}

.tutorial-btn:hover {
  color: #74C0FC;
  text-decoration: underline;
}

/* Key upload */
.key-upload-area {
  border: 1px dashed #444;
  border-radius: 8px;
  background: #222;
  width: 100%;
}

.key-upload-area:hover {
  border-color: #666;
}

.upload-icon {
  font-size: 28px;
  color: #555;
}

.upload-text {
  color: #aaa;
  margin-top: 6px;
  font-size: 13px;
}

.upload-hint {
  color: #555;
  font-size: 12px;
  margin-top: 4px;
}

/* Connected */
.connected-box {
  background: rgba(105, 219, 124, 0.06);
  border: 1px solid rgba(105, 219, 124, 0.2);
  border-radius: 8px;
  padding: 12px;
}

.connected-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.connected-label {
  font-size: 13px;
  font-weight: 500;
}

.connected-label.valid {
  color: #69DB7C;
}

.connected-label.unverified {
  color: #FFD43B;
}

.connected-label.invalid {
  color: #FF6B6B;
}

.connected-email {
  color: #888;
  font-size: 12px;
  margin-left: auto;
}

.verify-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.verify-hint {
  color: #FF6B6B;
  font-size: 11px;
}

.quota-bar {
  margin-bottom: 8px;
}

.quota-label {
  display: flex;
  justify-content: space-between;
  color: #888;
  font-size: 11px;
}

.quota-value {
  color: #bbb;
}

/* Info */
.info-box {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #2a2a2a;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  font-size: 11px;
  padding: 3px 0;
}

/* Mobile */
@media (max-width: 767px) {
  .gee-config-page {
    padding: 16px;
  }

  .config-card {
    max-width: 100%;
    padding: 20px;
    border-radius: 8px;
  }
}
</style>
