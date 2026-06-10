<template>
  <div class="mode-selection">
    <h2 class="mode-title">选择数据接入方式</h2>

    <div class="mode-cards">
      <!-- Manual Mode -->
      <div class="mode-card" @click="$emit('select', 'manual')">
        <div class="card-icon manual-icon">
          <el-icon :size="32"><EditPen /></el-icon>
        </div>
        <h3>手动模式</h3>
        <p>填写参数 → 生成 GEE 代码 → 复制到 Earth Engine 运行</p>
        <el-tag size="small" type="success">推荐</el-tag>
      </div>

      <!-- Auto Mode -->
      <el-tooltip v-if="!geeReady" content="请先在顶部 GEE 按钮配置密钥" placement="top">
        <div class="mode-card disabled" @click="showAutoTip">
          <div class="card-icon auto-icon">
            <el-icon :size="32"><VideoPlay /></el-icon>
          </div>
          <h3>自动模式</h3>
          <p>一键自动化处理，从数据获取到地图展示全流程</p>
          <el-tag size="small" type="info">需配置密钥</el-tag>
        </div>
      </el-tooltip>
      <div v-else class="mode-card" @click="$emit('select', 'auto')">
        <div class="card-icon auto-icon">
          <el-icon :size="32"><VideoPlay /></el-icon>
        </div>
        <h3>自动模式</h3>
        <p>一键自动化处理，从数据获取到地图展示全流程</p>
        <el-tag size="small" type="success">已就绪</el-tag>
      </div>

      <!-- GeoServer Upload -->
      <div class="mode-card" @click="$emit('select', 'geoserver')">
        <div class="card-icon upload-icon">
          <el-icon :size="32"><UploadFilled /></el-icon>
        </div>
        <h3>文件上传</h3>
        <p>上传 GeoTIFF / Shapefile 至 GeoServer 发布 WMS</p>
        <el-tag size="small" type="warning">已有数据</el-tag>
      </div>
    </div>

    <!-- 没有边界数据？条形按钮 -->
    <div class="no-data-bar" @click="showCityDialog = true">
      <span>没有边界数据？</span>
      <span class="bar-hint">支持全国 340+ 城市，输入城市名获取 →</span>
    </div>

    <!-- 城市边界对话框 -->
    <CityBoundaryDialog
      v-model:visible="showCityDialog"
      @done="onCityDone"
    />

    <RecomputeDialog
      v-model:visible="showRecomputeDialog"
      :boundary="recomputeTarget"
      @done="onRecomputeDone"
    />

    <!-- 已上传边界列表 -->
    <div v-if="boundaries.length" class="boundary-section">
      <div class="section-header">
        <span class="section-title">已上传边界</span>
        <el-button text size="small" @click="loadBoundaries">
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
      <div class="boundary-list">
        <div
          v-for="b in boundaries"
          :key="b.id"
          class="boundary-row clickable"
          @click="onRecompute(b)"
        >
          <div class="boundary-info">
            <span class="boundary-name">{{ b.name }}</span>
            <span class="boundary-filename">{{ b.filename }}</span>
          </div>
          <div class="boundary-meta">
            <el-tag size="small" :type="statusType(b.status)">{{ statusLabel(b.status) }}</el-tag>
            <span class="boundary-time">{{ shortTime(b.created_at) }}</span>
            <el-button text size="small" type="danger" @click.stop="onDelete(b)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { EditPen, VideoPlay, UploadFilled, Refresh, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getGeeKeyStatus, getBoundaryList, deleteBoundary } from '../../api'
import CityBoundaryDialog from './CityBoundaryDialog.vue'
import RecomputeDialog from './RecomputeDialog.vue'

const emit = defineEmits(['select', 'cityDone', 'recomputeDone'])

const recomputeTarget = ref(null)
const showRecomputeDialog = ref(false)

const geeReady = ref(false)
const showCityDialog = ref(false)
const boundaries = ref([])

onMounted(() => {
  loadGeeStatus()
  loadBoundaries()
  window.addEventListener('gee-status-changed', loadGeeStatus)
})
onUnmounted(() => {
  window.removeEventListener('gee-status-changed', loadGeeStatus)
})

async function loadGeeStatus() {
  try {
    const data = await getGeeKeyStatus()
    geeReady.value = data.has_key && data.status === 'valid'
  } catch {
    geeReady.value = false
  }
}

async function loadBoundaries() {
  try {
    const data = await getBoundaryList()
    boundaries.value = data.items || []
  } catch {
    boundaries.value = []
  }
}

async function onDelete(b) {
  try {
    await ElMessageBox.confirm(
      `确定删除「${b.name}」？`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await deleteBoundary(b.id)
    ElMessage.success(`已删除「${b.name}」`)
    boundaries.value = boundaries.value.filter(item => item.id !== b.id)
  } catch {
    ElMessage.error('删除失败')
  }
}

function onCityDone(payload) {
  showCityDialog.value = false
  loadBoundaries()
  emit('cityDone', payload)
}

function onRecompute(b) {
  if (b.status === 'processing') {
    ElMessage.info('该边界正在处理中，请等待完成后再重新计算')
    return
  }
  recomputeTarget.value = b
  showRecomputeDialog.value = true
}

function onRecomputeDone({ taskId }) {
  showRecomputeDialog.value = false
  emit('recomputeDone', { taskId })
}

function statusLabel(status) {
  return { processing: '处理中', completed: '完成', failed: '失败' }[status] || status
}

function statusType(status) {
  return { processing: 'info', completed: 'success', failed: 'danger' }[status] || 'info'
}

function shortTime(iso) {
  if (!iso) return ''
  return iso.slice(0, 16).replace('T', ' ')
}

function showAutoTip() {
  ElMessage.warning('请先点击顶部「GEE」按钮配置密钥')
}
</script>

<style scoped>
.mode-selection {
  text-align: center;
  padding: 20px 0;
}

.mode-title {
  color: #ddd;
  margin: 0 0 36px;
  font-size: 20px;
}

.mode-desc {
  color: #888;
  font-size: 13px;
  margin: 0 0 28px;
}

.mode-cards {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: nowrap;
}

.mode-card {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 20px 12px;
  width: 155px;
  cursor: pointer;
  transition: all 0.25s;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.mode-card:hover {
  border-color: #555;
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.mode-card h3 {
  color: #ddd;
  margin: 0;
  font-size: 16px;
}

.mode-card p {
  color: #888;
  font-size: 12px;
  margin: 0;
  line-height: 1.5;
}

.mode-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.mode-card.disabled:hover {
  border-color: #333;
  transform: none;
  box-shadow: none;
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.manual-icon {
  background: rgba(77, 171, 247, 0.15);
  color: #4DABF7;
}

.auto-icon {
  background: rgba(190, 75, 219, 0.15);
  color: #BE4BDB;
}

.upload-icon {
  background: rgba(255, 107, 107, 0.15);
  color: #FF6B6B;
}

/* 没有边界数据？条形按钮 */
.no-data-bar {
  margin-top: 20px;
  max-width: 500px;
  margin-left: auto;
  margin-right: auto;
  padding: 12px 20px;
  background: #1a1a1a;
  border: 1px dashed #444;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.25s;
  color: #888;
  font-size: 14px;
}

.no-data-bar:hover {
  border-color: #4DABF7;
  background: rgba(77, 171, 247, 0.06);
  color: #4DABF7;
}

.bar-hint {
  font-size: 12px;
  opacity: 0.7;
}

/* 已上传边界列表 */
.boundary-section {
  margin-top: 20px;
  border-top: 1px solid #2a2a2a;
  padding-top: 16px;
  text-align: left;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-title {
  color: #ccc;
  font-size: 14px;
  font-weight: 600;
}

.boundary-list {
  max-height: 240px;
  overflow-y: auto;
}

.boundary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #222;
}

.boundary-row.clickable {
  cursor: pointer;
  transition: background 0.15s;
}

.boundary-row.clickable:hover {
  background: rgba(255, 159, 67, 0.06);
}

.boundary-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.boundary-name {
  color: #ddd;
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.boundary-filename {
  color: #666;
  font-size: 11px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.boundary-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.boundary-time {
  color: #555;
  font-size: 11px;
}

@media (max-width: 700px) {
  .mode-cards {
    flex-direction: column;
    align-items: stretch;
  }

  .mode-card {
    width: 100%;
  }
}
</style>