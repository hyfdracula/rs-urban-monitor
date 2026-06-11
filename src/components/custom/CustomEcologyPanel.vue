<template>
  <div class="panel-content" v-if="!report">
    <p class="hint">请先选择研究区</p>
  </div>
  <div class="panel-content" v-else>
    <h3 class="panel-title">生态评估</h3>

    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-head-row"><span class="stat-lbl">RSEI 均值</span></div>
        <div class="stat-val">{{ fmt(report.ecology?.rseiMean, 3) }}</div>
        <div class="stat-grade" v-if="report.ecology?.rseiGradeLabel">
          <span class="grade-badge" :class="report.ecology?.rseiGrade">{{ report.ecology.rseiGradeLabel }}</span>
          <span class="grade-hint">生态等级</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-head-row">
          <span class="stat-lbl">RSEI 变化</span>
          <MockBadge v-if="!report.ecology?.rseiChange && report.ecology?.rseiChange !== 0" />
        </div>
        <div class="stat-val" :style="{ color: rseiChangeColor }">{{ fmt(report.ecology?.rseiChange, 3) }}</div>
        <div
          class="stat-dir"
          v-if="report.ecology?.changeDirection"
          :class="{
            'dir-good': report.ecology.changeDirection.includes('改善'),
            'dir-bad': report.ecology.changeDirection.includes('退化'),
          }"
        >
          {{ report.ecology.changeDirection }}
        </div>
      </div>
    </div>

    <div class="panel-desc" v-if="report.ecology?.description">
      <p>{{ report.ecology.description }}</p>
    </div>

    <div class="chart-section">
      <h4 class="sec-title">生态等级分布</h4>
      <div :ref="chartRefs.grade" class="chart-box" />
    </div>
    <div class="chart-section">
      <h4 class="sec-title">RSEI 时序变化</h4>
      <div :ref="chartRefs.trend" class="chart-box" />
    </div>
    <div class="chart-section" v-if="report.ecology?.changeDistribution?.length">
      <h4 class="sec-title">生态变化面积</h4>
      <div :ref="chartRefs.change" class="chart-box" />
    </div>
    <div class="chart-section">
      <h4 class="sec-title">RSEI 四维指标</h4>
      <div :ref="chartRefs.radar" class="chart-box tall" />
    </div>
  </div>
</template>

<script setup>
import MockBadge from '../common/MockBadge.vue'

defineProps({
  report: { type: Object, default: null },
  fmt: {
    type: Function,
    default: (val, dec = 1) => {
      if (val === null || val === undefined || val === '') return '—'
      return typeof val === 'number' ? val.toFixed(dec) : val
    },
  },
  rseiChangeColor: { type: String, default: '' },
  chartRefs: {
    type: Object,
    default: () => ({
      grade: () => {},
      trend: () => {},
      change: () => {},
      radar: () => {},
    }),
  },
})
</script>
