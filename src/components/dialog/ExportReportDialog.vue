<template>
  <el-dialog
    v-model="visible"
    title="导出 PDF 报告"
    width="460px"
    :close-on-click-modal="false"
    class="export-dialog"
  >
    <div class="dialog-body">
      <!-- Report title -->
      <div class="field">
        <label class="field-label">报告标题</label>
        <el-input
          v-model="reportTitle"
          size="small"
          placeholder="城市扩张与生态环境分析报告"
        />
      </div>

      <!-- Sections toggle -->
      <div class="field">
        <label class="field-label">包含板块</label>
        <el-checkbox-group v-model="selectedSections">
          <div
            v-for="s in availableSections"
            :key="s.key"
            class="section-check"
          >
            <el-checkbox :value="s.key" size="small">
              <span class="check-icon">{{ s.icon }}</span>
              <span class="check-label">{{ s.label }}</span>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </div>

      <!-- Include map screenshot -->
      <div class="field">
        <label class="field-label">附加内容</label>
        <el-checkbox v-model="includeMap" size="small">
          <span class="check-icon">🗺️</span>
          <span class="check-label">地图截图（封面页）</span>
        </el-checkbox>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="generating" @click="doExport">
          <el-icon><Download /></el-icon>
          <span>{{ generating ? '正在生成...' : '导出 PDF' }}</span>
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Download } from '@element-plus/icons-vue'
import { buildPdfReport, downloadPdf, captureElement, captureMap, REPORT_SECTIONS } from '../../utils/pdfReport'
import { getReportData } from '../../data/mockAnalysis'
import { getSocioEconomicData } from '../../data/mockSocioEconomic'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  mapRef: { type: Object, default: null },
  chartRefs: { type: Object, default: () => ({}) },
  studyArea: { type: String, default: '北京市' },
  timeRange: { type: String, default: '2000-2020' },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
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

watch(() => props.modelValue, (val) => { visible.value = val })
watch(visible, (val) => { emit('update:modelValue', val) })

async function doExport() {
  if (selectedSections.value.length === 0) return
  generating.value = true

  try {
    // Use provided chart refs or auto-capture from DOM
    const sectionRefs = props.chartRefs && Object.keys(props.chartRefs).length > 0
      ? props.chartRefs
      : null

    // Capture all chart elements for selected sections
    const chartImages = {}

    if (sectionRefs) {
      // Use provided refs
      for (const key of selectedSections.value) {
        const refs = sectionRefs[key] || []
        chartImages[key] = []
        for (const ref of refs) {
          let img = null
          if (ref.dataUrl) {
            img = ref.dataUrl
          } else if (ref.element) {
            img = await captureElement(ref.element)
          }
          if (img) {
            chartImages[key].push({
              dataUrl: img,
              width: ref.width || 600,
              height: ref.height || 300,
              label: ref.label || '',
            })
          }
        }
      }
    } else {
      // Auto-capture from DOM: grab all .chart-container elements
      const allChartEls = document.querySelectorAll('.chart-container')
      const capturedCharts = []
      for (const el of allChartEls) {
        const parent = el.closest('.stat-panel, .ecology-panel, .socio-panel')
        let sectionKey = 'expansion'
        if (parent) {
          if (parent.classList.contains('ecology-panel')) sectionKey = 'ecology'
          else if (parent.classList.contains('socio-panel')) sectionKey = 'socio'
          else sectionKey = 'expansion'
        }
        const img = await captureElement(el)
        if (img) {
          capturedCharts.push({ key: sectionKey, dataUrl: img, width: 600, height: 300, label: '' })
        }
      }
      for (const key of selectedSections.value) {
        chartImages[key] = capturedCharts.filter(c => c.key === key).map(c => ({
          dataUrl: c.dataUrl, width: c.width, height: c.height, label: c.label,
        }))
      }
    }

    // Capture map: try provided ref > auto-detect canvas in .map-container
    let mapImg = null
    if (includeMap.value) {
      const mapEl = props.mapRef || document.querySelector('.map-container canvas')
      mapImg = await captureMap(mapEl)
    }

    // Build sections for the PDF
    const sections = []

    // If map included, add it first
    if (mapImg) {
      sections.push({
        key: 'map',
        title: '研究区概况',
        charts: [{ dataUrl: mapImg, width: 800, height: 400, label: '研究区遥感影像' }],
      })
    }

    // Load data from centralized sources
    const reportData = getReportData()
    const socioData = getSocioEconomicData()

    // Expansion section
    if (selectedSections.value.includes('expansion')) {
      const exp = reportData
      sections.push({
        key: 'expansion',
        title: '建设用地扩张分析',
        cards: [
          { value: `${exp.expansionTable[0]?.newArea || 0} km²`, label: '新增建设用地' },
          { value: `${exp.expansionTable.length}个城市`, label: '研究城市数' },
          { value: '0.50 km²', label: '平均斑块规模' },
          { value: '3.15%', label: '年均扩张速率' },
        ],
        charts: chartImages.expansion || [],
        table: {
          headers: ['城市', '新增(km²)', '速率(%)', '强度', '主导模式'],
          rows: (exp.expansionTable || []).slice(0, 8).map(r => [
            r.district, String(r.newArea), String(r.rate), String(r.intensity), r.mode,
          ]),
        },
      })
    }

    // Ecology section
    if (selectedSections.value.includes('ecology')) {
      const eco = reportData
      sections.push({
        key: 'ecology',
        title: '生态环境评估',
        cards: [
          { value: '0.58', label: 'RSEI 均值' },
          { value: '-0.07', label: 'RSEI 变化' },
        ],
        charts: chartImages.ecology || [],
        table: {
          headers: ['等级', '面积(km²)', '占比(%)', '较上期变化'],
          rows: (eco.ecologyTable || []).map(r => [
            r.grade, String(r.area), `${r.percent}%`, r.change,
          ]),
        },
      })
    }

    // Socio-economic section
    if (selectedSections.value.includes('socio')) {
      const s = socioData
      sections.push({
        key: 'socio',
        title: '社会经济分析',
        cards: [
          { value: `${s.population.total}万`, label: '常住人口' },
          { value: `${s.gdp.total}万亿`, label: 'GDP总量' },
          { value: `${s.population.growth}%`, label: '人口增长率' },
          { value: `${s.gdp.growth}%`, label: 'GDP增速' },
        ],
        charts: chartImages.socio || [],
        table: {
          headers: ['城市', '人口(万)', 'GDP(亿元)'],
          rows: (s.districtPopulation || []).slice(0, 8).map((d, i) => [
            d.name, String(d.value), String((s.districtGdp[i]?.value / 10000 || 0).toFixed(1)) + '万亿',
          ]),
        },
      })
    }

    // Correlation section
    if (selectedSections.value.includes('correlation') && chartImages.correlation?.length) {
      sections.push({
        key: 'correlation',
        title: '扩张与生态关联分析',
        charts: chartImages.correlation || [],
      })
    }

    // Build and download
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
    alert('PDF 生成失败: ' + err.message)
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.dialog-body {
  padding: 4px 0;
}

.field {
  margin-bottom: 16px;
}

.field-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #ccc;
  margin-bottom: 8px;
}

.section-check {
  margin-bottom: 6px;
}

.check-icon {
  margin-right: 4px;
}

.check-label {
  color: #bbb;
  font-size: 13px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
