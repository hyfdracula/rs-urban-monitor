<template>
  <div v-loading="loading" class="ecology-panel">
    <h3 class="panel-title">生态评估</h3>
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value">{{ ecologyData.rseiMean }}</div>
        <div class="stat-label">RSEI 均值</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ ecologyData.rseiChange }}</div>
        <div class="stat-label">RSEI 变化</div>
      </div>
    </div>
    <div class="chart-section">
      <h4 class="section-title">生态等级分布</h4>
      <div ref="gradeChart" class="chart-container" />
    </div>
    <div class="chart-section">
      <h4 class="section-title">RSEI 时序变化</h4>
      <div ref="trendChart" class="chart-container" />
    </div>
    <div class="chart-section">
      <h4 class="section-title">生态变化面积</h4>
      <div ref="changeChart" class="chart-container" />
    </div>
    <div class="chart-section">
      <h4 class="section-title">RSEI 四维指标</h4>
      <div ref="radarChart" class="chart-container radar" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getEcologyData, getRadarData } from '../../data/mockAnalysis'

const props = defineProps({
  data: {
    type: Object,
    default: () => getEcologyData(),
  },
})

const gradeChart = ref(null)
const trendChart = ref(null)
const changeChart = ref(null)
const radarChart = ref(null)
let gradeInstance = null
let trendInstance = null
let changeInstance = null
let radarInstance = null
const loading = ref(true)

const ecologyData = ref(props.data)

const rseiColor = computed(() => {
  const v = ecologyData.value.rseiMean
  if (v >= 0.8) return '#2B8A3E'
  if (v >= 0.6) return '#69DB7C'
  if (v >= 0.4) return '#FFD43B'
  if (v >= 0.2) return '#FF922B'
  return '#FF6B6B'
})

const changeColor = computed(() => {
  const v = ecologyData.value.rseiChange
  if (v > 0.05) return '#2B8A3E'
  if (v > 0) return '#69DB7C'
  if (v > -0.05) return '#FFD43B'
  if (v > -0.1) return '#FF922B'
  return '#FF6B6B'
})

watch(() => props.data, (val) => {
  ecologyData.value = val
  updateCharts()
}, { deep: true })

function initCharts() {
  if (gradeChart.value) {
    gradeInstance = echarts.init(gradeChart.value)
    updateGradeChart()
  }
  if (trendChart.value) {
    trendInstance = echarts.init(trendChart.value)
    updateTrendChart()
  }
  if (changeChart.value) {
    changeInstance = echarts.init(changeChart.value)
    updateChangeChart()
  }
  if (radarChart.value) {
    radarInstance = echarts.init(radarChart.value)
    updateRadarChart()
  }
}

function updateGradeChart() {
  if (!gradeInstance) return
  const data = ecologyData.value.gradeDistribution
  gradeInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.grade),
      axisLine: { lineStyle: { color: '#444' } },
      axisLabel: { color: '#ccc', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: 'km²',
      nameTextStyle: { color: '#888', fontSize: 10 },
      axisLine: { lineStyle: { color: '#444' } },
      axisLabel: { color: '#888', fontSize: 10 },
      splitLine: { lineStyle: { color: '#333' } },
    },
    series: [{
      type: 'bar',
      data: data.map(d => ({
        value: d.area,
        itemStyle: { color: d.color, borderRadius: [3, 3, 0, 0] },
      })),
      barWidth: '50%',
    }],
  })
}

function updateTrendChart() {
  if (!trendInstance) return
  const data = ecologyData.value.trendData
  trendInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.year),
      axisLine: { lineStyle: { color: '#444' } },
      axisLabel: { color: '#ccc', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      axisLine: { lineStyle: { color: '#444' } },
      axisLabel: { color: '#888', fontSize: 10 },
      splitLine: { lineStyle: { color: '#333' } },
    },
    series: [{
      type: 'line',
      data: data.map(d => d.value),
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { color: '#51CF66', width: 2 },
      itemStyle: { color: '#51CF66' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(81, 207, 102, 0.3)' },
          { offset: 1, color: 'rgba(81, 207, 102, 0.05)' },
        ]),
      },
    }],
  })
}

function updateChangeChart() {
  if (!changeInstance) return
  const data = ecologyData.value.changeDistribution
  changeInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} km²',
    },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#1a1a1a',
        borderWidth: 2,
      },
      label: {
        show: true,
        fontSize: 10,
        color: '#ccc',
        formatter: '{b}\n{c}km²',
      },
      labelLine: { lineStyle: { color: '#666' } },
      data: data.map(d => ({
        name: d.name,
        value: d.area,
        itemStyle: { color: d.color },
      })),
    }],
  })
}

function updateCharts() {
  updateGradeChart()
  updateTrendChart()
  updateChangeChart()
  updateRadarChart()
}

function updateRadarChart() {
  if (!radarInstance) return
  const rd = getRadarData()
  radarInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {},
    legend: { bottom: 0, textStyle: { color: '#888', fontSize: 10 } },
    radar: {
      center: ['50%', '45%'],
      radius: '60%',
      indicator: [
        { name: '绿度', max: 1 }, { name: '湿度', max: 1 },
        { name: '干度', max: 1 }, { name: '热度', max: 1 },
      ],
      axisName: { color: '#aaa', fontSize: 10 },
      shape: 'circle',
      splitNumber: 4,
      axisLine: { lineStyle: { color: '#444' } },
      splitLine: { lineStyle: { color: '#333' } },
      splitArea: { areaStyle: { color: ['#1a1a1a', '#1a1a1a'] } },
    },
    series: rd.slice(0, 4).map(d => ({
      type: 'radar',
      name: d.city,
      data: [{ value: [d.ndvi, d.wet, d.ndbsi, d.lst], name: d.city }],
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { width: 1.5 },
    })),
  })
}

onMounted(() => {
  initCharts()
  loading.value = false
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  gradeInstance?.dispose()
  trendInstance?.dispose()
  changeInstance?.dispose()
  radarInstance?.dispose()
})

function handleResize() {
  gradeInstance?.resize()
  trendInstance?.resize()
  changeInstance?.resize()
  radarInstance?.resize()
}
</script>

<style scoped>
.ecology-panel {
  padding: 12px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #ddd;
  margin: 0 0 12px 0;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  margin-bottom: 16px;
}

.stat-card {
  background: #252525;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  color: #aaa;
  margin-top: 4px;
}

.chart-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  color: #aaa;
  margin: 0 0 8px 0;
}

.chart-container {
  height: 150px;
  background: #252525;
  border-radius: 8px;
}

.chart-container.radar {
  height: 220px;
}
</style>
