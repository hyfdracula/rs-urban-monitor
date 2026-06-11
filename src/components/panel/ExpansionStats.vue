<template>
  <div v-loading="loading" class="stat-panel">
    <h3 class="panel-title">扩张统计</h3>
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value">{{ formatNumber(expansionData.totalArea) }}</div>
        <div class="stat-unit">km²</div>
        <div class="stat-label">新增建设用地</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ expansionData.patches }}</div>
        <div class="stat-unit">个</div>
        <div class="stat-label">新增斑块数</div>
        <div class="stat-sub">面积÷平均斑块尺度(0.5km²)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ expansionData.avgPatchSize }}</div>
        <div class="stat-unit">km²</div>
        <div class="stat-label">平均斑块规模</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ expansionData.expansionRate }}</div>
        <div class="stat-unit">%</div>
        <div class="stat-label">年均扩张速率</div>
      </div>
    </div>
    <div class="chart-section">
      <h4 class="section-title">扩张模式占比</h4>
      <div ref="pieChart" class="chart-container" />
    </div>
    <div class="chart-section">
      <h4 class="section-title">区县扩张排名</h4>
      <div ref="barChart" class="chart-container" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import echarts from '../../utils/charts'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({
      totalArea: 0,
      patches: 0,
      avgPatchSize: 0,
      expansionRate: 0,
      modeDistribution: [],
      districtRanking: [],
    }),
  },
})

const emit = defineEmits(['district-click'])

const pieChart = ref(null)
const barChart = ref(null)
let pieInstance = null
let barInstance = null
const loading = ref(true)

const expansionData = ref(props.data)

watch(() => props.data, (val) => {
  expansionData.value = val
  updateCharts()
}, { deep: true })

function formatNumber(num = 0) {
  return num.toLocaleString('zh-CN', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

function initCharts() {
  if (pieChart.value) {
    pieInstance = echarts.init(pieChart.value)
    updatePieChart()
  }
  if (barChart.value) {
    barInstance = echarts.init(barChart.value)
    updateBarChart()
    // Chart click → map fly-to
    barInstance.on('click', (params) => {
      const data = expansionData.value.districtRanking
      const item = data.find(d => d.name === params.name)
      if (item && item.center) {
        emit('district-click', { name: item.name, center: item.center })
      }
    })
  }
}

function updatePieChart() {
  if (!pieInstance) return
  const data = expansionData.value.modeDistribution
  pieInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}%',
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#1a1a1a',
        borderWidth: 2,
      },
      label: {
        show: true,
        fontSize: 11,
        color: '#ccc',
        formatter: '{b}\n{c}%',
      },
      labelLine: {
        lineStyle: { color: '#666' },
      },
      data: data.map(d => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: d.color },
      })),
    }],
  })
}

function updateBarChart() {
  if (!barInstance) return
  const data = expansionData.value.districtRanking
  barInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#444' } },
      axisLabel: { color: '#888', fontSize: 10 },
      splitLine: { lineStyle: { color: '#333' } },
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name).reverse(),
      axisLine: { lineStyle: { color: '#444' } },
      axisLabel: { color: '#ccc', fontSize: 11 },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.value).reverse(),
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#FF6B6B' },
          { offset: 1, color: '#FFA94D' },
        ]),
        borderRadius: [0, 3, 3, 0],
      },
      barWidth: '60%',
    }],
  })
}

function updateCharts() {
  updatePieChart()
  updateBarChart()
}

onMounted(() => {
  initCharts()
  loading.value = false
  window.addEventListener('resize', handleResize)
  window.addEventListener('chart-replay', handleChartReplay)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('chart-replay', handleChartReplay)
  pieInstance?.dispose()
  barInstance?.dispose()
})

function handleResize() {
  pieInstance?.resize()
  barInstance?.resize()
}

function handleChartReplay() {
  pieInstance?.clear()
  barInstance?.clear()
  updateCharts()
}
</script>

<style scoped>
.stat-panel {
  padding: 12px;
  background: #1a1a1a;
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
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}

.stat-unit {
  font-size: 11px;
  color: #888;
  margin-top: 2px;
}

.stat-label {
  font-size: 11px;
  color: #aaa;
  margin-top: 4px;
}

.stat-sub {
  font-size: 9px;
  color: #666;
  margin-top: 2px;
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
  height: 160px;
  background: #252525;
  border-radius: 8px;
}
</style>
