<template>
  <div class="panel-content" v-if="!report">
    <p class="hint">请先选择研究区</p>
  </div>
  <div class="panel-content" v-else>
    <h3 class="panel-title">建设用地</h3>
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-lbl">总面积</div>
        <div class="stat-val">{{ fmt(report.expansion?.totalArea) }} <span class="stat-unit">km²</span></div>
        <div class="stat-note" v-if="report.expansion?.totalAreaDesc">{{ report.expansion.totalAreaDesc }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-head-row">
          <span class="stat-lbl">新增面积</span>
          <MockBadge v-if="report.expansion?.mock?.newArea" />
        </div>
        <div class="stat-val">{{ fmt(report.expansion?.newArea) }} <span class="stat-unit">km²</span></div>
        <div class="stat-note" v-if="report.expansion?.newAreaDesc">{{ report.expansion.newAreaDesc }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-head-row"><span class="stat-lbl">斑块数</span></div>
        <div class="stat-val">{{ report.expansion?.patches || '—' }}</div>
        <div class="stat-note">面积÷平均斑块尺度（0.5 km²）</div>
      </div>
      <div class="stat-card">
        <div class="stat-head-row">
          <span class="stat-lbl">年均扩张速率</span>
          <MockBadge v-if="report.expansion?.mock?.expansionRate" />
        </div>
        <div class="stat-val">{{ fmt(report.expansion?.expansionRate) }} <span class="stat-unit">%</span></div>
        <div class="stat-note" v-if="report.expansion?.expansionRateDesc">{{ report.expansion.expansionRateDesc }}</div>
      </div>
    </div>

    <div class="panel-desc" v-if="report.expansion?.description">
      <p>{{ report.expansion.description }}</p>
    </div>

    <el-alert v-if="report.expansion?.singleYearNote" type="info" :closable="false" style="margin-top:8px">
      {{ report.expansion.singleYearNote }}
    </el-alert>
    <div class="chart-section" v-if="report.expansion?.districtRanking?.length">
      <h4 class="sec-title">区县扩张排名</h4>
      <div :ref="chartRefs.expansion" class="chart-box" />
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
  chartRefs: {
    type: Object,
    default: () => ({
      expansion: () => {},
    }),
  },
})
</script>
