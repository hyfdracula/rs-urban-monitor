<template>
  <div class="upload-page" :class="{ mobile: isMobile }">
    <!-- Upload card -->
    <div class="upload-card">
      <h2>数据上传</h2>
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

      <!-- Progress bars for each file -->
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

    <!-- Layer name prompt dialog -->
    <el-dialog
      v-model="showNameDialog"
      title="输入图层名称"
      width="360px"
      :close-on-click-modal="false"
    >
      <p class="dialog-hint">请为 {{ currentFile?.name }} 设置发布后的图层名：</p>
      <el-input
        v-model="layerNameInput"
        placeholder="例如: construction_2020"
        :maxlength="50"
        clearable
      />
      <template #footer>
        <el-button @click="showNameDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmUpload">确认上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { UploadFilled, Refresh, Loading } from '@element-plus/icons-vue'
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

const fileList = ref([])
const uploading = ref(false)
const uploadTasks = ref([])
const publishedLayers = ref([])
const loadingLayers = ref(false)
const isMobile = ref(false)

// Layer name dialog
const showNameDialog = ref(false)
const currentFile = ref(null)
const layerNameInput = ref('')
const uploadQueue = ref([])

const WORKSPACE = GEOSERVER_CONFIG.workspace

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  refreshLayers()
})

function onFileChange(file) {
  // Validate file type
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
  const type = getFileType(name)
  return type === '栅格' ? 'warning' : 'success'
}

function statusText(status) {
  return { uploading: '上传中', success: '成功', error: '失败' }[status] || status
}

async function startUpload() {
  if (fileList.value.length === 0) return

  uploadQueue.value = [...fileList.value]
  fileList.value = []
  uploading.value = true
  uploadTasks.value = []

  for (const file of uploadQueue.value) {
    await uploadSingleFile(file)
  }

  uploading.value = false
  refreshLayers()
}

async function uploadSingleFile(file) {
  // Generate layer name from filename
  const baseName = file.name.replace(/\.(tif|tiff|zip)$/i, '').replace(/[^a-zA-Z0-9_]/g, '_')
  const layerName = baseName.toLowerCase()

  const taskId = Date.now() + Math.random()
  const task = {
    id: taskId,
    name: file.name,
    status: 'uploading',
    progress: 0,
  }
  uploadTasks.value.push(task)

  const onProgress = (e) => {
    task.progress = Math.round((e.loaded / e.total) * 100)
  }

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
    console.error('Upload failed:', err)
    ElMessage.error(`${file.name} 上传失败: ${err.response?.data || err.message}`)
  }
}

async function refreshLayers() {
  loadingLayers.value = true
  publishedLayers.value = []

  try {
    // Get raster layers (coverage stores)
    const rasterStores = await listCoverageStores(WORKSPACE)
    for (const s of rasterStores) {
      publishedLayers.value.push({
        name: s.name.replace('_store', ''),
        type: 'raster',
        storeName: s.name,
        deleting: false,
      })
    }

    // Get vector layers (data stores)
    const vectorStores = await listDataStores(WORKSPACE)
    for (const s of vectorStores) {
      // Skip GeoJSON stores created by publishGeoJSON (they have '_store' suffix)
      if (s.name.endsWith('_store')) {
        publishedLayers.value.push({
          name: s.name.replace('_store', ''),
          type: 'vector',
          storeName: s.name,
          deleting: false,
        })
      }
    }

    // Sort by name
    publishedLayers.value.sort((a, b) => a.name.localeCompare(b.name))
  } catch (err) {
    console.error('Failed to list layers:', err)
    ElMessage.error('获取图层列表失败')
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
    console.error('Delete failed:', err)
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

.dialog-hint {
  color: #888;
  font-size: 13px;
  margin-bottom: 12px;
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