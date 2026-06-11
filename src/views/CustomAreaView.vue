<template>
  <MapLayout class="custom-area-page" :tabs="tabs" default-tab="overview" :show-layer-control="true" :show-legend="false">
    <template #map>
      <MapViewer ref="mapRef" @map-loaded="onMapLoaded" />
      <CustomLegendBar :map-layers="mapLayers" :visible-types="visibleTypes" />
      <BottomBar v-if="report" :items="customBottomItems" @item-click="onBottomBarClick" />
    </template>

    <template #layer-control>
      <CustomLayerControl
        :map-layers="mapLayers"
        :visible-types="visibleTypes"
        @layer-toggle="onLayerToggle"
      />
    </template>

    <template #overview>
      <CustomOverviewPanel
        :computing="computing"
        :progress-data="progressData"
        :progress-status="progressStatus"
        :report="report"
        :overview="overview"
        :fmt="fmt"
        @cancel="cancelTask"
      />
    </template>

    <template #ecology>
      <CustomEcologyPanel
        :report="report"
        :fmt="fmt"
        :rsei-change-color="rseiChangeColor"
        :chart-refs="chartRefSetters"
      />
    </template>

    <template #construction>
      <CustomExpansionPanel
        :report="report"
        :fmt="fmt"
        :chart-refs="chartRefSetters"
      />
    </template>

    <template #socio>
      <CustomSocioPanel
        :report="report"
        :fmt="fmt"
        :chart-refs="chartRefSetters"
      />
    </template>

    <template #tasks>
      <CustomAreaPanel ref="panelRef" @select="onTaskSelect" @deselect="onTaskDeselect" />
    </template>

    <template #placeholder>
      <div class="panel-content"><p class="hint">敬请期待</p></div>
    </template>

    <template #report>
      <CustomReportTab
        :report="report"
        :chart-refs="chartRefSetters"
        @open-report="showReportDialog = true"
      />
    </template>
  </MapLayout>

  <CustomReportDialog
    v-model="showReportDialog"
    :report="report"
    :study-area="report?.overview?.studyArea || '自定义研究区'"
    :years="report?.meta?.years || report?.overview?.years || []"
  />
  <CompareDialog v-if="report" v-model="showCompare" :default-range="customCompareRange" storage-key="compare-range-custom" />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import '../styles/customArea.css'
import { useCustomAreaCharts } from '../composables/useCustomAreaCharts'
import { useCustomAreaMap } from '../composables/useCustomAreaMap'
import { useTaskPolling } from '../composables/useTaskPolling'
import { Switch } from '@element-plus/icons-vue'
import MapLayout from '../components/layout/MapLayout.vue'
import MapViewer from '../components/map/MapViewer.vue'
import CustomAreaPanel from '../components/custom/CustomAreaPanel.vue'
import CustomOverviewPanel from '../components/custom/CustomOverviewPanel.vue'
import CustomEcologyPanel from '../components/custom/CustomEcologyPanel.vue'
import CustomExpansionPanel from '../components/custom/CustomExpansionPanel.vue'
import CustomSocioPanel from '../components/custom/CustomSocioPanel.vue'
import CustomReportTab from '../components/custom/CustomReportTab.vue'
import CustomReportDialog from '../components/custom/CustomReportDialog.vue'
import CustomLayerControl from '../components/map/CustomLayerControl.vue'
import CustomLegendBar from '../components/map/CustomLegendBar.vue'
import BottomBar from '../components/layout/BottomBar.vue'
import CompareDialog from '../components/dialog/CompareDialog.vue'
import { TIME_PERIODS } from '../config/map'
import { getAnalysis, getComputeProgress, cancelCompute } from '../api'

const route = useRoute()
const router = useRouter()
const mapRef = ref(null)
const panelRef = ref(null)
const report = ref(null)
let loadGeneration = 0
const showReportDialog = ref(false)
const showCompare = ref(false)

const {
  mapLayers,
  visibleTypes,
  onMapLoaded,
  addMapLayers,
  removeMapLayers,
  onLayerToggle,
  addBoundaryGeoJSON,
} = useCustomAreaMap()

const {
  computing,
  progressData,
  startProgressPolling,
  resetTaskPolling,
  cancelTask,
} = useTaskPolling({
  getProgress: getComputeProgress,
  getAnalysis,
  cancelTaskRequest: cancelCompute,
  isCurrent: (token) => token === loadGeneration,
  onCompleted: applyTaskAnalysis,
  notify: ElMessage,
})

const customCompareRange = computed(() => {
  const years = report.value?.meta?.years || report.value?.overview?.years || []
  if (years.length >= 2) return [years[0], years[years.length - 1]]
  return [TIME_PERIODS[0], TIME_PERIODS[TIME_PERIODS.length - 1]]
})

function loadCustomRange() {
  try {
    const raw = localStorage.getItem('compare-range-custom')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length === 2) return parsed
    }
  } catch { /* ignore */ }
  return customCompareRange.value
}

const customBottomItems = computed(() => {
  const [start, end] = loadCustomRange()
  return [
    { key: 'compare', label: '双期对比', sub: `${start} → ${end}`, icon: Switch },
  ]
})

function onBottomBarClick(item) {
  if (item.key === 'compare') showCompare.value = true
}

const tabs = [
  { key: 'overview', label: '总览', color: '#FFD43B' },
  { key: 'ecology', label: '生态评估', color: '#51CF66' },
  { key: 'construction', label: '建设用地', color: '#FF6B6B' },
  { key: 'socio', label: '经济统计', color: '#4DABF7' },
  { key: 'tasks', label: '任务列表', color: '#20C997' },
  { key: 'placeholder', label: '占位', color: '#868E96' },
  { key: 'report', label: '分析报告', color: '#F783AC' },
]

const overview = computed(() => report.value?.overview || {})
const progressStatus = computed(() => progressData.value.percent >= 100 ? 'success' : '')
const rseiChangeColor = computed(() => {
  const v = report.value?.ecology?.rseiChange
  if (v == null) return ''
  return v >= 0 ? '#69DB7C' : '#FF6B6B'
})

const {
  gradeChartRef,
  trendChartRef,
  changeChartRef,
  radarChartRef,
  expBarChartRef,
  industryPieRef,
  popBarRef,
  gdpBarRef,
  rptRankChartRef,
  rptRseiChartRef,
  rptGradeChartRef,
  rptChangeChartRef,
  rptIndustryChartRef,
  renderCharts,
  replayChartsForTab,
  resizeCharts,
  disposeCharts,
} = useCustomAreaCharts({ report, overview })

function assignChartRef(target) {
  return (el) => {
    target.value = el
  }
}

const chartRefSetters = {
  grade: assignChartRef(gradeChartRef),
  trend: assignChartRef(trendChartRef),
  change: assignChartRef(changeChartRef),
  radar: assignChartRef(radarChartRef),
  expansion: assignChartRef(expBarChartRef),
  industry: assignChartRef(industryPieRef),
  population: assignChartRef(popBarRef),
  gdp: assignChartRef(gdpBarRef),
  reportRank: assignChartRef(rptRankChartRef),
  reportRsei: assignChartRef(rptRseiChartRef),
  reportGrade: assignChartRef(rptGradeChartRef),
  reportChange: assignChartRef(rptChangeChartRef),
  reportIndustry: assignChartRef(rptIndustryChartRef),
}

function fmt(val, dec = 1) {
  if (val === null || val === undefined || val === '') return '—'
  return typeof val === 'number' ? val.toFixed(dec) : val
}

function onChartReplay(e) {
  const key = e?.detail
  if (typeof key === 'string') {
    replayChartsForTab(key)
    if (key === 'tasks' && panelRef.value) {
      panelRef.value.fetchTasks()
    }
  }
}

function applyTaskAnalysis(data, gen) {
  const layerData = data.map_layers || null
  const loadReport = () => {
    if (gen !== loadGeneration) return
    report.value = data.report || data
    renderCharts()
    if (layerData) addMapLayers(layerData)
  }

  if (data.boundary_geojson) {
    addBoundaryGeoJSON(data.boundary_geojson, loadReport)
  } else {
    loadReport()
  }
}

async function onTaskSelect(task) {
  resetTaskPolling()

  const gen = ++loadGeneration
  const taskId = task.task_id || task.id
  report.value = null
  try {
    const data = await getAnalysis(taskId)
    if (gen !== loadGeneration) return
    if (data.status === 'failed') { ElMessage.error(data.error || '计算失败'); return }
    if (data.status === 'processing' || data.status === 'pending') {
      startProgressPolling(taskId, gen)
      return
    }

    applyTaskAnalysis(data, gen)
  } catch (err) {
    if (gen !== loadGeneration) return
    ElMessage.error(err.response?.data?.detail || '加载失败')
  }
}

function onTaskDeselect() {
  report.value = null
  removeMapLayers()
  disposeCharts()
  resetTaskPolling()
}

watch(report, resizeCharts)

onMounted(() => {
  window.addEventListener('chart-replay', onChartReplay)
  if (route.query.submitted === '1') {
    router.replace({ path: '/custom-area', query: {} })
    setTimeout(() => {
      if (panelRef.value) panelRef.value.fetchTasks()
    }, 2500)
  }
})

onUnmounted(() => {
  window.removeEventListener('chart-replay', onChartReplay)
  resetTaskPolling()
  removeMapLayers()
  disposeCharts()
})
</script>
