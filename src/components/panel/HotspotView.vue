<template>
  <div v-loading="loading" class="hotspot-panel">
    <h3 class="panel-title">扩张热点乡镇</h3>
    <div class="stat-cards">
      <div class="stat-card hot"><div class="val">{{ hotspotCount }}</div><div class="lbl">热点乡镇</div></div>
      <div class="stat-card cold"><div class="val">{{ coldspotCount }}</div><div class="lbl">冷点乡镇</div></div>
    </div>
    <div class="chart-section">
      <h4 class="section-title">热点强度排名</h4>
      <div ref="barChart" class="chart-container" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { getHotspotData } from '../../data/mockAnalysis'

const props = defineProps({ data: { type: Array, default: () => getHotspotData() } })
const emit = defineEmits(['district-click'])
const barChart = ref(null)
let barInstance = null
const hotspotData = ref(props.data)
const loading = ref(true)

const hotspotCount = computed(() => hotspotData.value.filter(d => d.type === 'hot').length)
const coldspotCount = computed(() => hotspotData.value.filter(d => d.type === 'cold').length)

watch(() => props.data, (val) => { hotspotData.value = val; updateChart() }, { deep: true })

function initChart() {
  if (!barChart.value) return
  barInstance = echarts.init(barChart.value)
  updateChart()
  // Click bar → fly to town
  barInstance.on('click', (params) => {
    const item = hotspotData.value.find(d => d.name === params.name)
    if (item && item.center) {
      emit('district-click', { name: item.name, center: item.center })
    }
  })
}
function updateChart() {
  if (!barInstance) return
  const sorted = [...hotspotData.value].sort((a, b) => b.value - a.value)
  barInstance.setOption({
    backgroundColor: 'transparent', tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
    xAxis: { type: 'value', axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888', fontSize: 10 }, splitLine: { lineStyle: { color: '#333' } } },
    yAxis: { type: 'category', data: sorted.map(d => d.name).reverse(), axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#ccc', fontSize: 11 } },
    series: [{
      type: 'bar', data: sorted.map(d => ({ value: d.value, itemStyle: { color: d.type === 'hot' ? '#FF6B6B' : '#4DABF7' } })).reverse(),
      barWidth: '60%', itemStyle: { borderRadius: [0, 3, 3, 0] },
    }],
  })
}
onMounted(() => { initChart(); loading.value = false; window.addEventListener('resize', () => barInstance?.resize()); window.addEventListener('chart-replay', () => { barInstance?.clear(); updateChart() }) })
onUnmounted(() => { barInstance?.dispose(); window.removeEventListener('resize', () => {}); window.removeEventListener('chart-replay', () => {}) })
</script>

<style scoped>
.hotspot-panel { padding: 12px; background: #1a1a1a; }
.panel-title { font-size: 14px; font-weight: 600; color: #ddd; margin: 0 0 12px 0; }
.stat-cards { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 16px; }
.stat-card { background: #252525; border-radius: 8px; padding: 12px; text-align: center; }
.val { font-size: 22px; font-weight: 700; }
.stat-card.hot .val { color: #FF6B6B; }
.stat-card.cold .val { color: #4DABF7; }
.lbl { font-size: 11px; color: #aaa; margin-top: 4px; }
.section-title { font-size: 12px; font-weight: 600; color: #aaa; margin: 0 0 8px 0; }
.chart-container { height: 200px; background: #252525; border-radius: 8px; }
</style>
