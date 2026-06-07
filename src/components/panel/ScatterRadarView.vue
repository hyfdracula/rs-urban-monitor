<template>
  <div v-loading="loading" class="sr-panel">
    <h3 class="panel-title">耦合响应</h3>

    <!-- Correlation indicator cards -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value" :style="{ color: corrColor }">{{ correlation }}</div>
        <div class="stat-label">扩张—生态相关系数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ coupledCities }}</div>
        <div class="stat-label">强负相关城市</div>
      </div>
    </div>

    <div class="chart-section">
      <h4 class="section-title">扩张速率 vs RSEI 变化</h4>
      <div ref="scatterChart" class="chart-container" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { getReportData } from '../../data/mockAnalysis'
import { DISTRICTS } from '../../data/districts'

const emit = defineEmits(['district-click'])

const scatterChart = ref(null)
let scatter = null
const loading = ref(true)

function findCityCenter(name) {
  if (!name) return null
  const found = DISTRICTS.find(d => d.name === name)
  return found?.center || null
}

const scatterData = computed(() => getReportData().scatterData || [])

// Compute Pearson correlation coefficient
const correlation = computed(() => {
  const data = scatterData.value
  if (!data || data.length < 2) return '—'
  const xs = data.map(d => d[0])
  const ys = data.map(d => d[1])
  const n = xs.length
  const meanX = xs.reduce((a, b) => a + b, 0) / n
  const meanY = ys.reduce((a, b) => a + b, 0) / n
  let num = 0, denX = 0, denY = 0
  for (let i = 0; i < n; i++) {
    const dx = xs[i] - meanX
    const dy = ys[i] - meanY
    num += dx * dy
    denX += dx * dx
    denY += dy * dy
  }
  const r = num / Math.sqrt(denX * denY)
  return r.toFixed(3)
})

const corrColor = computed(() => {
  const r = parseFloat(correlation.value)
  if (isNaN(r)) return '#888'
  if (r < -0.5) return '#FF6B6B'
  if (r < -0.2) return '#FFD43B'
  return '#69DB7C'
})

const coupledCities = computed(() => {
  return scatterData.value.filter(d => d[1] < -0.05).length
})

function init() {
  if (scatterChart.value) {
    scatter = echarts.init(scatterChart.value)
    const data = scatterData.value
    scatter.setOption({
      backgroundColor: 'transparent', tooltip: { trigger: 'item', formatter: (p) => `${p.data.name}<br/>扩张速率: ${p.value[0]}%<br/>RSEI变化: ${p.value[1]}` },
      grid: { left: '8%', right: '4%', bottom: '8%', top: '8%', containLabel: true },
      xAxis: { name: '扩张速率(%)', nameTextStyle: { color: '#888', fontSize: 10 }, axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
      yAxis: { name: 'RSEI变化', nameTextStyle: { color: '#888', fontSize: 10 }, axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
      series: [{
        type: 'scatter', symbolSize: 16,
        data: data.map(([x, y, name]) => ({ value: [x, y], name, itemStyle: { color: y < -0.05 ? '#FF6B6B' : y < -0.02 ? '#FFD43B' : '#69DB7C' } })),
        label: { show: true, formatter: '{b}', position: 'right', fontSize: 10, color: '#ccc' },
        emphasis: { focus: 'self', itemStyle: { shadowBlur: 10, shadowColor: 'rgba(255,255,255,0.3)' } },
      }],
    })
    scatter.on('click', (params) => {
      const center = findCityCenter(params.data?.name)
      if (center) emit('district-click', { name: params.data.name, center })
    })
  }
}

onMounted(() => { init(); loading.value = false })
onUnmounted(() => { scatter?.dispose() })
</script>

<style scoped>
.sr-panel { padding: 12px; }
.panel-title { font-size: 13px; font-weight: 600; color: #ddd; margin: 0 0 10px 0; }
.stat-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.stat-card { background: #252525; border-radius: 8px; padding: 10px; text-align: center; }
.stat-value { font-size: 22px; font-weight: 700; color: #fff; }
.stat-label { font-size: 11px; color: #888; margin-top: 4px; }
.section-title { font-size: 12px; font-weight: 600; color: #aaa; margin: 0 0 8px 0; }
.chart-section { margin-bottom: 16px; }
.chart-container { height: 240px; background: #252525; border-radius: 8px; }
</style>