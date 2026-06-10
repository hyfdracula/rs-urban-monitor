<template>
  <el-dialog
    v-model="visible"
    width="900px"
    :close-on-click-modal="false"
    class="report-dialog"
    destroy-on-close
  >
    <template #header>
      <div class="dlg-header">
        <span class="dlg-title">📄 报告预览</span>
        <el-button type="primary" size="small" :loading="exporting" @click="exportPDF">
          <span>📥 下载PDF</span>
        </el-button>
      </div>
    </template>

    <div class="dialog-body">
      <!-- Page previews: 2 per row -->
      <div class="page-grid">
        <!-- Page 1: Title + 综合结论 -->
        <div class="preview-page">
          <div class="page-inner">
            <h1 class="pp-title">{{ meta.title || studyArea + ' 城市扩张与生态评估报告' }}</h1>
            <div class="pp-meta">
              <span>{{ studyArea }}</span>
              <span v-if="yearLabel">{{ yearLabel }}</span>
            </div>
            <div class="pp-section-label">一、综合结论</div>
            <p class="pp-text">{{ overview?.conclusion || '暂无结论数据。' }}</p>
            <div class="pp-kpis">
              <div v-if="overview?.totalBuiltArea != null" class="pp-kpi">
                <b>{{ overview.totalBuiltArea }} km²</b><br/><small>建设用地总面积</small>
              </div>
              <div v-if="overview?.newConstruction != null" class="pp-kpi">
                <b>{{ overview.newConstruction }} km²</b><br/><small>新增建设面积</small>
              </div>
              <div v-if="overview?.expansionRate != null" class="pp-kpi">
                <b>{{ overview.expansionRate }}%</b><br/><small>年均扩张速率</small>
              </div>
              <div v-if="overview?.rseiMean != null" class="pp-kpi">
                <b>{{ overview.rseiMean }} ({{ overview.rseiGradeLabel || '—' }})</b><br/><small>RSEI 均值</small>
              </div>
              <div v-if="overview?.population != null" class="pp-kpi">
                <b>{{ overview.population }} 万人</b><br/><small>常住人口</small>
              </div>
              <div v-if="overview?.gdp != null" class="pp-kpi">
                <b>{{ overview.gdp }} 亿元</b><br/><small>GDP 总量</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Page 2: 建设用地扩张 -->
        <div class="preview-page">
          <div class="page-inner">
            <div class="pp-section-label">二、建设用地扩张</div>
            <p class="pp-text">{{ expansion?.description || '暂无数据。' }}</p>
            <div class="pp-kpis">
              <div v-if="expansion?.totalArea != null" class="pp-kpi">
                <b>{{ expansion.totalArea }} km²</b><br/><small>总面积</small>
              </div>
              <div v-if="expansion?.newArea != null" class="pp-kpi">
                <b>{{ expansion.newArea }} km²</b><br/><small>新增面积</small>
              </div>
              <div v-if="expansion?.expansionRate != null" class="pp-kpi">
                <b>{{ expansion.expansionRate }}%</b><br/><small>扩张速率 (CAGR)</small>
              </div>
              <div v-if="expansion?.patches != null" class="pp-kpi">
                <b>{{ expansion.patches }}</b><br/><small>建设斑块数</small>
              </div>
            </div>
            <table v-if="expansion?.districtRanking?.length" class="pp-table">
              <tr><th>排名</th><th>区县</th><th>面积 (km²)</th></tr>
              <tr v-for="(d, i) in expansion.districtRanking.slice(0, 8)" :key="d.name">
                <td>{{ i + 1 }}</td><td>{{ d.name }}</td><td>{{ d.value }}</td>
              </tr>
            </table>
          </div>
        </div>

        <!-- Page 3: 生态响应 -->
        <div class="preview-page">
          <div class="page-inner">
            <div class="pp-section-label">三、生态响应</div>
            <p class="pp-text">{{ ecology?.description || '暂无数据。' }}</p>
            <div class="pp-kpis">
              <div v-if="ecology?.rseiMean != null" class="pp-kpi">
                <b>{{ ecology.rseiMean }} ({{ ecology.rseiGradeLabel || '—' }})</b><br/><small>RSEI 均值</small>
              </div>
              <div v-if="ecology?.rseiChange != null" class="pp-kpi">
                <b :class="ecology.rseiChange > 0 ? 'val-green' : 'val-red'">
                  {{ ecology.rseiChange > 0 ? '+' : '' }}{{ ecology.rseiChange }}
                </b><br/><small>{{ ecology.changeDirection || 'RSEI 变化' }}</small>
              </div>
            </div>
            <table v-if="ecology?.trendData?.length > 1" class="pp-table">
              <tr><th>年份</th><th>RSEI</th></tr>
              <tr v-for="d in ecology.trendData" :key="d.year">
                <td>{{ d.year }}</td><td>{{ d.value }}</td>
              </tr>
            </table>
            <table v-if="ecology?.gradeDistribution?.length" class="pp-table">
              <tr><th>等级</th><th>面积 (km²)</th></tr>
              <tr v-for="d in ecology.gradeDistribution" :key="d.grade">
                <td>{{ d.grade }}</td><td>{{ d.area }}</td>
              </tr>
            </table>
          </div>
        </div>

        <!-- Page 4: 社会经济 -->
        <div class="preview-page">
          <div class="page-inner">
            <div class="pp-section-label">四、社会经济</div>
            <p class="pp-text">{{ socio?.description || '暂无数据。' }}</p>
            <div class="pp-kpis">
              <div v-if="socio?.population?.total != null" class="pp-kpi">
                <b>{{ socio.population.total }} 万人</b><br/><small>常住人口</small>
              </div>
              <div v-if="socio?.gdp?.total != null" class="pp-kpi">
                <b>{{ socio.gdp.total }} 亿人民币</b><br/><small>GDP 总量 (PPP)</small>
              </div>
              <div v-if="socio?.gdp?.perCapita != null" class="pp-kpi">
                <b>{{ socio.gdp.perCapita }} 万元</b><br/><small>人均 GDP</small>
              </div>
            </div>
            <table v-if="socio?.gdp?.structure?.length" class="pp-table">
              <tr><th>产业</th><th>占比 (%)</th></tr>
              <tr v-for="d in socio.gdp.structure" :key="d.name">
                <td>{{ d.name }}</td><td>{{ d.value }}</td>
              </tr>
            </table>
          </div>
        </div>

        <!-- Page 5: 耦合关系 -->
        <div class="preview-page">
          <div class="page-inner">
            <div class="pp-section-label">五、耦合关系</div>
            <p class="pp-text">{{ couplingText }}</p>
            <div v-if="coupling?.correlation != null" class="pp-kpis">
              <div class="pp-kpi">
                <b>{{ coupling.correlation }}</b><br/><small>扩张-生态相关系数</small>
              </div>
              <div v-if="coupling.strongNegativeCount" class="pp-kpi">
                <b>{{ coupling.strongNegativeCount }}</b><br/><small>强负相关区县数</small>
              </div>
            </div>
          </div>
        </div>

        <!-- Page 6: 数据说明 -->
        <div class="preview-page">
          <div class="page-inner">
            <div class="pp-section-label">六、数据说明</div>
            <div v-if="meta.dataSources?.length" class="pp-sources">
              <span class="pp-src-label">数据来源：</span>
              <span v-for="src in meta.dataSources" :key="src" class="pp-src-tag">{{ src }}</span>
            </div>
            <p class="pp-disclaimer">
              本报告基于遥感影像反演与栅格统计数据自动生成。部分指标为经验公式或统计模型估算值，仅供参考。
              GDP 数据采用购买力平价（PPP）换算，汇率为 {{ gdpRate }}。
            </p>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const GDP_RATE = 4.2

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  report: { type: Object, default: null },
  studyArea: { type: String, default: '' },
  years: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:modelValue'])

const visible = ref(false)
const exporting = ref(false)

const overview = computed(() => props.report?.overview)
const expansion = computed(() => props.report?.expansion)
const ecology = computed(() => props.report?.ecology)
const socio = computed(() => props.report?.socio)
const coupling = computed(() => props.report?.coupling)

const meta = computed(() => ({
  title: props.report?.meta?.title || '',
  years: props.report?.meta?.years || props.years || [],
  generatedAt: props.report?.meta?.generated_at || '',
  dataSources: props.report?.meta?.data_sources || props.report?.overview?.dataSources || [],
}))

const yearLabel = computed(() => {
  const yrs = meta.value.years
  if (!yrs?.length) return ''
  if (yrs.length === 1) return `${yrs[0]} 年`
  return `${yrs[0]}–${yrs[yrs.length - 1]} 年`
})

const gdpRate = computed(() => GDP_RATE)

const couplingText = computed(() => {
  const c = coupling.value
  if (!c) return '暂无耦合分析数据。'
  const corr = c.correlation
  const parts = []
  if (corr != null && corr !== 0) {
    const dir = corr < 0 ? '负相关' : '正相关'
    const strength = Math.abs(corr) > 0.5 ? '强' : Math.abs(corr) > 0.3 ? '中等' : '弱'
    parts.push(`建设用地扩张与生态质量变化之间呈${strength}${dir}关系（r = ${corr}）。`)
    if (c.strongNegativeCities?.length) {
      parts.push(`扩张-生态强负相关区县：${c.strongNegativeCities.join('、')}。`)
    }
  } else {
    parts.push('耦合相关系数不足，可能为单年份分析或数据不足。')
  }
  return parts.join('')
})

watch(() => props.modelValue, (val) => { visible.value = val })
watch(visible, (val) => emit('update:modelValue', val))

/* ─── PDF / Print export ─── */
async function exportPDF() {
  exporting.value = true
  try {
    const ov = overview.value || {}
    const exp = expansion.value || {}
    const eco = ecology.value || {}
    const soc = socio.value || {}
    const cpl = coupling.value || {}
    const m = meta.value

    const title = m.title || `${props.studyArea} 城市扩张与生态评估报告`
    const now = new Date().toLocaleString('zh-CN')

    let html = `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><title>${esc(title)}</title>
<style>
  @page { size: A4; margin: 20mm 18mm; }
  * { box-sizing: border-box; }
  body { font-family: "SimSun","Songti SC",serif; color: #222; line-height: 1.8; max-width: 700px; margin: 0 auto; padding: 0; }
  h1 { font-size: 20px; text-align: center; margin: 0 0 6px; }
  .meta-line { text-align: center; color: #666; font-size: 13px; margin-bottom: 20px; }
  h2 { font-size: 16px; border-bottom: 1px solid #ccc; padding-bottom: 4px; margin: 24px 0 10px; }
  p { margin: 6px 0; font-size: 14px; text-indent: 2em; }
  .kpi-row { display: flex; flex-wrap: wrap; gap: 10px; margin: 10px 0; }
  .kpi { background: #f7f7f7; border-radius: 6px; padding: 8px 14px; min-width: 120px; }
  .kpi .v { font-size: 18px; font-weight: 700; color: #333; }
  .kpi .l { font-size: 11px; color: #888; }
  table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 13px; }
  th, td { border: 1px solid #ddd; padding: 5px 8px; text-align: left; }
  th { background: #f5f5f5; font-weight: 600; }
  .note { color: #888; font-size: 12px; text-indent: 0; }
  .src-tags { margin: 6px 0; }
  .src-tag { display: inline-block; background: #f0f0f0; border-radius: 3px; padding: 2px 8px; font-size: 11px; margin: 2px 4px 2px 0; color: #555; }
</style></head><body>`

    html += `<h1>${esc(title)}</h1>`
    html += `<div class="meta-line">${esc(props.studyArea)}${yearLabel.value ? ' | ' + esc(yearLabel.value) : ''} | 生成时间: ${now}</div>`

    html += `<h2>一、综合结论</h2>`
    html += `<p>${esc(ov.conclusion || '暂无结论。')}</p>`
    if (ov.singleYearNote) html += `<p class="note">${esc(ov.singleYearNote)}</p>`

    const kpis = []
    if (ov.totalBuiltArea != null) kpis.push([`${ov.totalBuiltArea} km²`, '建设用地总面积'])
    if (ov.newConstruction != null) kpis.push([`${ov.newConstruction} km²`, '新增建设面积'])
    if (ov.expansionRate != null) kpis.push([`${ov.expansionRate}%`, '年均扩张速率'])
    if (ov.rseiMean != null) kpis.push([`${ov.rseiMean} (${ov.rseiGradeLabel || '—'})`, 'RSEI 均值'])
    if (ov.population != null) kpis.push([`${ov.population} 万人`, '常住人口'])
    if (ov.gdp != null) kpis.push([`${ov.gdp} 亿元`, 'GDP 总量'])
    if (kpis.length) {
      html += `<div class="kpi-row">${kpis.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join('')}</div>`
    }

    html += `<h2>二、建设用地扩张</h2>`
    html += `<p>${esc(exp.description || '暂无数据。')}</p>`
    const expKpis = []
    if (exp.totalArea != null) expKpis.push([`${exp.totalArea} km²`, '总面积'])
    if (exp.newArea != null) expKpis.push([`${exp.newArea} km²`, '新增面积'])
    if (exp.expansionRate != null) expKpis.push([`${exp.expansionRate}%`, '扩张速率 (CAGR)'])
    if (exp.patches != null) expKpis.push([`${exp.patches}`, '建设斑块数'])
    if (expKpis.length) {
      html += `<div class="kpi-row">${expKpis.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join('')}</div>`
    }
    if (exp.districtRanking?.length) {
      html += `<table><tr><th>排名</th><th>区县</th><th>建设用地 (km²)</th></tr>`
      exp.districtRanking.forEach((d, i) => {
        html += `<tr><td>${i + 1}</td><td>${esc(d.name)}</td><td>${d.value}</td></tr>`
      })
      html += `</table>`
    }

    html += `<h2>三、生态响应</h2>`
    html += `<p>${esc(eco.description || '暂无数据。')}</p>`
    const ecoKpis = []
    if (eco.rseiMean != null) ecoKpis.push([`${eco.rseiMean} (${eco.rseiGradeLabel || '—'})`, 'RSEI 均值'])
    if (eco.rseiChange != null) ecoKpis.push([`${eco.rseiChange > 0 ? '+' : ''}${eco.rseiChange}`, eco.changeDirection || 'RSEI 变化'])
    if (ecoKpis.length) {
      html += `<div class="kpi-row">${ecoKpis.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join('')}</div>`
    }
    if (eco.trendData?.length > 1) {
      html += `<table><tr><th>年份</th><th>RSEI 均值</th></tr>`
      eco.trendData.forEach(d => { html += `<tr><td>${d.year}</td><td>${d.value}</td></tr>` })
      html += `</table>`
    }
    if (eco.gradeDistribution?.length) {
      html += `<table><tr><th>等级</th><th>面积 (km²)</th></tr>`
      eco.gradeDistribution.forEach(d => { html += `<tr><td>${d.grade}</td><td>${d.area}</td></tr>` })
      html += `</table>`
    }

    html += `<h2>四、社会经济</h2>`
    html += `<p>${esc(soc.description || '暂无数据。')}</p>`
    const socKpis = []
    if (soc.population?.total != null) socKpis.push([`${soc.population.total} 万人`, '常住人口'])
    if (soc.gdp?.total != null) socKpis.push([`${soc.gdp.total} 亿人民币`, 'GDP 总量 (PPP)'])
    if (soc.gdp?.perCapita != null) socKpis.push([`${soc.gdp.perCapita} 万元`, '人均 GDP (人民币)'])
    if (socKpis.length) {
      html += `<div class="kpi-row">${socKpis.map(([v, l]) => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div></div>`).join('')}</div>`
    }
    if (soc.gdp?.structure?.length) {
      html += `<table><tr><th>产业</th><th>占比 (%)</th></tr>`
      soc.gdp.structure.forEach(d => { html += `<tr><td>${esc(d.name)}</td><td>${d.value}</td></tr>` })
      html += `</table>`
    }

    html += `<h2>五、耦合关系</h2>`
    html += `<p>${esc(couplingText.value)}</p>`
    if (cpl.correlation != null) {
      html += `<div class="kpi-row"><div class="kpi"><div class="v">${cpl.correlation}</div><div class="l">扩张-生态相关系数</div></div>`
      if (cpl.strongNegativeCount) {
        html += `<div class="kpi"><div class="v">${cpl.strongNegativeCount}</div><div class="l">强负相关区县数</div></div>`
      }
      html += `</div>`
    }

    html += `<h2>六、数据说明</h2>`
    if (m.dataSources?.length) {
      html += `<div class="src-tags">数据来源：${m.dataSources.map(s => `<span class="src-tag">${esc(s)}</span>`).join('')}</div>`
    }
    html += `<p class="note">本报告基于遥感影像反演与栅格统计数据自动生成。部分指标为经验公式或统计模型估算值，仅供参考。GDP 数据采用购买力平价（PPP）换算，汇率为 ${GDP_RATE}。</p>`

    html += `<script>window.onload = function() { window.print(); }<\/script></body></html>`

    const win = window.open('', '_blank')
    win.document.write(html)
    win.document.close()
  } catch (err) {
    console.error('Export failed:', err)
  }
  exporting.value = false
}

function esc(str) {
  if (str == null) return ''
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}
</script>

<style scoped>
/* Dialog header */
.dlg-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}
.dlg-title {
  font-size: 16px;
  font-weight: 700;
  color: #e0e0e0;
}

/* Dialog body */
.dialog-body {
  max-height: 75vh;
  overflow-y: auto;
  padding-right: 4px;
}

/* Page grid: 2 per row */
.page-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* Single preview page */
.preview-page {
  background: #fdfdfd;
  border: 1px solid #ddd;
  border-radius: 2px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  aspect-ratio: 0.707; /* 1 / sqrt(2) ~ A4 */
  overflow: hidden;
  display: flex;
}

.page-inner {
  padding: 16px 18px;
  width: 100%;
  overflow-y: auto;
  color: #333;
  font-size: 10px;
  line-height: 1.6;
}

.pp-title {
  font-size: 13px;
  font-weight: 700;
  text-align: center;
  color: #222;
  margin: 0 0 4px;
}

.pp-meta {
  text-align: center;
  color: #999;
  font-size: 9px;
  margin-bottom: 10px;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.pp-section-label {
  font-size: 11px;
  font-weight: 700;
  color: #444;
  border-bottom: 1px solid #ddd;
  padding-bottom: 2px;
  margin-bottom: 6px;
}

.pp-text {
  font-size: 10px;
  color: #555;
  margin: 0 0 8px;
  text-align: justify;
}

/* KPIs */
.pp-kpis {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.pp-kpi {
  background: #f5f5f5;
  border-radius: 4px;
  padding: 4px 8px;
  min-width: 70px;
  flex: 1;
  text-align: center;
}

.pp-kpi b {
  font-size: 12px;
  color: #333;
}

.pp-kpi small {
  font-size: 8px;
  color: #888;
}

.val-green { color: #2B8A3E !important; }
.val-red { color: #C92A2A !important; }

/* Tables */
.pp-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8px;
  margin-bottom: 6px;
}

.pp-table th, .pp-table td {
  border: 1px solid #ddd;
  padding: 2px 4px;
  text-align: left;
}

.pp-table th {
  background: #f0f0f0;
  font-weight: 600;
}

/* Sources */
.pp-sources {
  margin-bottom: 6px;
  font-size: 9px;
  color: #888;
}

.pp-src-label { color: #666; }

.pp-src-tag {
  display: inline-block;
  background: #eee;
  border-radius: 2px;
  padding: 1px 5px;
  margin: 1px 2px;
  font-size: 8px;
  color: #555;
}

.pp-disclaimer {
  font-size: 9px;
  color: #999;
  line-height: 1.5;
  text-align: justify;
}

/* Scrollbar */
.dialog-body::-webkit-scrollbar { width: 4px; }
.dialog-body::-webkit-scrollbar-thumb { background: #444; border-radius: 2px; }

/* Mobile */
@media (max-width: 767px) {
  .page-grid { grid-template-columns: 1fr; }
}
</style>
