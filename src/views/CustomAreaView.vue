<template>
  <MapLayout :tabs="tabs" default-tab="overview">
    <template #map>
      <MapViewer ref="mapRef" @map-loaded="onMapLoaded" />
      <BottomBar :items="bottomItems" />
    </template>

    <!-- 总览: 任务列表 -->
    <template #overview>
      <CustomAreaPanel @select="onTaskSelect" @deselect="onTaskDeselect" />
    </template>

    <!-- 生态 -->
    <template #ecology>
      <div class="section">
        <h4>生态评估</h4>
        <div v-if="!report" class="state-hint">请先选择研究区</div>
        <div v-else-if="!ecologyIndicators.length" class="state-hint">无生态指标数据</div>
        <div v-else class="ind-grid">
          <div v-for="ind in ecologyIndicators" :key="ind.label" class="ind-card">
            <span class="ind-label">{{ ind.label }}</span>
            <span class="ind-value">{{ ind.value }}</span>
            <span v-if="ind.trend" class="ind-trend" :class="ind.trend">
              {{ ind.trend === 'up' ? '↑' : '↓' }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- 建设 -->
    <template #construction>
      <div class="section">
        <h4>建设用地</h4>
        <div v-if="!report" class="state-hint">请先选择研究区</div>
        <div v-else-if="!constructionIndicators.length" class="state-hint">无建设用地数据</div>
        <div v-else class="ind-grid">
          <div v-for="ind in constructionIndicators" :key="ind.label" class="ind-card">
            <span class="ind-label">{{ ind.label }}</span>
            <span class="ind-value">{{ ind.value }}</span>
            <span v-if="ind.trend" class="ind-trend" :class="ind.trend">
              {{ ind.trend === 'up' ? '↑' : '↓' }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- 扩张 -->
    <template #expansion>
      <div class="section">
        <h4>扩张模式</h4>
        <div v-if="!report" class="state-hint">请先选择研究区</div>
        <div v-else-if="!expansionIndicators.length" class="state-hint">无扩张模式数据</div>
        <div v-else class="ind-grid">
          <div v-for="ind in expansionIndicators" :key="ind.label" class="ind-card">
            <span class="ind-label">{{ ind.label }}</span>
            <span class="ind-value">{{ ind.value }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- 夜灯 -->
    <template #nightlight>
      <div class="section">
        <h4>夜间灯光</h4>
        <div v-if="!report" class="state-hint">请先选择研究区</div>
        <div v-else-if="!nightlightIndicators.length" class="state-hint">无夜灯数据</div>
        <div v-else class="ind-grid">
          <div v-for="ind in nightlightIndicators" :key="ind.label" class="ind-card">
            <span class="ind-label">{{ ind.label }}</span>
            <span class="ind-value">{{ ind.value }}</span>
            <span v-if="ind.trend" class="ind-trend" :class="ind.trend">
              {{ ind.trend === 'up' ? '↑' : '↓' }}
            </span>
          </div>
        </div>
      </div>
    </template>

    <!-- 经济 -->
    <template #socio>
      <div class="section">
        <h4>社会经济</h4>
        <div v-if="!report" class="state-hint">请先选择研究区</div>
        <div v-else-if="!socioIndicators.length" class="state-hint">无社会经济数据</div>
        <div v-else class="ind-grid">
          <div v-for="ind in socioIndicators" :key="ind.label" class="ind-card">
            <span class="ind-label">{{ ind.label }}</span>
            <span class="ind-value">{{ ind.value }}</span>
          </div>
        </div>
      </div>
    </template>

    <!-- 数据 -->
    <template #data>
      <div class="section">
        <h4>数据表格</h4>
        <div v-if="!report" class="state-hint">请先选择研究区</div>
        <div v-else-if="!report.table" class="state-hint">无表格数据</div>
        <div v-else class="table-scroll">
          <table>
            <thead>
              <tr><th v-for="col in report.table.columns" :key="col">{{ col }}</th></tr>
            </thead>
            <tbody>
              <tr v-for="(row, i) in report.table.rows" :key="i">
                <td v-for="(cell, j) in row" :key="j">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>
  </MapLayout>
</template>

<script setup>
import { ref, computed, nextTick, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import MapLayout from '../components/layout/MapLayout.vue'
import MapViewer from '../components/map/MapViewer.vue'
import BottomBar from '../components/layout/BottomBar.vue'
import CustomAreaPanel from '../components/custom/CustomAreaPanel.vue'
import { getComputeReport } from '../api'

const mapRef = ref(null)
const report = ref(null)
const reportLoading = ref(false)
const mapInstance = ref(null)

const bottomItems = []  // TODO: 后续定义自定义研究区底栏按钮
const addedLayerIds = []
const chartRefs = {}
const chartInstances = []

const tabs = [
  { key: 'overview', label: '总览', color: '#FFD43B' },
  { key: 'ecology', label: '生态', color: '#51CF66' },
  { key: 'construction', label: '建设', color: '#FF6B6B' },
  { key: 'expansion', label: '扩张', color: '#FF922B' },
  { key: 'nightlight', label: '夜灯', color: '#BE4BDB' },
  { key: 'socio', label: '经济', color: '#4DABF7' },
  { key: 'data', label: '数据', color: '#20C997' },
]

// --- Task selection ---
async function onTaskSelect(taskId) {
  reportLoading.value = true
  report.value = null
  try {
    const data = await getComputeReport(taskId)
    report.value = data
    addMapLayers(data.map_layers)
  } catch (err) {
    ElMessage.error('加载分析结果失败')
  }
  reportLoading.value = false
}

function onTaskDeselect() {
  report.value = null
  removeMapLayers()
}

// --- Map layers ---
function onMapLoaded(map) {
  mapInstance.value = map
  if (report.value?.map_layers) addMapLayers(report.value.map_layers)
}

function addMapLayers(layers) {
  if (!mapInstance.value || !layers) return
  removeMapLayers()
  for (const layer of layers) {
    if (!layer.wms_url) continue
    const sourceId = `custom-${layer.type}`
    const layerId = `custom-${layer.type}`
    mapInstance.value.addSource(sourceId, {
      type: 'raster',
      tiles: [layer.wms_url + '&bbox={bbox-epsg-3857}'],
      tileSize: 256,
    })
    mapInstance.value.addLayer({
      id: layerId, type: 'raster', source: sourceId,
      paint: { 'raster-opacity': 0.7 },
    })
    addedLayerIds.push(layerId)
    if (!layer.visible) mapInstance.value.setLayoutProperty(layerId, 'visibility', 'none')
  }
}

function removeMapLayers() {
  if (!mapInstance.value) return
  for (const layerId of addedLayerIds) {
    try {
      const sourceId = mapInstance.value.getLayer(layerId)?.source
      mapInstance.value.removeLayer(layerId)
      if (sourceId) mapInstance.value.removeSource(sourceId)
    } catch { /* ignore */ }
  }
  addedLayerIds.length = 0
}

// --- Indicator filtering ---
const CATEGORY_MAP = {
  ecology: ['RSEI', 'NDVI', 'WET', 'NDBSI', 'LST', '生态', '植被', '湿度'],
  construction: ['建设用地', '建筑', 'MNDWI', 'NDBI', '不透水'],
  expansion: ['扩张', '边缘', '填充', '跃迁', 'edge', 'infill', 'leapfrog'],
  nightlight: ['夜灯', 'NTL', 'DMSP', 'VIIRS', '灯光'],
  socio: ['人口', 'GDP', '经济', 'POP', '密度'],
}

function filterIndicators(keywords) {
  if (!report.value?.indicators) return []
  return report.value.indicators.filter(ind =>
    keywords.some(kw => ind.label?.toLowerCase().includes(kw.toLowerCase()))
  )
}

const ecologyIndicators = computed(() => filterIndicators(CATEGORY_MAP.ecology))
const constructionIndicators = computed(() => filterIndicators(CATEGORY_MAP.construction))
const expansionIndicators = computed(() => filterIndicators(CATEGORY_MAP.expansion))
const nightlightIndicators = computed(() => filterIndicators(CATEGORY_MAP.nightlight))
const socioIndicators = computed(() => filterIndicators(CATEGORY_MAP.socio))

onUnmounted(() => {
  chartInstances.forEach(i => i.dispose())
  removeMapLayers()
})
</script>

<style scoped>
.section { padding: 12px; }
.section h4 { color: #ccc; margin: 0 0 12px; font-size: 14px; }
.section-head {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;
}
.section-head h4 { margin: 0; }

.state-hint {
  color: #666; font-size: 13px; text-align: center; padding: 40px 16px;
}

.ind-grid {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;
}
.ind-card {
  background: #222; border: 1px solid #333; border-radius: 8px;
  padding: 12px; display: flex; flex-direction: column; gap: 2px;
}
.ind-label { color: #888; font-size: 11px; }
.ind-value { color: #ddd; font-size: 18px; font-weight: 600; }
.ind-trend.up { color: #69DB7C; font-size: 14px; }
.ind-trend.down { color: #FF6B6B; font-size: 14px; }

.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { background: #222; color: #aaa; padding: 6px 8px; text-align: left; border-bottom: 1px solid #333; white-space: nowrap; }
td { color: #bbb; padding: 5px 8px; border-bottom: 1px solid #2a2a2a; }
</style>
