<template>
  <div v-loading="loading" class="sr-panel">
    <div class="chart-section">
      <h4 class="section-title">扩张速率 vs RSEI 变化</h4>
      <div ref="scatterChart" class="chart-container" />
    </div>
    <div class="chart-section">
      <h4 class="section-title">RSEI 四维指标</h4>
      <div ref="radarChart" class="chart-container" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getReportData, getRadarData } from '../../data/mockAnalysis'
import { DISTRICTS } from '../../data/districts'

const emit = defineEmits(['district-click'])

const scatterChart = ref(null)
const radarChart = ref(null)
let scatter = null, radar = null
const loading = ref(true)

function findCityCenter(name) {
  if (!name) return null
  const found = DISTRICTS.find(d => d.name === name)
  return found?.center || null
}

function init() {
  if (scatterChart.value) {
    scatter = echarts.init(scatterChart.value)
    const data = getReportData().scatterData
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
    // Click scatter point → fly to city
    scatter.on('click', (params) => {
      const center = findCityCenter(params.data?.name)
      if (center) {
        emit('district-click', { name: params.data.name, center })
      }
    })
  }
  if (radarChart.value) {
    radar = echarts.init(radarChart.value)
    const rd = getRadarData()
    radar.setOption({
      backgroundColor: 'transparent', tooltip: {},
      legend: { bottom: 0, textStyle: { color: '#888', fontSize: 10 } },
      radar: {
        center: ['50%', '45%'], radius: '60%',
        indicator: [
          { name: '绿度', max: 1 }, { name: '湿度', max: 1 }, { name: '干度', max: 1 }, { name: '热度', max: 1 },
        ],
        axisName: { color: '#aaa', fontSize: 10 },
        shape: 'circle', splitNumber: 4,
        axisLine: { lineStyle: { color: '#444' } },
        splitLine: { lineStyle: { color: '#333' } },
        splitArea: { areaStyle: { color: ['#1a1a1a', '#1a1a1a'] } },
      },
      series: rd.slice(0, 4).map(d => ({
        type: 'radar', name: d.city,
        data: [{ value: [d.ndvi, d.wet, d.ndbsi, d.lst], name: d.city }],
        symbol: 'circle', symbolSize: 4,
        lineStyle: { width: 1.5 },
      })),
    })
    // Click radar series → fly to city
    radar.on('click', (params) => {
      const center = findCityCenter(params.name)
      if (center) {
        emit('district-click', { name: params.name, center })
      }
    })
  }
}
onMounted(() => { init(); loading.value = false })
onUnmounted(() => { scatter?.dispose(); radar?.dispose() })
</script>

<style scoped>
.sr-panel { padding: 12px; }
.section-title { font-size: 12px; font-weight: 600; color: #aaa; margin: 0 0 8px 0; }
.chart-section { margin-bottom: 16px; }
.chart-container { height: 220px; background: #252525; border-radius: 8px; }
</style>
