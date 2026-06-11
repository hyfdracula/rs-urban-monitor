<template>
  <el-dialog
    v-model="visible"
    title="分析报告"
    width="760px"
    :close-on-click-modal="false"
    class="export-dialog"
  >
    <div class="dialog-body">
      <!-- Tabs: 查看 / 导出 -->
      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: tab === 'view' }" @click="tab = 'view'">
          📊 查看报告
        </button>
        <button class="tab-btn" :class="{ active: tab === 'export' }" @click="tab = 'export'">
          📥 导出 PDF
        </button>
      </div>

      <!-- Tab: 查看报告 -->
      <div v-if="tab === 'view'" class="report-content">
        <div class="section-grid">
          <div class="chart-box">
            <h3>扩张模式占比</h3>
            <div ref="modeChart" class="chart" />
          </div>
          <div class="chart-box">
            <h3>区县扩张排名</h3>
            <div ref="rankChart" class="chart" />
          </div>
        </div>
        <div class="data-table">
          <div class="table-header">
            <span class="table-title">城市扩张数据</span>
          </div>
          <el-table :data="expansionTable" stripe size="small" max-height="180">
            <el-table-column prop="district" label="区县" width="100" />
            <el-table-column prop="newArea" label="新增面积(km²)" width="120" />
            <el-table-column prop="rate" label="扩张速率(%)" width="120" />
            <el-table-column prop="intensity" label="扩张强度" width="100" />
            <el-table-column prop="mode" label="主导模式" />
          </el-table>
        </div>

        <div class="section-grid">
          <div class="chart-box">
            <h3>RSEI 时序变化</h3>
            <div ref="rseiTrendChart" class="chart" />
          </div>
          <div class="chart-box">
            <h3>生态等级分布</h3>
            <div ref="gradeChart" class="chart" />
          </div>
        </div>
        <div class="data-table">
          <div class="table-header">
            <span class="table-title">生态等级数据</span>
          </div>
          <el-table :data="ecologyTable" stripe size="small" max-height="140">
            <el-table-column prop="grade" label="等级" width="80" />
            <el-table-column prop="area" label="面积(km²)" width="100" />
            <el-table-column prop="percent" label="占比(%)" width="100" />
            <el-table-column prop="change" label="较上期变化" />
          </el-table>
        </div>

        <div class="chart-box full-width">
          <h3>扩张速率 vs RSEI 变化</h3>
          <div ref="scatterChart" class="chart" />
        </div>
      </div>

      <!-- Tab: 导出 PDF -->
      <div v-if="tab === 'export'" class="export-config">
        <div class="field">
          <label class="field-label">报告标题</label>
          <el-input v-model="reportTitle" size="small" placeholder="城市扩张与生态环境分析报告" />
        </div>
        <div class="field">
          <label class="field-label">包含板块</label>
          <el-checkbox-group v-model="selectedSections">
            <div v-for="s in availableSections" :key="s.key" class="section-check">
              <el-checkbox :value="s.key" size="small">
                <span class="check-icon">{{ s.icon }}</span>
                <span class="check-label">{{ s.label }}</span>
              </el-checkbox>
            </div>
          </el-checkbox-group>
        </div>
        <div class="field">
          <label class="field-label">附加内容</label>
          <el-checkbox v-model="includeMap" size="small">
            <span class="check-icon">🗺️</span>
            <span class="check-label">地图截图（封面页）</span>
          </el-checkbox>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">{{ tab === 'export' ? '取消' : '关闭' }}</el-button>
      <el-button v-if="tab === 'export'" type="primary" :loading="generating" @click="doExport">
        <el-icon><Download /></el-icon>
        <span>{{ generating ? '正在生成...' : '导出 PDF' }}</span>
      </el-button>
      <el-button v-else type="primary" @click="tab = 'export'">
        <el-icon><Download /></el-icon>
        <span>导出 PDF</span>
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { Download } from '@element-plus/icons-vue'
import echarts from '../../utils/charts'
import { buildPdfReport, downloadPdf, captureMap } from '../../utils/pdfReport'
import { fetchReportData, fetchSocioEconomicData } from '../../services/dataService'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  mapRef: { type: Object, default: null },
  chartRefs: { type: Object, default: () => ({}) },
  studyArea: { type: String, default: '北京市' },
  timeRange: { type: String, default: '2000-2020' },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const tab = ref('view')
const generating = ref(false)
const reportTitle = ref('城市扩张与生态环境分析报告')
const selectedSections = ref(['expansion', 'ecology', 'socio', 'correlation'])
const includeMap = ref(true)

const availableSections = [
  { key: 'expansion', icon: '🏗️', label: '建设用地扩张分析' },
  { key: 'ecology', icon: '🌿', label: '生态环境评估' },
  { key: 'socio', icon: '📊', label: '社会经济分析' },
  { key: 'correlation', icon: '🔗', label: '扩张与生态关联分析' },
]

const EMPTY_REPORT = {
  expansionTable: [],
  ecologyTable: [],
  modeDistribution: [],
  districtRanking: [],
  rseiTrend: [],
  ecologyGradeDistribution: [],
  scatterData: [],
}

const reportData = ref(EMPTY_REPORT)
const expansionTable = ref([])
const ecologyTable = ref([])

async function loadReportData() {
  const data = await fetchReportData()
  reportData.value = { ...EMPTY_REPORT, ...data }
  expansionTable.value = reportData.value.expansionTable
  ecologyTable.value = reportData.value.ecologyTable
}

// Chart refs
const modeChart = ref(null)
const rankChart = ref(null)
const rseiTrendChart = ref(null)
const gradeChart = ref(null)
const scatterChart = ref(null)

let instances = []

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    tab.value = 'view'
    loadReportData().then(() => nextTick(() => initCharts()))
  }
})
watch(visible, (val) => { emit('update:modelValue', val) })

function initCharts() {
  // Dispose old
  instances.forEach(i => i.dispose())
  instances = []

  const dark = { backgroundColor: 'transparent' }

  if (modeChart.value) {
    const inst = echarts.init(modeChart.value)
    inst.setOption({
      ...dark,
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie', radius: ['40%', '70%'],
        data: reportData.value.modeDistribution.map(item => ({
          name: item.name, value: item.value, itemStyle: { color: item.color },
        })),
        label: { color: '#ccc', fontSize: 11 },
      }],
    })
    instances.push(inst)
  }

  if (rankChart.value) {
    const inst = echarts.init(rankChart.value)
    inst.setOption({
      ...dark,
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLabel: { color: '#888' }, axisLine: { lineStyle: { color: '#444' } } },
      yAxis: {
        type: 'category',
        data: reportData.value.districtRanking.map(i => i.name).reverse(),
        axisLabel: { color: '#ccc' }, axisLine: { lineStyle: { color: '#444' } },
      },
      series: [{
        type: 'bar',
        data: reportData.value.districtRanking.map(i => i.value).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#FF6B6B' }, { offset: 1, color: '#FFA94D' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      }],
    })
    instances.push(inst)
  }

  if (rseiTrendChart.value) {
    const inst = echarts.init(rseiTrendChart.value)
    inst.setOption({
      ...dark,
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
      xAxis: {
        type: 'category', data: reportData.value.rseiTrend.map(i => i.year),
        axisLabel: { color: '#ccc' }, axisLine: { lineStyle: { color: '#444' } },
      },
      yAxis: {
        type: 'value', min: 0, max: 1,
        axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } },
      },
      series: [{
        type: 'line', data: reportData.value.rseiTrend.map(i => i.value), smooth: true,
        lineStyle: { color: '#51CF66', width: 2 }, itemStyle: { color: '#51CF66' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(81,207,102,0.3)' }, { offset: 1, color: 'rgba(81,207,102,0.05)' },
          ]),
        },
      }],
    })
    instances.push(inst)
  }

  if (gradeChart.value) {
    const inst = echarts.init(gradeChart.value)
    inst.setOption({
      ...dark,
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: {
        type: 'category', data: reportData.value.ecologyGradeDistribution.map(i => i.grade),
        axisLabel: { color: '#ccc' }, axisLine: { lineStyle: { color: '#444' } },
      },
      yAxis: { type: 'value', axisLabel: { color: '#888' } },
      series: [{
        type: 'bar', barWidth: '50%',
        data: reportData.value.ecologyGradeDistribution.map(i => ({ value: i.area, itemStyle: { color: i.color } })),
      }],
    })
    instances.push(inst)
  }

  if (scatterChart.value) {
    const inst = echarts.init(scatterChart.value)
    inst.setOption({
      ...dark,
      tooltip: { trigger: 'item' },
      grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
      xAxis: {
        name: '扩张速率(%)', nameTextStyle: { color: '#888' },
        axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } },
      },
      yAxis: {
        name: 'RSEI变化', nameTextStyle: { color: '#888' },
        axisLabel: { color: '#888' }, splitLine: { lineStyle: { color: '#333' } },
      },
      series: [{
        type: 'scatter', symbolSize: 16,
        data: reportData.value.scatterData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
            { offset: 0, color: '#FF6B6B' }, { offset: 1, color: '#4DABF7' },
          ]),
        },
      }],
    })
    instances.push(inst)
  }

  // Handle resize
  const onResize = () => instances.forEach(i => i.resize())
  window.addEventListener('resize', onResize)
}

onUnmounted(() => {
  instances.forEach(i => i.dispose())
})

async function doExport() {
  if (selectedSections.value.length === 0) return
  generating.value = true
  try {
    const socioData = await fetchSocioEconomicData()
    const sections = []

    // Map screenshot
    if (includeMap.value) {
      const mapEl = props.mapRef || document.querySelector('.map-container canvas')
      const mapImg = await captureMap(mapEl)
      if (mapImg) {
        sections.push({
          key: 'map', title: '研究区概况',
          charts: [{ dataUrl: mapImg, width: 800, height: 400, label: '研究区遥感影像' }],
        })
      }
    }

    // Expansion
    if (selectedSections.value.includes('expansion')) {
      sections.push({
        key: 'expansion', title: '建设用地扩张分析',
        cards: [
          { value: `${reportData.value.expansionTable[0]?.newArea || 0} km²`, label: '新增建设用地' },
          { value: `${reportData.value.expansionTable.length}个城市`, label: '研究城市数' },
        ],
        table: {
          headers: ['城市', '新增(km²)', '速率(%)', '强度', '主导模式'],
          rows: (reportData.value.expansionTable || []).slice(0, 8).map(r => [
            r.district, String(r.newArea), String(r.rate), String(r.intensity), r.mode,
          ]),
        },
      })
    }

    // Ecology
    if (selectedSections.value.includes('ecology')) {
      sections.push({
        key: 'ecology', title: '生态环境评估',
        cards: [{ value: '0.58', label: 'RSEI 均值' }, { value: '-0.07', label: 'RSEI 变化' }],
        table: {
          headers: ['等级', '面积(km²)', '占比(%)', '较上期变化'],
          rows: (reportData.value.ecologyTable || []).map(r => [r.grade, String(r.area), `${r.percent}%`, r.change]),
        },
      })
    }

    // Socio
    if (selectedSections.value.includes('socio')) {
      sections.push({
        key: 'socio', title: '社会经济分析',
        cards: [
          { value: `${socioData.population.total}万`, label: '常住人口' },
          { value: `${socioData.gdp.total}亿`, label: 'GDP总量' },
        ],
        table: {
          headers: ['城市', '人口(万)', 'GDP(亿人民币)'],
          rows: (socioData.districtPopulation || []).slice(0, 8).map((d, i) => [
            d.name, String(d.value), String(socioData.districtGdp[i]?.value ?? '—') + '亿人民币',
          ]),
        },
      })
    }

    const doc = await buildPdfReport({
      title: reportTitle.value,
      studyArea: props.studyArea,
      timeRange: props.timeRange,
      sections,
    })
    downloadPdf(doc, `${reportTitle.value}.pdf`)
    visible.value = false
  } catch (err) {
    console.error('PDF generation failed:', err)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.dialog-body { max-height: 70vh; overflow-y: auto; }

.tab-bar {
  display: flex; gap: 4px; margin-bottom: 16px;
  background: #222; border-radius: 8px; padding: 3px;
}
.tab-btn {
  flex: 1; padding: 8px; border: none; border-radius: 6px;
  background: none; color: #888; font-size: 13px;
  cursor: pointer; transition: all 0.2s;
}
.tab-btn:hover { color: #ccc; }
.tab-btn.active { background: #333; color: #fff; }

/* Report content */
.report-content { display: flex; flex-direction: column; gap: 16px; }
.section-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.chart-box { background: #252525; border-radius: 8px; padding: 12px; }
.chart-box.full-width { grid-column: span 2; }
.chart-box h3 { font-size: 13px; font-weight: 600; color: #aaa; margin: 0 0 8px; }
.chart { height: 180px; }
.data-table { background: #252525; border-radius: 8px; padding: 12px; }
.table-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.table-title { font-size: 13px; font-weight: 600; color: #aaa; }

/* Export config */
.export-config { padding: 4px 0; }
.field { margin-bottom: 16px; }
.field-label { display: block; font-size: 13px; font-weight: 600; color: #ccc; margin-bottom: 8px; }
.section-check { margin-bottom: 6px; }
.check-icon { margin-right: 4px; }
.check-label { color: #bbb; font-size: 13px; }

@media (max-width: 767px) {
  .section-grid { grid-template-columns: 1fr; }
  .chart-box.full-width { grid-column: span 1; }
}
</style>
