<template>
  <div v-if="computing" class="progress-overlay">
    <h4>计算进度</h4>
    <el-progress :percentage="progressData.percent" :status="progressStatus" :stroke-width="10" />
    <p class="progress-step">{{ progressData.step || '准备中...' }}</p>
    <p class="progress-warn">⚠️ 计算正在进行，请勿离开页面</p>
    <el-button type="danger" size="small" plain @click="emit('cancel')">取消计算</el-button>
  </div>

  <div v-if="report && !computing" class="overview-section">
    <div class="report-header">
      <div class="header-row">
        <span class="header-title">{{ overview.studyArea || '自定义研究区' }}</span>
        <span class="rsei-badge" :class="overview.rseiGrade">{{ overview.rseiGradeLabel || '—' }}</span>
      </div>
      <div class="header-meta">
        <span v-if="overview.yearRange" class="meta-tag">📅 {{ overview.yearRange }}</span>
        <span v-if="overview.totalBuiltArea" class="meta-tag">🏗️ 建设用地 {{ fmt(overview.totalBuiltArea) }} km²</span>
        <span v-if="overview.gdp" class="meta-tag">💰 GDP {{ overview.gdp }} 亿元</span>
      </div>
    </div>

    <div class="conclusion-box" v-if="overview.conclusion">
      <div class="conclusion-label">核心结论</div>
      <p class="conclusion-text">{{ overview.conclusion }}</p>
    </div>

    <div class="overview-grid">
      <div class="ind-card">
        <span class="ind-label">研究区域</span>
        <span class="ind-value ind-name">{{ overview.studyArea || '—' }}</span>
      </div>
      <div class="ind-card">
        <div class="ind-head">
          <span class="ind-label">新增建设用地</span>
          <MockBadge v-if="overview.mock?.newConstruction" />
        </div>
        <span class="ind-value">{{ fmt(overview.newConstruction) }} <span class="ind-unit">km²</span></span>
      </div>
      <div class="ind-card">
        <div class="ind-head">
          <span class="ind-label">年均扩张速率</span>
          <MockBadge v-if="overview.mock?.expansionRate" />
        </div>
        <span class="ind-value">{{ fmt(overview.expansionRate) }} <span class="ind-unit">%</span></span>
      </div>
      <div class="ind-card">
        <span class="ind-label">RSEI 均值</span>
        <span class="ind-value">{{ fmt(overview.rseiMean, 3) }}</span>
      </div>
      <div class="ind-card">
        <div class="ind-head">
          <span class="ind-label">生态改善面积</span>
          <MockBadge v-if="overview.mock?.improvedArea" />
        </div>
        <span class="ind-value eco-good">{{ fmt(overview.improvedArea) }} <span class="ind-unit">km²</span></span>
      </div>
      <div class="ind-card">
        <div class="ind-head">
          <span class="ind-label">生态退化面积</span>
          <MockBadge v-if="overview.mock?.degradedArea" />
        </div>
        <span class="ind-value eco-bad">{{ fmt(overview.degradedArea) }} <span class="ind-unit">km²</span></span>
      </div>
      <div class="ind-card">
        <span class="ind-label">常住人口</span>
        <span class="ind-value">{{ fmt(overview.population) }} <span class="ind-unit">万</span></span>
      </div>
      <div class="ind-card">
        <span class="ind-label">GDP（亿人民币）</span>
        <span class="ind-value">{{ overview.gdp || '—' }}</span>
      </div>
    </div>

    <div class="data-sources" v-if="overview.dataSources?.length">
      <span class="src-label">数据来源：</span>
      <span class="src-tag" v-for="src in overview.dataSources" :key="src">{{ src }}</span>
    </div>

    <el-alert v-if="overview.singleYearNote" type="info" :closable="false" style="margin-top:8px">
      {{ overview.singleYearNote }}
    </el-alert>
  </div>
</template>

<script setup>
import MockBadge from '../common/MockBadge.vue'

defineProps({
  computing: { type: Boolean, default: false },
  progressData: { type: Object, default: () => ({ percent: 0, step: '' }) },
  progressStatus: { type: String, default: '' },
  report: { type: Object, default: null },
  overview: { type: Object, default: () => ({}) },
  fmt: {
    type: Function,
    default: (val, dec = 1) => {
      if (val === null || val === undefined || val === '') return '—'
      return typeof val === 'number' ? val.toFixed(dec) : val
    },
  },
})

const emit = defineEmits(['cancel'])
</script>
