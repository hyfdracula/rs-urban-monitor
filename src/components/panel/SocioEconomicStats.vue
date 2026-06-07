<template>
  <div v-loading="loading" class="socio-panel">
    <h3 class="panel-title">社会经济</h3>

    <!-- Key Stats -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-value">{{ socioData.population.total }}</div>
        <div class="stat-unit">万人</div>
        <div class="stat-label">常住人口</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ socioData.gdp.total }}</div>
        <div class="stat-unit">万亿元</div>
        <div class="stat-label">GDP 总量</div>
      </div>
      <div class="stat-card">
        <div class="stat-value highlight-green">{{ socioData.population.growth }}</div>
        <div class="stat-unit">%</div>
        <div class="stat-label">人口增长率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value highlight-green">{{ socioData.gdp.growth }}</div>
        <div class="stat-unit">%</div>
        <div class="stat-label">GDP 增速</div>
      </div>
    </div>

    <!-- GDP Structure -->
    <div class="chart-section">
      <h4 class="section-title">产业结构</h4>
      <div ref="structureChart" class="chart-container" />
    </div>

    <!-- District Population Ranking -->
    <div class="chart-section">
      <h4 class="section-title">区县人口排名</h4>
      <div ref="populationChart" class="chart-container" />
    </div>

    <!-- District GDP Ranking -->
    <div class="chart-section">
      <h4 class="section-title">区县 GDP 排名</h4>
      <div ref="gdpChart" class="chart-container" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getSocioEconomicData } from '../../data/mockSocioEconomic'

const props = defineProps({
  data: {
    type: Object,
    default: () => getSocioEconomicData(),
  },
})

const emit = defineEmits(['district-click'])

const structureChart = ref(null)
const populationChart = ref(null)
const gdpChart = ref(null)
let structureInstance = null
let populationInstance = null
let gdpInstance = null
const loading = ref(true)

const socioData = ref(props.data)

watch(() => props.data, (val) => {
  socioData.value = val
  updateCharts()
}, { deep: true })

function initCharts() {
  if (structureChart.value) {
    structureInstance = echarts.init(structureChart.value)
    updateStructureChart()
  }
  if (populationChart.value) {
    populationInstance = echarts.init(populationChart.value)
    updatePopulationChart()
    populationInstance.on('click', (params) => {
      const item = socioData.value.districtPopulation.find(d => d.name === params.name)
      if (item && item.center) {
        emit('district-click', { name: item.name, center: item.center })
      }
    })
  }
  if (gdpChart.value) {
    gdpInstance = echarts.init(gdpChart.value)
    updateGdpChart()
    gdpInstance.on('click', (params) => {
      const item = socioData.value.districtGdp.find(d => d.name === params.name)
      if (item && item.center) {
        emit('district-click', { name: item.name, center: item.center })
      }
    })
  }
}

function updateStructureChart() {
  if (!structureInstance) return
  const data = socioData.value.gdp.structure
  structureInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}%',
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
        formatter: '{b}\n{c}%',
      },
      labelLine: { lineStyle: { color: '#666' } },
      data: data.map(d => ({
        name: d.name,
        value: d.value,
        itemStyle: { color: d.color },
      })),
    }],
  })
}

function updatePopulationChart() {
  if (!populationInstance) return
  const data = socioData.value.districtPopulation
  populationInstance.setOption({
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
          { offset: 0, color: '#4DABF7' },
          { offset: 1, color: '#74C0FC' },
        ]),
        borderRadius: [0, 3, 3, 0],
      },
      barWidth: '60%',
    }],
  })
}

function updateGdpChart() {
  if (!gdpInstance) return
  const data = socioData.value.districtGdp
  gdpInstance.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const d = params[0]
        return `${d.name}: ${(d.value / 10000).toFixed(1)}万亿`
      },
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
      axisLabel: {
        color: '#888',
        fontSize: 10,
        formatter: (v) => `${(v / 10000).toFixed(0)}万亿`,
      },
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
  updateStructureChart()
  updatePopulationChart()
  updateGdpChart()
}

onMounted(() => {
  initCharts()
  loading.value = false
  window.addEventListener('resize', handleResize)
  window.addEventListener('chart-replay', () => { structureInstance?.clear(); populationInstance?.clear(); gdpInstance?.clear(); updateCharts() })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  structureInstance?.dispose()
  populationInstance?.dispose()
  gdpInstance?.dispose()
})

function handleResize() {
  structureInstance?.resize()
  populationInstance?.resize()
  gdpInstance?.resize()
}
</script>

<style scoped>
.socio-panel {
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
  padding: 10px;
  text-align: center;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  line-height: 1;
}

.stat-value.highlight-green {
  color: #fff;
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
</style>
