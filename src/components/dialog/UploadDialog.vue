<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    :width="dialogWidth"
    :close-on-click-modal="false"
    class="upload-dialog"
  >
    <div class="dialog-body">
      <!-- Mode Selection -->
      <ModeSelection v-if="!currentMode" @select="currentMode = $event" />

      <!-- Manual Mode Wizard -->
      <ManualModeWizard v-else-if="currentMode === 'manual'" @back="currentMode = null" />

      <!-- Auto Mode Wizard -->
      <AutoModeWizard v-else-if="currentMode === 'auto'" @back="currentMode = null" @done="onAutoDone" />

      <!-- GeoServer Upload -->
      <template v-else-if="currentMode === 'geoserver'">
        <div class="geoserver-header">
          <el-button text size="small" @click="currentMode = null">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <span class="geoserver-title">上传至 GeoServer</span>
        </div>

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

        <!-- Progress -->
        <div v-if="uploadTasks.length" class="progress-list">
          <div v-for="t in uploadTasks" :key="t.id" class="progress-item">
            <div class="progress-info">
              <span class="progress-name">{{ t.name }}</span>
              <span class="progress-status" :class="t.status">{{ statusText(t.status) }}</span>
            </div>
            <div v-if="t.status === 'uploading'" class="progress-bar">
              <div class="progress-fill" :style="{ width: t.progress + '%' }" />
            </div>
          </div>
        </div>

        <!-- Published layers -->
        <div class="layers-section" v-if="publishedLayers.length">
          <div class="layers-header">
            <span class="layers-title">已发布图层</span>
            <el-button size="small" text @click="refreshLayers">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="layers-list">
            <div v-for="layer in publishedLayers" :key="layer.name" class="layer-item">
              <span class="layer-name">{{ layer.name }}</span>
              <el-tag size="small" :type="layer.type === 'raster' ? 'warning' : 'success'">
                {{ layer.type === 'raster' ? '栅格' : '矢量' }}
              </el-tag>
              <el-button size="small" type="danger" text @click="deleteLayerItem(layer)">
                删除
              </el-button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <template #footer v-if="currentMode === 'geoserver'">
      <el-button @click="visible = false">关闭</el-button>
      <el-button
        type="primary"
        :loading="uploading"
        :disabled="fileList.length === 0"
        @click="startUpload"
      >
        {{ uploading ? '上传中...' : '上传并发布' }}
      </el-button>
    </template>
    <template #footer v-else>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, UploadFilled, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElNotification } from 'element-plus'
import {
  uploadGeoTIFF,
  uploadShapefile,
  listCoverageStores,
  listDataStores,
  deleteCoverageStore,
  deleteLayer as deleteVectorLayer,
} from '../../utils/geoserverRest'
import { GEOSERVER_CONFIG } from '../../config/map'
import ModeSelection from '../upload/ModeSelection.vue'
import ManualModeWizard from '../upload/ManualModeWizard.vue'
import AutoModeWizard from '../upload/AutoModeWizard.vue'

const props = defineProps({ modelValue: { type: Boolean, default: false } })
const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const currentMode = ref(null)
const fileList = ref([])
const uploading = ref(false)
const uploadTasks = ref([])
const publishedLayers = ref([])
const loadingLayers = ref(false)

const WORKSPACE = GEOSERVER_CONFIG.workspace
const router = useRouter()

function onAutoDone({ taskId }) {
  visible.value = false
  router.push('/custom-area')
}

const dialogTitle = computed(() => {
  if (!currentMode.value) return '数据接入'
  if (currentMode.value === 'manual') return '手动模式 — GEE 代码生成'
  return '数据上传'
})

const dialogWidth = computed(() => {
  if (currentMode.value === 'manual') return '720px'
  return '560px'
})

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    currentMode.value = null
    refreshLayers()
  }
})
watch(visible, (val) => { emit('update:modelValue', val) })

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
    ElMessage.error(`${file.name} 上传失败`)
  }
}

async function refreshLayers() {
  loadingLayers.value = true
  publishedLayers.value = []
  try {
    const rasterStores = await listCoverageStores(WORKSPACE)
    for (const s of rasterStores) {
      publishedLayers.value.push({ name: s.name.replace('_store', ''), type: 'raster', storeName: s.name })
    }
    const vectorStores = await listDataStores(WORKSPACE)
    for (const s of vectorStores) {
      if (s.name.endsWith('_store')) {
        publishedLayers.value.push({ name: s.name.replace('_store', ''), type: 'vector', storeName: s.name })
      }
    }
    publishedLayers.value.sort((a, b) => a.name.localeCompare(b.name))
  } catch {
    // silent
  }
  loadingLayers.value = false
}

async function deleteLayerItem(layer) {
  try {
    if (layer.type === 'raster') await deleteCoverageStore(WORKSPACE, layer.storeName)
    else await deleteVectorLayer(WORKSPACE, layer.name)
    ElMessage.success(`图层 ${layer.name} 已删除`)
    refreshLayers()
  } catch {
    ElMessage.error('删除失败')
  }
}
</script>

<style scoped>
.dialog-body { max-height: 60vh; overflow-y: auto; }

.geoserver-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.geoserver-title { color: #ccc; font-size: 13px; font-weight: 500; }

.upload-area { border: 1px dashed #444; border-radius: 8px; background: #222; }
.upload-area:hover { border-color: #666; }
.upload-icon { font-size: 36px; color: #555; }
.upload-text { color: #aaa; margin-top: 8px; font-size: 14px; }
.upload-hint { color: #555; font-size: 12px; margin-top: 4px; }

.file-list { margin-top: 12px; }
.file-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; color: #bbb; font-size: 13px; border-bottom: 1px solid #2a2a2a; }
.file-name { flex: 1; }
.file-size { color: #666; }

.progress-list { margin-top: 12px; }
.progress-item { padding: 6px 0; }
.progress-info { display: flex; justify-content: space-between; font-size: 13px; color: #bbb; }
.progress-name { overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
.progress-status.success { color: #69DB7C; }
.progress-status.error { color: #FF6B6B; }
.progress-bar { margin-top: 4px; height: 4px; background: #333; border-radius: 2px; }
.progress-fill { height: 100%; background: #4DABF7; border-radius: 2px; transition: width 0.3s; }

.layers-section { margin-top: 16px; border-top: 1px solid #333; padding-top: 12px; }
.layers-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.layers-title { font-size: 13px; font-weight: 600; color: #ccc; }
.layers-list { max-height: 200px; overflow-y: auto; }
.layer-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #2a2a2a; }
.layer-name { flex: 1; color: #bbb; font-size: 13px; }
</style>
