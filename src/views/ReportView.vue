<template>
  <div class="report-view">
    <div class="report-header">
      <h1>城市扩张与生态环境分析报告</h1>
      <div class="report-meta">
        <span>研究区域: {{ studyArea }}</span>
        <span>分析时段: {{ timeRange }}</span>
        <el-button type="primary" size="small" @click="showExportDialog = true">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>
    <div class="report-content">
      <section class="report-section">
        <h2>1. 建设用地扩张分析</h2>
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
            <button class="csv-btn" @click="exportExpansionCsv">📥 导出 CSV</button>
          </div>
          <el-table :data="expansionTable" stripe size="small">
            <el-table-column prop="district" label="区县" width="100" />
            <el-table-column prop="newArea" label="新增面积(km²)" width="120" />
            <el-table-column prop="rate" label="扩张速率(%)" width="120" />
            <el-table-column prop="intensity" label="扩张强度" width="100" />
            <el-table-column prop="mode" label="主导模式" />
          </el-table>
        </div>
      </section>
      <section class="report-section">
        <h2>2. 生态环境质量评估</h2>
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
            <button class="csv-btn" @click="exportEcologyCsv">📥 导出 CSV</button>
          </div>
          <el-table :data="ecologyTable" stripe size="small">
            <el-table-column prop="grade" label="等级" width="80" />
            <el-table-column prop="area" label="面积(km²)" width="100" />
            <el-table-column prop="percent" label="占比(%)" width="100" />
            <el-table-column prop="change" label="较上期变化" />
          </el-table>
        </div>
      </section>
      <section class="report-section">
        <h2>3. 城市扩张与生态关联分析</h2>
        <div class="chart-box full-width">
          <h3>扩张速率 vs RSEI 变化</h3>
          <div ref="scatterChart" class="chart" />
        </div>
      </section>
    </div>

    <!-- Export dialog -->
    <ExportReportDialog
      v-model="showExportDialog"
      :study-area="studyArea"
      :time-range="timeRange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { Download } from '@element-plus/icons-vue'
import { getReportData, getCityTableData } from '../data/mockAnalysis'
import ExportReportDialog from '../components/dialog/ExportReportDialog.vue'
import { exportCsv } from '../utils/csvExport'

const reportData = getReportData()

const studyArea = ref(reportData.studyArea)
const timeRange = ref(reportData.timeRange)
const showExportDialog = ref(false)

const modeChart = ref(null)
const rankChart = ref(null)
const rseiTrendChart = ref(null)
const gradeChart = ref(null)
const scatterChart = ref(null)

let modeInstance = null
let rankInstance = null
let rseiTrendInstance = null
let gradeInstance = null
let scatterInstance = null

const expansionTable = ref(reportData.expansionTable)
const ecologyTable = ref(reportData.ecologyTable)

function exportExpansionCsv() {
  exportCsv(
    expansionTable.value,
    ['区县', '新增面积(km²)', '扩张速率(%)', '扩张强度', '主导模式'],
    ['district', 'newArea', 'rate', 'intensity', 'mode'],
    '城市扩张数据.csv'
  )
}

function exportEcologyCsv() {
  exportCsv(
    ecologyTable.value,
    ['等级', '面积(km²)', '占比(%)', '较上期变化'],
    ['grade', 'area', 'percent', 'change'],
    '生态等级数据.csv'
  )
}

function initCharts() {
  // Mode pie chart
  if (modeChart.value) {
    modeInstance = echarts.init(modeChart.value)
    modeInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: ['40%', '70%'],
        data: reportData.modeDistribution.map(item => ({
          name: item.name,
          value: item.value,
          itemStyle: { color: item.color },
        })),
        label: { color: '#ccc' },
      }],
    })
  }

  // Rank bar chart
  if (rankChart.value) {
    rankInstance = echarts.init(rankChart.value)
    rankInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: { type: 'value', axisLine: { lineStyle: { color: '#444' } }, axisLabel: { color: '#888' } },
      yAxis: {
        type: 'category',
        data: reportData.districtRanking.map(item => item.name).reverse(),
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#ccc' },
      },
      series: [{
        type: 'bar',
        data: reportData.districtRanking.map(item => item.value).reverse(),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#FF6B6B' },
            { offset: 1, color: '#FFA94D' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
      }],
    })
  }

  // RSEI trend chart
  if (rseiTrendChart.value) {
    rseiTrendInstance = echarts.init(rseiTrendChart.value)
    rseiTrendInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: reportData.rseiTrend.map(item => item.year),
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#ccc' },
      },
      yAxis: {
        type: 'value',
        min: 0,
        max: 1,
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#888' },
        splitLine: { lineStyle: { color: '#333' } },
      },
      series: [{
        type: 'line',
        data: reportData.rseiTrend.map(item => item.value),
        smooth: true,
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

  // Grade bar chart
  if (gradeChart.value) {
    gradeInstance = echarts.init(gradeChart.value)
    gradeInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'axis' },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true },
      xAxis: {
        type: 'category',
        data: reportData.ecologyGradeDistribution.map(item => item.grade),
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#ccc' },
      },
      yAxis: {
        type: 'value',
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#888' },
      },
      series: [{
        type: 'bar',
        data: reportData.ecologyGradeDistribution.map(item => ({
          value: item.area,
          itemStyle: { color: item.color },
        })),
        barWidth: '50%',
      }],
    })
  }

  // Scatter chart
  if (scatterChart.value) {
    scatterInstance = echarts.init(scatterChart.value)
    scatterInstance.setOption({
      backgroundColor: 'transparent',
      tooltip: { trigger: 'item' },
      grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
      xAxis: {
        name: '扩张速率(%)',
        nameTextStyle: { color: '#888' },
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#888' },
        splitLine: { lineStyle: { color: '#333' } },
      },
      yAxis: {
        name: 'RSEI变化',
        nameTextStyle: { color: '#888' },
        axisLine: { lineStyle: { color: '#444' } },
        axisLabel: { color: '#888' },
        splitLine: { lineStyle: { color: '#333' } },
      },
      series: [{
        type: 'scatter',
        symbolSize: 20,
        data: reportData.scatterData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [
            { offset: 0, color: '#FF6B6B' },
            { offset: 1, color: '#4DABF7' },
          ]),
        },
      }],
    })
  }
}

function exportReport() {
  showExportDialog.value = true
}

function handleResize() {
  modeInstance?.resize()
  rankInstance?.resize()
  rseiTrendInstance?.resize()
  gradeInstance?.resize()
  scatterInstance?.resize()
}

onMounted(() => {
  initCharts()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  modeInstance?.dispose()
  rankInstance?.dispose()
  rseiTrendInstance?.dispose()
  gradeInstance?.dispose()
  scatterInstance?.dispose()
})
</script>

<style scoped>
.report-view {
  height: 100%;
  overflow-y: auto;
  background: #1a1a1a;
}

.report-header {
  padding: 24px;
  border-bottom: 1px solid #333;
}

.report-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px 0;
}

.report-meta {
  display: flex;
  align-items: center;
  gap: 24px;
  color: #888;
  font-size: 14px;
}

.report-content {
  padding: 24px;
}

.report-section {
  margin-bottom: 32px;
}

.report-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: #ddd;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid #333;
}

.section-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.chart-box {
  background: #252525;
  border-radius: 8px;
  padding: 16px;
}

.chart-box.full-width {
  grid-column: span 2;
}

.chart-box h3 {
  font-size: 14px;
  font-weight: 600;
  color: #aaa;
  margin: 0 0 12px 0;
}

.chart {
  height: 200px;
}

.data-table {
  background: #252525;
  border-radius: 8px;
  padding: 16px;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.table-title {
  font-size: 13px;
  font-weight: 600;
  color: #aaa;
}

.csv-btn {
  padding: 4px 12px;
  background: #333;
  color: #aaa;
  border: 1px solid #444;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.csv-btn:hover {
  background: #444;
  color: #fff;
  border-color: #666;
}
</style>
