<template>
  <div class="panel-content" v-if="!report">
    <p class="hint">请先选择研究区</p>
  </div>
  <div class="panel-content" v-else>
    <h3 class="panel-title">社会经济</h3>

    <div class="sub-section">
      <h4 class="sub-title">人口</h4>
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-val">{{ report.socio?.population?.total || '—' }}</div>
          <div class="stat-lbl">常住人口 <span class="unit-hint">(万人)</span></div>
        </div>
        <div class="stat-card">
          <div class="stat-head-row"><span class="stat-lbl">人口增长率</span></div>
          <div class="stat-val">{{ fmt(report.socio?.population?.growth) }} <span class="stat-unit">%</span></div>
          <div class="stat-note" v-if="report.socio?.population?.growthDesc">{{ report.socio.population.growthDesc }}</div>
        </div>
      </div>
    </div>

    <div class="sub-section">
      <h4 class="sub-title">GDP</h4>
      <div class="stat-cards">
        <div class="stat-card">
          <div class="stat-val">{{ report.socio?.gdp?.total || '—' }}</div>
          <div class="stat-lbl">GDP 总量 <span class="unit-hint">(亿人民币)</span></div>
        </div>
        <div class="stat-card">
          <div class="stat-val">{{ report.socio?.gdp?.perCapita || '—' }}</div>
          <div class="stat-lbl">人均 GDP <span class="unit-hint">(万元)</span></div>
        </div>
      </div>
      <div class="stat-cards" style="margin-top:8px">
        <div class="stat-card">
          <div class="stat-head-row"><span class="stat-lbl">总GDP增量</span></div>
          <div class="stat-val">{{ fmt(report.socio?.gdp?.increment) }} <span class="stat-unit">亿人民币</span></div>
          <div class="stat-note" v-if="report.socio?.gdp?.incrementDesc">{{ report.socio.gdp.incrementDesc }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-head-row"><span class="stat-lbl">GDP年增速</span></div>
          <div class="stat-val">{{ fmt(report.socio?.gdp?.growth) }} <span class="stat-unit">%</span></div>
          <div class="stat-note" v-if="report.socio?.gdp?.growthDesc">{{ report.socio.gdp.growthDesc }}</div>
        </div>
      </div>
    </div>

    <div class="panel-desc" v-if="report.socio?.description">
      <p>{{ report.socio.description }}</p>
    </div>

    <div class="chart-section" v-if="report.socio?.industryStructure?.length">
      <h4 class="sec-title">产业结构</h4>
      <div :ref="chartRefs.industry" class="chart-box" />
    </div>
    <div class="chart-section" v-if="report.socio?.districtPopulation?.length">
      <h4 class="sec-title">区县人口排名 <span class="unit-hint">(人)</span></h4>
      <div :ref="chartRefs.population" class="chart-box" />
    </div>
    <div class="chart-section" v-if="report.socio?.districtGdp?.length">
      <h4 class="sec-title">区县 GDP 排名 <span class="unit-hint">(亿人民币)</span></h4>
      <div :ref="chartRefs.gdp" class="chart-box" />
    </div>
  </div>
</template>

<script setup>
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
      industry: () => {},
      population: () => {},
      gdp: () => {},
    }),
  },
})
</script>
