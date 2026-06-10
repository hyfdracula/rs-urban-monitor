<template>
  <div class="analysis-page">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <span>加载分析结果...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <el-icon :size="32" color="#FF6B6B"><CircleClose /></el-icon>
      <h3>加载失败</h3>
      <p>{{ error }}</p>
      <el-button @click="router.push('/')">返回总览</el-button>
    </div>

    <!-- Report loaded -->
    <MapLayout v-else-if="report" :tabs="[{key:'analysis', label:'分析结果'}]" default-tab="analysis" :show-layer-control="false" :show-legend="false" :class="{ mobile: isMobile }">
      <template #map>
        <MapViewer ref="mapRef" @map-loaded="onMapReady" />
      </template>

      <template #analysis>
        <!-- Indicator cards -->
        <div class="indicator-cards">
          <div v-for="ind in report.indicators" :key="ind.label" class="ind-card">
            <span class="ind-label">{{ ind.label }}</span>
            <span class="ind-value">{{ ind.value }}</span>
            <span class="ind-trend" :class="ind.trend">{{ ind.trend === 'up' ? '↑' : '↓' }}</span>
          </div>
        </div>

        <!-- Charts -->
        <div class="chart-section" v-if="report.charts">
          <div v-for="(chart, key) in report.charts" :key="key" class="chart-card">
            <h4>{{ chart.title }}</h4>
            <div :ref="el => setChartRef(key, el)" class="chart-container" />
          </div>
        </div>

        <!-- Data table -->
        <div class="table-section" v-if="report.table">
          <div class="table-header">
            <h4>{{ report.table.title }}</h4>
            <el-button v-if="report.table.export_csv" size="small" @click="exportCSV">
              导出 CSV
            </el-button>
          </div>
          <div class="table-scroll">
            <table>
              <thead>
                <tr>
                  <th v-for="col in report.table.columns" :key="col">{{ col }}</th>
                </tr>
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
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Loading, CircleClose } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { getAnalysis, getComputeReport } from '../api'
import MapViewer from '../components/map/MapViewer.vue'
import MapLayout from '../components/layout/MapLayout.vue'
import { buildWmsTileUrlFromUrl } from '../utils/geoserver'

const route = useRoute()
const router = useRouter()

const taskId = route.params.taskId
const loading = ref(true)
const error = ref('')
const report = ref(null)
const isMobile = ref(false)
const mapRef = ref(null)
const chartRefs = {}
const chartInstances = []

function setChartRef(key, el) {
  if (el) chartRefs[key] = el
}

function checkMobile() {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)

  // 处理中：轮询
  let pollCount = 0
  const maxPolls = 200 // 最多轮询 10 分钟

  while (pollCount < maxPolls) {
    try {
      const data = await getAnalysis(taskId)

      // 计算中 / 待处理 / 失败
      if (data.status === 'processing' || data.status === 'pending') {
        await new Promise(r => setTimeout(r, 3000))
        pollCount++
        continue
      }

      if (data.status === 'failed') {
        error.value = data.error || '计算失败，请重新提交'
        loading.value = false
        return
      }

      // 完成 — 从聚合响应中取 report 数据
      if (data.status === 'completed') {
        const reportData = data.report || {}
        report.value = {
          status: 'completed',
          map_layers: reportData.map_layers || [],
          charts: reportData.charts || {},
          indicators: reportData.indicators || [],
          table: reportData.table || null,
          meta: reportData.meta || {},
        }
        loading.value = false

        // Render charts after DOM update
        await nextTick()
        renderCharts()
        return
      }
    } catch (err) {
      error.value = err.response?.data?.detail || '无法加载分析结果'
      loading.value = false
      return
    }
  }

  error.value = '任务超时，请稍后再试'
  loading.value = false
})

function renderCharts() {
  if (!report.value?.charts) return

  for (const [key, chart] of Object.entries(report.value.charts)) {
    const el = chartRefs[key]
    if (!el) continue

    const instance = echarts.init(el, 'dark')
    chartInstances.push(instance)

    const option = buildChartOption(chart)
    instance.setOption(option)
  }

  // Responsive resize
  window.addEventListener('resize', () => {
    chartInstances.forEach(i => i.resize())
  })
}

function buildChartOption(chart) {
  const base = {
    backgroundColor: 'transparent',
    textStyle: { color: '#ccc', fontSize: 11 },
    grid: { top: 30, right: 12, bottom: 24, left: 50 },
  }

  if (chart.x_axis && chart.series) {
    // Bar / Line chart
    base.xAxis = { type: 'category', data: chart.x_axis, axisLabel: { color: '#888' } }
    base.yAxis = { type: 'value', axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#2a2a2a' } } }

    if (chart.series.length && Array.isArray(chart.series[0])) {
      // Multiple series
      base.series = chart.series.map((s, i) => ({
        type: i === 0 ? 'bar' : 'line',
        data: s.data || s,
        smooth: i > 0,
      }))
    } else if (chart.series.data) {
      base.series = [{ type: 'bar', data: chart.series.data }]
    } else {
      base.series = [{ type: 'bar', data: chart.series }]
    }
  } else if (chart.data) {
    // Pie chart
    base.series = [{
      type: 'pie', radius: ['40%', '70%'],
      data: chart.data,
      label: { color: '#ccc', fontSize: 11 },
    }]
    base.tooltip = { trigger: 'item' }
  }

  return base
}

function onMapReady(map) {
  if (!report.value?.map_layers) return

  for (const layer of report.value.map_layers) {
    if (!layer.wms_url) continue
    const sourceId = `analysis-${layer.type}`
    const layerId = `analysis-${layer.type}`

    map.addSource(sourceId, {
      type: 'raster',
      tiles: [buildWmsTileUrlFromUrl(layer.wms_url)],
      tileSize: 256,
    })
    map.addLayer({
      id: layerId,
      type: 'raster',
      source: sourceId,
      paint: { 'raster-opacity': 0.7 },
    })

    // 所有图层默认关闭，由用户手动打开
    map.setLayoutProperty(layerId, 'visibility', 'none')
  }
}

function exportCSV() {
  if (!report.value?.table) return
  const { columns, rows } = report.value.table
  const csv = [columns.join(','), ...rows.map(r => r.join(','))].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = `analysis_${taskId}.csv`
  link.click()
  ElMessage.success('CSV 已导出')
}
</script>

<style scoped>
.analysis-page { height: 100%; }

.loading-state, .error-state {
  height: 100%; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 12px;
  color: #888; font-size: 14px;
}
.error-state h3 { color: #FF6B6B; margin: 0; }
.error-state p { color: #888; font-size: 13px; margin: 0; }

.indicator-cards {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; padding: 12px;
}
.ind-card {
  background: #1a1a1a; border: 1px solid #333; border-radius: 8px;
  padding: 10px; display: flex; flex-direction: column; gap: 2px;
}
.ind-label { color: #888; font-size: 11px; }
.ind-value { color: #ddd; font-size: 16px; font-weight: 600; }
.ind-trend.up { color: #69DB7C; }
.ind-trend.down { color: #FF6B6B; }

.chart-section { padding: 0 12px; display: flex; flex-direction: column; gap: 8px; }
.chart-card {
  background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 12px;
}
.chart-card h4 { color: #ccc; margin: 0 0 8px; font-size: 13px; }
.chart-container { width: 100%; height: 200px; }

.table-section { padding: 12px; }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.table-header h4 { color: #ccc; margin: 0; font-size: 13px; }

.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { background: #222; color: #aaa; padding: 6px 8px; text-align: left; border-bottom: 1px solid #333; white-space: nowrap; }
td { color: #bbb; padding: 5px 8px; border-bottom: 1px solid #2a2a2a; }

@media (max-width: 767px) {
  .indicator-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
