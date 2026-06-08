<template>
  <div class="auto-wizard">
    <div class="wizard-header">
      <el-button text size="small" @click="$emit('back')">
        <el-icon><ArrowLeft /></el-icon>
        返回模式选择
      </el-button>
      <h3 class="wizard-title">自动模式 — 一键分析</h3>
    </div>

    <!-- Step 1: Upload boundary -->
    <div v-if="step === 'upload'" class="step-content">
      <h4 class="step-title">上传研究区边界</h4>
      <p class="step-desc">上传 GeoJSON / Shapefile / GeoTIFF 边界文件</p>

      <el-input
        v-model="boundaryName"
        placeholder="边界名称，如：上海市"
        class="name-input"
      />

      <el-upload
        drag
        :auto-upload="false"
        :on-change="onFileChange"
        accept=".geojson,.json,.zip,.tif,.tiff"
        :limit="1"
        :show-file-list="false"
        class="boundary-upload"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">{{ selectedFile ? selectedFile.name : '拖拽文件到此处' }}</div>
        <div class="upload-hint">支持 .geojson .json .zip .tif</div>
      </el-upload>

      <el-button
        type="primary"
        class="start-btn"
        :loading="uploading"
        :disabled="!selectedFile || !boundaryName"
        @click="startCompute"
      >
        {{ uploading ? '上传中...' : '开始一键分析' }}
      </el-button>
    </div>

    <!-- Step 2: Polling progress -->
    <div v-else-if="step === 'processing'" class="step-content">
      <h4 class="step-title">分析计算中...</h4>
      <p class="step-desc">后端正在使用你的 GEE 密钥进行计算</p>

      <div class="progress-section">
        <div class="progress-bar-track">
          <div class="progress-bar-fill" :style="{ width: progress + '%' }" />
        </div>
        <div class="progress-label">
          <span>{{ progress }}%</span>
          <span>{{ completedTasks }} / {{ totalTasks }} 完成</span>
        </div>
      </div>

      <div class="task-details" v-if="taskDetails.length">
        <div v-for="t in taskDetails" :key="t.type" class="task-row">
          <span class="task-name">{{ t.type }}</span>
          <span class="task-state" :class="t.state.toLowerCase()">
            {{ stateLabel(t.state) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Step 3: Done -->
    <div v-else-if="step === 'done'" class="step-content">
      <div class="done-box">
        <el-icon color="#69DB7C" :size="48"><CircleCheck /></el-icon>
        <h4>分析完成！</h4>
        <p>WMS 图层已自动发布到 GeoServer，可在地图上查看</p>
      </div>

      <div class="wms-layers" v-if="wmsUrls">
        <h5>已生成图层</h5>
        <div v-for="(url, key) in wmsUrls" :key="key" class="wms-row">
          <span class="wms-name">{{ key }}</span>
          <el-tag size="small" type="success">WMS</el-tag>
        </div>
      </div>

      <div class="done-actions">
        <el-button type="primary" @click="$emit('done', { taskId, wmsUrls, url: analysisUrl })">
          查看分析报告
        </el-button>
        <el-button @click="$emit('back')">
          返回
        </el-button>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="step === 'error'" class="step-content">
      <div class="done-box error">
        <el-icon color="#FF6B6B" :size="48"><CircleClose /></el-icon>
        <h4>分析失败</h4>
        <p>{{ errorMsg }}</p>
      </div>
      <el-button @click="step = 'upload'; reset()">重试</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ArrowLeft, UploadFilled, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { uploadBoundary, getComputeStatus } from '../../api'

defineEmits(['back', 'done'])

const step = ref('upload') // upload | processing | done | error
const boundaryName = ref('')
const selectedFile = ref(null)
const uploading = ref(false)
const taskId = ref('')
const analysisUrl = ref('')
const progress = ref(0)
const completedTasks = ref(0)
const totalTasks = ref(0)
const taskDetails = ref([])
const wmsUrls = ref(null)
const errorMsg = ref('')
let pollTimer = null

function onFileChange(file) {
  selectedFile.value = file
}

async function startCompute() {
  if (!selectedFile.value || !boundaryName.value) return

  uploading.value = true
  try {
    const data = await uploadBoundary(
      selectedFile.value.raw,
      boundaryName.value,
      'online',
      (e) => { /* upload progress */ }
    )
    taskId.value = data.task_id
    analysisUrl.value = data.url || `/analysis/${data.task_id}`
    step.value = 'processing'
    startPolling()
  } catch (err) {
    const detail = err.response?.data?.detail
    if (detail) {
      ElMessage.error(detail)
    } else {
      ElMessage.error('上传失败')
    }
    step.value = 'error'
    errorMsg.value = detail || '上传失败，请检查网络连接'
  }
  uploading.value = false
}

function startPolling() {
  pollTimer = setInterval(async () => {
    try {
      const data = await getComputeStatus(taskId.value)
      progress.value = data.progress || 0
      completedTasks.value = data.completed_tasks || 0
      totalTasks.value = data.total_tasks || 0
      taskDetails.value = data.details || []

      if (data.status === 'completed') {
        clearInterval(pollTimer)
        wmsUrls.value = data.wms_urls
        step.value = 'done'
      } else if (data.status === 'failed') {
        clearInterval(pollTimer)
        step.value = 'error'
        errorMsg.value = '计算任务失败，请检查 GEE 密钥是否有效'
      }
    } catch {
      clearInterval(pollTimer)
      step.value = 'error'
      errorMsg.value = '无法连接后端服务'
    }
  }, 3000)
}

function stateLabel(state) {
  const map = { COMPLETED: '✓ 完成', RUNNING: '⏳ 运行中', PENDING: '等待中', FAILED: '✗ 失败' }
  return map[state] || state
}

function reset() {
  step.value = 'upload'
  selectedFile.value = null
  boundaryName.value = ''
  progress.value = 0
  wmsUrls.value = null
  taskId.value = ''
  analysisUrl.value = ''
}
</script>

<style scoped>
.auto-wizard { max-width: 560px; margin: 0 auto; }

.wizard-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
}
.wizard-title { color: #ddd; margin: 0; font-size: 15px; }

.step-content { padding: 8px 0; }
.step-title { color: #ddd; margin: 0 0 6px; font-size: 15px; }
.step-desc { color: #888; font-size: 13px; margin: 0 0 16px; }

.name-input { margin-bottom: 14px; }

.boundary-upload {
  border: 1px dashed #444; border-radius: 8px; background: #222; width: 100%;
  margin-bottom: 16px;
}
.boundary-upload:hover { border-color: #666; }
.upload-icon { font-size: 32px; color: #555; }
.upload-text { color: #aaa; margin-top: 6px; font-size: 13px; }
.upload-hint { color: #555; font-size: 12px; margin-top: 4px; }

.start-btn { width: 100%; }

/* Progress */
.progress-section { margin: 16px 0; }
.progress-bar-track {
  height: 8px; background: #333; border-radius: 4px; overflow: hidden;
}
.progress-bar-fill {
  height: 100%; background: #BE4BDB; border-radius: 4px;
  transition: width 0.5s;
}
.progress-label {
  display: flex; justify-content: space-between; color: #888;
  font-size: 12px; margin-top: 6px;
}

.task-details { margin-top: 12px; }
.task-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 6px 0; border-bottom: 1px solid #2a2a2a; font-size: 12px;
}
.task-name { color: #bbb; }
.task-state { font-size: 11px; }
.task-state.completed { color: #69DB7C; }
.task-state.running { color: #FFD43B; }
.task-state.failed { color: #FF6B6B; }
.task-state.pending { color: #666; }

/* Done */
.done-box {
  text-align: center; padding: 24px;
  background: rgba(105, 219, 124, 0.06); border: 1px solid rgba(105, 219, 124, 0.2);
  border-radius: 12px; margin-bottom: 16px;
}
.done-box.error {
  background: rgba(255, 107, 107, 0.06); border-color: rgba(255, 107, 107, 0.2);
}
.done-box h4 { color: #ddd; margin: 12px 0 4px; }
.done-box p { color: #888; font-size: 13px; margin: 0; }

.wms-layers {
  background: #1a1a1a; border: 1px solid #333; border-radius: 8px;
  padding: 12px; margin-bottom: 16px;
}
.wms-layers h5 { color: #ccc; margin: 0 0 8px; font-size: 13px; }
.wms-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 4px 0; border-bottom: 1px solid #2a2a2a;
}
.wms-name { color: #bbb; font-size: 12px; }

.done-actions { display: flex; gap: 10px; justify-content: center; }
</style>
