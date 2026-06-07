<template>
  <el-dialog
    v-model="visible"
    title="发布地图服务"
    width="520px"
    :close-on-click-modal="false"
    class="publish-dialog"
  >
    <!-- Step indicator -->
    <div class="steps">
      <div class="step" :class="{ active: step >= 1, done: step > 1 }">
        <span class="step-num">1</span>
        <span class="step-label">选择图层</span>
      </div>
      <div class="step-line" :class="{ done: step > 1 }" />
      <div class="step" :class="{ active: step >= 2, done: step > 2 }">
        <span class="step-num">2</span>
        <span class="step-label">配置发布</span>
      </div>
      <div class="step-line" :class="{ done: step > 2 }" />
      <div class="step" :class="{ active: step >= 3, done: step > 3 }">
        <span class="step-num">3</span>
        <span class="step-label">完成</span>
      </div>
    </div>

    <!-- Step 1: Select layers -->
    <div v-if="step === 1" class="step-body">
      <div class="hint">选择要发布到 GeoServer 的分析结果图层：</div>
      <div
        v-for="layer in publishableLayers"
        :key="layer.id"
        class="layer-card"
        :class="{ selected: selectedLayers.includes(layer.id) }"
        @click="toggleLayer(layer.id)"
      >
        <div class="layer-card-header">
          <span class="layer-category">{{ layer.category }}</span>
          <el-checkbox :model-value="selectedLayers.includes(layer.id)" size="small" />
        </div>
        <div class="layer-card-title">{{ layer.name }}</div>
        <div class="layer-card-desc">{{ layer.description }}</div>
      </div>
    </div>

    <!-- Step 2: Configure -->
    <div v-if="step === 2" class="step-body">
      <div class="hint">确认发布配置：</div>
      <div
        v-for="layerId in selectedLayers"
        :key="layerId"
        class="config-card"
      >
        <div class="config-name">{{ getLayerInfo(layerId).name }}</div>
        <div class="config-row">
          <span class="config-key">工作区:</span>
          <span class="config-val">{{ workspace }}</span>
        </div>
        <div class="config-row">
          <span class="config-key">图层名:</span>
          <span class="config-val">{{ layerId }}</span>
        </div>
        <div class="config-row">
          <span class="config-key">投影:</span>
          <span class="config-val">EPSG:4326</span>
        </div>
        <div class="config-row">
          <span class="config-key">数据格式:</span>
          <span class="config-val">GeoJSON → WMS</span>
        </div>
      </div>
    </div>

    <!-- Step 3: Done -->
    <div v-if="step === 3" class="step-body">
      <div class="result-area">
        <div v-if="publishResults.length > 0">
          <div
            v-for="r in publishResults"
            :key="r.layerName"
            class="result-card"
            :class="{ error: r.error }"
          >
            <div class="result-status">
              <el-icon v-if="!r.error" class="success-icon">
                <CircleCheck />
              </el-icon>
              <el-icon v-else class="error-icon">
                <CircleClose />
              </el-icon>
              <span>{{ r.error ? '发布失败' : '发布成功' }}</span>
            </div>
            <div class="result-name">{{ r.layerName }}</div>
            <div v-if="!r.error" class="result-url">
              <div class="url-label">WMS 预览 (复制到浏览器):</div>
              <div class="url-box" @click="copyUrl(r.wmsUrl)">
                {{ r.wmsUrl.substring(0, 80) }}...
              </div>
            </div>
            <div v-if="r.error" class="result-error">{{ r.error }}</div>
          </div>
        </div>
        <div v-else class="empty-result">
          <p>暂无发布结果</p>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button v-if="step > 1 && step < 3" @click="step--">上一步</el-button>
        <el-button @click="visible = false">{{ step === 3 ? '关闭' : '取消' }}</el-button>
        <el-button
          v-if="step === 1"
          type="primary"
          :disabled="selectedLayers.length === 0"
          @click="step = 2"
        >
          下一步
        </el-button>
        <el-button
          v-if="step === 2"
          type="primary"
          :loading="publishing"
          @click="doPublish"
        >
          <el-icon><Upload /></el-icon>
          <span>{{ publishing ? '发布中...' : '发布到 GeoServer' }}</span>
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Upload, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import { getPublishableLayers, publishGeoJSON } from '../../utils/geoserverRest'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const step = ref(1)
const publishing = ref(false)
const selectedLayers = ref([])
const publishResults = ref([])
const workspace = ref('rs_urban')

const publishableLayers = getPublishableLayers()

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    step.value = 1
    selectedLayers.value = []
    publishResults.value = []
  }
})

watch(visible, (val) => { emit('update:modelValue', val) })

function toggleLayer(id) {
  const idx = selectedLayers.value.indexOf(id)
  if (idx >= 0) {
    selectedLayers.value.splice(idx, 1)
  } else {
    selectedLayers.value.push(id)
  }
}

function getLayerInfo(id) {
  return publishableLayers.find(l => l.id === id) || { name: id, description: '' }
}

async function doPublish() {
  publishing.value = true
  publishResults.value = []

  const results = []

  for (const layerId of selectedLayers.value) {
    try {
      const geojson = generateMockGeoJSONForLayer(layerId)
      const result = await publishGeoJSON(workspace.value, layerId, geojson, {
        title: getLayerInfo(layerId).name,
      })
      results.push({ ...result, error: null })
    } catch (err) {
      console.error(`Failed to publish ${layerId}:`, err)
      results.push({
        layerName: layerId,
        error: err.response?.data || err.message || '未知错误',
      })
    }
  }

  publishResults.value = results
  publishing.value = false
  step.value = 3
}

/**
 * Generate mock GeoJSON for a layer type.
 * In production, this would read from real analysis data.
 */
function generateMockGeoJSONForLayer(layerId) {
  // Beijing area approximate bounds
  const bboxW = 116.0
  const bboxE = 116.8
  const bboxS = 39.7
  const bboxN = 40.1

  const features = []

  // Generate 15-30 random polygon features
  const count = 15 + Math.floor(Math.random() * 15)

  for (let i = 0; i < count; i++) {
    const cx = bboxW + Math.random() * (bboxE - bboxW)
    const cy = bboxS + Math.random() * (bboxN - bboxS)
    const size = 0.01 + Math.random() * 0.04

    features.push({
      type: 'Feature',
      properties: {
        id: i,
        name: `polygon_${i}`,
        area: (Math.random() * 5).toFixed(2),
        year: [2000, 2005, 2010, 2015, 2020][Math.floor(Math.random() * 5)],
      },
      geometry: {
        type: 'Polygon',
        coordinates: [[
          [cx, cy],
          [cx + size, cy],
          [cx + size, cy + size * 0.7],
          [cx + size * 0.5, cy + size],
          [cx, cy + size * 0.5],
          [cx, cy],
        ]],
      },
    })
  }

  return {
    type: 'FeatureCollection',
    features,
  }
}

function copyUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    // subtle feedback via title change
  }).catch(() => {
    // fallback
  })
}
</script>

<style scoped>
/* Steps */
.steps {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  padding: 0 8px;
}

.step {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  font-size: 13px;
}

.step.active {
  color: #FF6B6B;
}

.step.done {
  color: #69DB7C;
}

.step-num {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: #888;
  flex-shrink: 0;
}

.step.active .step-num {
  background: #FF6B6B;
  color: #fff;
}

.step.done .step-num {
  background: #69DB7C;
  color: #fff;
}

.step-line {
  flex: 1;
  height: 2px;
  background: #333;
  margin: 0 12px;
}

.step-line.done {
  background: #69DB7C;
}

.step-body {
  min-height: 200px;
  max-height: 400px;
  overflow-y: auto;
}

.hint {
  font-size: 13px;
  color: #888;
  margin-bottom: 12px;
}

/* Layer cards */
.layer-card {
  background: #252525;
  border: 1px solid #333;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.layer-card:hover {
  border-color: #555;
}

.layer-card.selected {
  border-color: #FF6B6B;
  background: #2a2020;
}

.layer-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.layer-category {
  font-size: 11px;
  color: #888;
  background: #1a1a1a;
  padding: 2px 8px;
  border-radius: 4px;
}

.layer-card-title {
  font-size: 14px;
  font-weight: 600;
  color: #ddd;
  margin-bottom: 4px;
}

.layer-card-desc {
  font-size: 12px;
  color: #777;
}

/* Config cards */
.config-card {
  background: #252525;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.config-name {
  font-size: 14px;
  font-weight: 600;
  color: #ddd;
  margin-bottom: 8px;
}

.config-row {
  display: flex;
  gap: 8px;
  padding: 2px 0;
}

.config-key {
  font-size: 12px;
  color: #777;
  min-width: 60px;
}

.config-val {
  font-size: 12px;
  color: #bbb;
}

/* Results */
.result-card {
  background: #252525;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 10px;
}

.result-card.error {
  border: 1px solid #FF6B6B;
}

.result-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #69DB7C;
  margin-bottom: 6px;
}

.result-card.error .result-status {
  color: #FF6B6B;
}

.result-name {
  font-size: 14px;
  color: #ddd;
  margin-bottom: 6px;
}

.url-label {
  font-size: 11px;
  color: #777;
  margin-bottom: 4px;
}

.url-box {
  font-size: 11px;
  color: #4DABF7;
  background: #1a1a1a;
  padding: 6px 8px;
  border-radius: 4px;
  word-break: break-all;
  cursor: pointer;
}

.url-box:hover {
  background: #222;
}

.result-error {
  font-size: 12px;
  color: #FF6B6B;
  margin-top: 4px;
}

.empty-result {
  text-align: center;
  color: #666;
  padding: 40px 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
