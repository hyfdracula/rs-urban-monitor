<template>
  <div class="panel-content" v-if="!report">
    <p class="hint">请先选择研究区</p>
  </div>
  <div class="panel-content" v-else>
    <div class="dl-card" @click="emit('open-report')">
      <span class="dl-icon">🏙️</span>
      <div class="dl-info">
        <span class="dl-name">分析报告</span>
        <span class="dl-desc">PDF 格式完整监测报告</span>
      </div>
      <span class="dl-arrow">›</span>
    </div>

    <div class="rpt-body">
      <div class="rpt-sec">
        <h4 class="rpt-sec-title"><span class="rpt-num">1</span>综合结论</h4>
        <p class="rpt-p">{{ report.overview?.conclusion || '暂无结论数据。' }}</p>
        <div class="rpt-kpi-row">
          <div v-if="report.overview?.totalBuiltArea != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.overview.totalBuiltArea }}<span class="rpt-kpi-u">km²</span></span>
            <span class="rpt-kpi-l">建设用地总面积</span>
          </div>
          <div v-if="report.overview?.newConstruction != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.overview.newConstruction }}<span class="rpt-kpi-u">km²</span></span>
            <span class="rpt-kpi-l">新增建设面积<MockBadge v-if="report.overview.mock?.newConstruction" /></span>
          </div>
          <div v-if="report.overview?.expansionRate != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.overview.expansionRate }}<span class="rpt-kpi-u">%</span></span>
            <span class="rpt-kpi-l">年均扩张速率<MockBadge v-if="report.overview.mock?.expansionRate" /></span>
          </div>
          <div v-if="report.overview?.rseiMean != null" class="rpt-kpi">
            <span class="rpt-kpi-v" :class="rseiClass">{{ report.overview.rseiMean }}</span>
            <span class="rpt-kpi-l">RSEI 均值 ({{ report.overview.rseiGradeLabel || '—' }})</span>
          </div>
          <div v-if="report.overview?.population != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.overview.population }}<span class="rpt-kpi-u">万人</span></span>
            <span class="rpt-kpi-l">常住人口</span>
          </div>
          <div v-if="report.overview?.gdp != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.overview.gdp }}<span class="rpt-kpi-u">亿元</span></span>
            <span class="rpt-kpi-l">GDP 总量</span>
          </div>
        </div>
        <p v-if="report.overview?.singleYearNote" class="rpt-note">{{ report.overview.singleYearNote }}</p>
      </div>

      <div class="rpt-sec">
        <h4 class="rpt-sec-title"><span class="rpt-num">2</span>建设用地扩张</h4>
        <p class="rpt-p">{{ report.expansion?.description || '暂无数据。' }}</p>
        <div class="rpt-kpi-row">
          <div v-if="report.expansion?.totalArea != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.expansion.totalArea }}<span class="rpt-kpi-u">km²</span></span>
            <span class="rpt-kpi-l">总面积</span>
          </div>
          <div v-if="report.expansion?.newArea != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.expansion.newArea }}<span class="rpt-kpi-u">km²</span></span>
            <span class="rpt-kpi-l">新增面积<MockBadge v-if="report.expansion.mock?.newArea" /></span>
          </div>
          <div v-if="report.expansion?.patches != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.expansion.patches }}</span>
            <span class="rpt-kpi-l">建设斑块数</span>
            <span class="rpt-kpi-sub">面积÷平均斑块尺度（0.5 km²）</span>
          </div>
          <div v-if="report.expansion?.expansionRate != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.expansion.expansionRate }}<span class="rpt-kpi-u">%</span></span>
            <span class="rpt-kpi-l">扩张速率 (CAGR)<MockBadge v-if="report.expansion.mock?.expansionRate" /></span>
          </div>
        </div>
        <div v-if="report.expansion?.districtRanking?.length" class="rpt-chart-wrap">
          <h5 class="rpt-chart-lbl">区县建设用地排名</h5>
          <div :ref="chartRefs.reportRank" class="rpt-chart" />
        </div>
      </div>

      <div class="rpt-sec">
        <h4 class="rpt-sec-title"><span class="rpt-num">3</span>生态响应</h4>
        <p class="rpt-p">{{ report.ecology?.description || '暂无数据。' }}</p>
        <div class="rpt-kpi-row">
          <div v-if="report.ecology?.rseiMean != null" class="rpt-kpi">
            <span class="rpt-kpi-v" :class="rseiClass">{{ report.ecology.rseiMean }}</span>
            <span class="rpt-kpi-l">RSEI 均值 ({{ report.ecology.rseiGradeLabel || '—' }})</span>
          </div>
          <div v-if="report.ecology?.rseiChange != null" class="rpt-kpi">
            <span class="rpt-kpi-v" :class="report.ecology.rseiChange > 0 ? 'val-green' : 'val-red'">
              {{ report.ecology.rseiChange > 0 ? '+' : '' }}{{ report.ecology.rseiChange }}
            </span>
            <span class="rpt-kpi-l">{{ report.ecology.changeDirection || 'RSEI 变化' }}</span>
          </div>
        </div>
        <div v-if="report.ecology?.trendData?.length > 1" class="rpt-chart-wrap">
          <h5 class="rpt-chart-lbl">RSEI 时序变化</h5>
          <div :ref="chartRefs.reportRsei" class="rpt-chart" />
        </div>
        <div v-if="report.ecology?.gradeDistribution?.length" class="rpt-chart-wrap">
          <h5 class="rpt-chart-lbl">生态等级分布</h5>
          <div :ref="chartRefs.reportGrade" class="rpt-chart" />
        </div>
        <div v-if="report.ecology?.changeDistribution?.length" class="rpt-chart-wrap">
          <h5 class="rpt-chart-lbl">生态变化面积分布</h5>
          <div :ref="chartRefs.reportChange" class="rpt-chart" />
        </div>
      </div>

      <div class="rpt-sec">
        <h4 class="rpt-sec-title"><span class="rpt-num">4</span>社会经济</h4>
        <p class="rpt-p">{{ report.socio?.description || '暂无数据。' }}</p>
        <div class="rpt-kpi-row">
          <div v-if="report.socio?.population?.total != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.socio.population.total }}<span class="rpt-kpi-u">万人</span></span>
            <span class="rpt-kpi-l">常住人口<span v-if="report.socio.population.growth != null">({{ report.socio.population.growth }}%/年)</span></span>
          </div>
          <div v-if="report.socio?.gdp?.total != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.socio.gdp.total }}<span class="rpt-kpi-u">亿人民币</span></span>
            <span class="rpt-kpi-l">GDP 总量 (PPP)<span v-if="report.socio.gdp.growth != null">({{ report.socio.gdp.growth }}%/年)</span></span>
          </div>
          <div v-if="report.socio?.gdp?.perCapita != null" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.socio.gdp.perCapita }}<span class="rpt-kpi-u">万元</span></span>
            <span class="rpt-kpi-l">人均 GDP</span>
          </div>
        </div>
        <div v-if="report.socio?.gdp?.structure?.length" class="rpt-chart-wrap">
          <h5 class="rpt-chart-lbl">产业结构<MockBadge v-if="report.socio.mock?.industryStructure" /></h5>
          <div :ref="chartRefs.reportIndustry" class="rpt-chart" style="height:140px" />
        </div>
      </div>

      <div class="rpt-sec">
        <h4 class="rpt-sec-title"><span class="rpt-num">5</span>耦合关系</h4>
        <p class="rpt-p">{{ couplingText }}</p>
        <div v-if="report.coupling?.correlation != null" class="rpt-kpi-row">
          <div class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.coupling.correlation }}</span>
            <span class="rpt-kpi-l">扩张-生态相关系数</span>
          </div>
          <div v-if="report.coupling.strongNegativeCount" class="rpt-kpi">
            <span class="rpt-kpi-v">{{ report.coupling.strongNegativeCount }}</span>
            <span class="rpt-kpi-l">强负相关区县数</span>
          </div>
        </div>
      </div>

      <div class="rpt-sec">
        <h4 class="rpt-sec-title"><span class="rpt-num">6</span>数据说明</h4>
        <div v-if="report.meta?.data_sources?.length || report.overview?.dataSources?.length" class="rpt-src-row">
          <span class="rpt-src-lbl">数据来源：</span>
          <span v-for="src in (report.meta?.data_sources || report.overview?.dataSources)" :key="src" class="rpt-src-tag">{{ src }}</span>
        </div>
        <p class="rpt-disc">
          本报告基于遥感影像反演与栅格统计数据自动生成。部分指标（标注"估算数据"）为经验公式或统计模型估算值，仅供参考。GDP 数据采用购买力平价（PPP）换算，汇率为 {{ GDP_RATE }}。
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MockBadge from '../common/MockBadge.vue'

const GDP_RATE = 4.2

const props = defineProps({
  report: { type: Object, default: null },
  chartRefs: {
    type: Object,
    default: () => ({
      reportRank: () => {},
      reportRsei: () => {},
      reportGrade: () => {},
      reportChange: () => {},
      reportIndustry: () => {},
    }),
  },
})

const emit = defineEmits(['open-report'])

const couplingText = computed(() => {
  const c = props.report?.coupling
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

const rseiClass = computed(() => {
  const grade = props.report?.overview?.rseiGrade || props.report?.ecology?.rseiGrade
  const classByGrade = {
    excellent: 'val-excellent',
    good: 'val-green',
    moderate: 'val-moderate',
    poor: 'val-orange',
    bad: 'val-red',
  }
  if (classByGrade[grade]) return classByGrade[grade]

  const mean = props.report?.overview?.rseiMean ?? props.report?.ecology?.rseiMean
  const numericMean = Number(mean)
  if (!Number.isFinite(numericMean)) return ''
  if (numericMean >= 0.75) return 'val-excellent'
  if (numericMean >= 0.55) return 'val-green'
  if (numericMean >= 0.35) return 'val-moderate'
  if (numericMean >= 0.2) return 'val-orange'
  return 'val-red'
})
</script>
