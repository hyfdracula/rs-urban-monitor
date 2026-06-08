<template>
  <div class="upload-page" :class="{ mobile: isMobile }">
    <!-- Mode Selection (default) -->
    <ModeSelection v-if="!currentMode" @select="currentMode = $event" />

    <!-- Manual Mode Wizard -->
    <div v-else-if="currentMode === 'manual'" class="mode-content">
      <ManualModeWizard @back="currentMode = null" />
    </div>

    <!-- Auto Mode Wizard -->
    <div v-else-if="currentMode === 'auto'" class="mode-content">
      <AutoModeWizard @back="currentMode = null" @done="onAutoDone" />
    </div>

    <!-- GeoServer Upload (existing) -->
    <template v-else-if="currentMode === 'geoserver'">
      <div class="upload-card">
        <div class="card-header">
          <el-button text size="small" @click="currentMode = null">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <h2>数据上传</h2>
        </div>
        <p class="desc">上传 GeoTIFF 或 Shapefile 至 GeoServer 发布为 WMS 服务</p>

        <el-upload
          class="upload-area"
          drag
          :auto-upload="false"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          :file-list="fileList"
          accept=".tif,.tiff,.zip"
          :limit="5"
        >
          <el-icon class="upload-icon"><UploadFilled /></el-icon>
          <div class="upload-text">拖拽文件到此处 或 点击选择</div>
          <div class="upload-hint">支持 .tif .tiff .zip (含 .shp)</div>
        </el-upload>

        <div class="file-list" v-if="fileList.length">
          <div v-for="f in fileList" :key="f.uid" class="file-item">
            <span class="file-name">{{ f.name }}</span>
            <span class="file-size">{{ formatSize(f.size) }}</span>
            <el-tag v-if="getFileType(f.name)" size="small" :type="getFileTag(f.name)">
              {{ getFileType(f.name) }}
            </el-tag>
          </div>
        </div>

        <el-button
          type="primary"
          :loading="uploading"
          :disabled="fileList.length === 0"
          @click="startUpload"
          class="upload-btn"
        >
          {{ uploading ? '上传中...' : '上传并发布' }}
        </el-button>

        <!-- Progress bars -->
        <div v-if="uploadTasks.length" class="progress-list">
          <div v-for="t in uploadTasks" :key="t.id" class="progress-item">
            <div class="progress-info">
              <span class="progress-name">{{ t.name }}</span>
              <span class="progress-status" :class="t.status">
                {{ statusText(t.status) }}
              </span>
            </div>
            <div v-if="t.status === 'uploading'" class="progress-bar">
              <div class="progress-fill" :style="{ width: t.progress + '%' }" />
            </div>
          </div>
        </div>
      </div>

      <!-- Published layers list -->
      <div class="layers-card">
        <h3>已发布图层</h3>
        <el-button size="small" text @click="refreshLayers">
          <el-icon><Refresh /></el-icon>
          <span>刷新</span>
        </el-button>

        <div v-if="loadingLayers" class="layers-loading">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>

        <div v-else-if="publishedLayers.length === 0" class="layers-empty">
          暂无已发布图层
        </div>

        <div v-else class="layers-list">
          <div v-for="layer in publishedLayers" :key="layer.name" class="layer-item">
            <span class="layer-name">{{ layer.name }}</span>
            <el-tag size="small" :type="layer.type === 'raster' ? 'warning' : 'success'">
              {{ layer.type === 'raster' ? '栅格' : '矢量' }}
            </el-tag>
            <el-button
              size="small"
              type="danger"
              text
              @click="deleteLayer(layer)"
              :loading="layer.deleting"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, UploadFilled, Refresh, Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import {
  uploadGeoTIFF,
  uploadShapefile,
  listCoverageStores,
  listDataStores,
  deleteCoverageStore,
  deleteLayer as deleteVectorLayer,
} from '../utils/geoserverRest'
import { GEOSERVER_CONFIG } from '../config/map'
import ModeSelection from '../components/upload/ModeSelection.vue'
import ManualModeWizard from '../components/upload/ManualModeWizard.vue'
import AutoModeWizard from '../components/upload/AutoModeWizard.vue'

const currentMode = ref(null) // null | 'manual' | 'auto' | 'geoserver'
const fileList = ref([])
const uploading = ref(false)
const uploadTasks = ref([])
const publishedLayers = ref([])
const loadingLayers = ref(false)
const isMobile = ref(false)

const WORKSPACE = GEOSERVER_CONFIG.workspace
const router = useRouter()

function onAutoDone({ taskId, wmsUrls, url }) {
  ElMessage.success(`分析完成！已生成 ${Object.keys(wmsUrls || {}).length} 个图层`)
  router.push(url || `/analysis/${taskId}`)
}

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  refreshLayers()
})

function onFileChange(file) {
  const ext = file.name.toLowerCase().split('.').pop()
  if (!['tif', 'tiff', 'zip'].includes(ext)) {
    ElMessage.error('只支持 .tif/.tiff/.zip 文件')
    return false
  }
  fileList.value.push(file)
  return true
}

function onFileRemove(file) {
  const idx = fileList.value.findIndex(f => f.uid === file.uid)
  if (idx >= 0) fileList.value.splice(idx, 1)
}

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function getFileType(name) {
  const ext = name.toLowerCase().split('.').pop()
  if (['tif', 'tiff'].includes(ext)) return '栅格'
  if (ext === 'zip') return '矢量'
  return null
}

function getFileTag(name) {
  return getFileType(name) === '栅格' ? 'warning' : 'success'
}

function statusText(status) {
  return { uploading: '上传中', success: '成功', error: '失败' }[status] || status
}

async function startUpload() {
  if (fileList.value.length === 0) return

  uploading.value = true
  uploadTasks.value = []

  for (const file of [...fileList.value]) {
    await uploadSingleFile(file)
  }

  fileList.value = []
  uploading.value = false
  refreshLayers()
}

async function uploadSingleFile(file) {
  const layerName = file.name.replace(/\.(tif|tiff|zip)$/i, '').replace(/[^a-zA-Z0-9_]/g, '_').toLowerCase()
  const taskId = Date.now() + Math.random()
  const task = { id: taskId, name: file.name, status: 'uploading', progress: 0 }
  uploadTasks.value.push(task)

  const onProgress = (e) => { task.progress = Math.round((e.loaded / e.total) * 100) }

  try {
    const ext = file.name.toLowerCase().split('.').pop()
    if (['tif', 'tiff'].includes(ext)) {
      await uploadGeoTIFF(WORKSPACE, layerName, file.raw, onProgress)
    } else {
      await uploadShapefile(WORKSPACE, layerName, file.raw, onProgress)
    }
    task.status = 'success'
    task.progress = 100
    ElMessage.success(`${file.name} 发布成功`)
  } catch (err) {
    task.status = 'error'
    ElMessage.error(`${file.name} 上传失败: ${err.response?.data || err.message}`)
  }
}

async function refreshLayers() {
  loadingLayers.value = true
  publishedLayers.value = []

  try {
    const rasterStores = await listCoverageStores(WORKSPACE)
    for (const s of rasterStores) {
      publishedLayers.value.push({
        name: s.name.replace('_store', ''),
        type: 'raster',
        storeName: s.name,
        deleting: false,
      })
    }

    const vectorStores = await listDataStores(WORKSPACE)
    for (const s of vectorStores) {
      if (s.name.endsWith('_store')) {
        publishedLayers.value.push({
          name: s.name.replace('_store', ''),
          type: 'vector',
          storeName: s.name,
          deleting: false,
        })
      }
    }

    publishedLayers.value.sort((a, b) => a.name.localeCompare(b.name))
  } catch (err) {
    console.error('Failed to list layers:', err)
  }

  loadingLayers.value = false
}

async function deleteLayer(layer) {
  layer.deleting = true
  try {
    if (layer.type === 'raster') {
      await deleteCoverageStore(WORKSPACE, layer.storeName)
    } else {
      await deleteVectorLayer(WORKSPACE, layer.name)
    }
    ElMessage.success(`图层 ${layer.name} 已删除`)
    refreshLayers()
  } catch (err) {
    ElMessage.error(`删除失败: ${err.response?.data || err.message}`)
  }
  layer.deleting = false
}
</script>

<style scoped>
.upload-page {
  height: 100%;
  overflow-y: auto;
  padding: 40px;
  background: #0d0d0d;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
}

.mode-content {
  width: 100%;
  max-width: 700px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.card-header h2 {
  color: #ddd;
  margin: 0;
}

.upload-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 32px;
  max-width: 520px;
  width: 100%;
}

.upload-card h2 {
  color: #ddd;
  margin: 0 0 8px;
}

.desc {
  color: #888;
  font-size: 13px;
  margin: 0 0 20px;
}

.upload-area {
  border: 1px dashed #444;
  border-radius: 8px;
  background: #222;
}

.upload-area:hover {
  border-color: #666;
}

.upload-icon {
  font-size: 40px;
  color: #555;
}

.upload-text {
  color: #aaa;
  margin-top: 8px;
}

.upload-hint {
  color: #555;
  font-size: 12px;
  margin-top: 4px;
}

.file-list {
  margin-top: 12px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  color: #bbb;
  font-size: 13px;
  border-bottom: 1px solid #2a2a2a;
}

.file-name {
  flex: 1;
}

.file-size {
  color: #666;
}

.upload-btn {
  margin-top: 16px;
  width: 100%;
}

.progress-list {
  margin-top: 16px;
}

.progress-item {
  padding: 8px 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #bbb;
}

.progress-name {
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.progress-status.success {
  color: #69DB7C;
}

.progress-status.error {
  color: #FF6B6B;
}

.progress-bar {
  margin-top: 4px;
  height: 4px;
  background: #333;
  border-radius: 2px;
}

.progress-fill {
  height: 100%;
  background: #4DABF7;
  border-radius: 2px;
  transition: width 0.3s;
}

.layers-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 20px;
  max-width: 520px;
  width: 100%;
}

.layers-card h3 {
  color: #ccc;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.layers-loading,
.layers-empty {
  color: #666;
  font-size: 13px;
  padding: 12px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.layers-list {
  max-height: 300px;
  overflow-y: auto;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid #2a2a2a;
}

.layer-name {
  flex: 1;
  color: #bbb;
  font-size: 13px;
}

/* Mobile responsive */
@media (max-width: 767px) {
  .upload-page {
    padding: 16px;
    gap: 16px;
  }

  .upload-page.mobile {
    align-items: stretch;
  }

  .upload-card,
  .layers-card {
    max-width: 100%;
    padding: 20px;
    border-radius: 8px;
  }

  .upload-card h2 {
    font-size: 18px;
  }

  .upload-icon {
    font-size: 32px;
  }

  .upload-text {
    font-size: 14px;
  }

  .file-item {
    flex-wrap: wrap;
    gap: 4px;
  }

  .file-name {
    max-width: 100%;
  }
}
</style>
