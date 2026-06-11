import { nextTick, ref } from 'vue'
import echarts from '../utils/charts.js'
import {
  buildCouplingScatterOption,
  buildEcologyChangeOption,
  buildEcologyGradeOption,
  buildEcologyRadarOption,
  buildEcologyTrendOption,
  buildExpansionDistrictBarOption,
  buildGdpBarOption,
  buildIndustryPieOption,
  buildPopulationBarOption,
  buildReportChangeOption,
  buildReportGradeOption,
  buildReportIndustryOption,
  buildReportRankOption,
  buildReportRseiTrendOption,
} from '../config/charts/customAreaCharts.js'

export function useCustomAreaCharts({ report, overview }) {
  const gradeChartRef = ref(null)
  const trendChartRef = ref(null)
  const changeChartRef = ref(null)
  const radarChartRef = ref(null)
  const expBarChartRef = ref(null)
  const expModeBarRef = ref(null)
  const scatterChartRef = ref(null)
  const industryPieRef = ref(null)
  const popBarRef = ref(null)
  const gdpBarRef = ref(null)
  const chartInstances = []

  const rptRankChartRef = ref(null)
  const rptRseiChartRef = ref(null)
  const rptGradeChartRef = ref(null)
  const rptChangeChartRef = ref(null)
  const rptIndustryChartRef = ref(null)
  const rptChartInstances = []

  function disposeCharts() {
    chartInstances.forEach(i => { try { i.dispose() } catch {} })
    chartInstances.length = 0
  }

  function initChart(el) {
    if (!el) return null
    const inst = echarts.init(el)
    chartInstances.push(inst)
    return inst
  }

  function renderCharts() {
    disposeCharts()
    nextTick(() => {
      renderEcologyCharts()
      renderExpansionCharts()
      renderSocioCharts()
      renderCouplingChart()
    })
  }

  function renderEcologyCharts() {
    const eco = report.value?.ecology
    if (!eco) return

    if (gradeChartRef.value && eco.gradeDistribution?.length) {
      initChart(gradeChartRef.value).setOption(buildEcologyGradeOption(eco.gradeDistribution))
    }

    if (trendChartRef.value && eco.trendData?.length) {
      initChart(trendChartRef.value).setOption(buildEcologyTrendOption(eco.trendData))
    }

    if (changeChartRef.value && eco.changeDistribution?.length) {
      initChart(changeChartRef.value).setOption(buildEcologyChangeOption(eco.changeDistribution))
    }

    if (radarChartRef.value && eco.fourIndicators) {
      initChart(radarChartRef.value).setOption(buildEcologyRadarOption(eco.fourIndicators, overview.value.studyArea))
    }
  }

  function renderExpansionCharts() {
    const exp = report.value?.expansion
    if (!exp) return

    const districtData = exp.districtRanking?.slice(0, 15)
    if (expBarChartRef.value && districtData?.length) {
      initChart(expBarChartRef.value).setOption(buildExpansionDistrictBarOption(districtData))
    }
    if (expModeBarRef.value && districtData?.length) {
      initChart(expModeBarRef.value).setOption(buildExpansionDistrictBarOption(districtData))
    }
  }

  function renderSocioCharts() {
    const socio = report.value?.socio
    if (!socio) return

    if (industryPieRef.value && socio.industryStructure?.length) {
      initChart(industryPieRef.value).setOption(buildIndustryPieOption(socio.industryStructure))
    }

    if (popBarRef.value && socio.districtPopulation?.length) {
      initChart(popBarRef.value).setOption(buildPopulationBarOption(socio.districtPopulation.slice(0, 12)))
    }

    if (gdpBarRef.value && socio.districtGdp?.length) {
      initChart(gdpBarRef.value).setOption(buildGdpBarOption(socio.districtGdp.slice(0, 12)))
    }
  }

  function renderCouplingChart() {
    const coupling = report.value?.coupling
    if (!scatterChartRef.value || !coupling?.scatterData?.length) return

    initChart(scatterChartRef.value).setOption(buildCouplingScatterOption(coupling.scatterData))
  }

  function disposeReportCharts() {
    rptChartInstances.forEach(i => { try { i.dispose() } catch {} })
    rptChartInstances.length = 0
  }

  function initReportChart(el, height) {
    if (!el) return null
    if (height) el.style.height = `${height}px`
    const inst = echarts.init(el)
    rptChartInstances.push(inst)
    return inst
  }

  function renderReportCharts() {
    disposeReportCharts()
    nextTick(() => {
      if (rptRankChartRef.value && report.value?.expansion?.districtRanking?.length) {
        const data = report.value.expansion.districtRanking.slice(0, 12)
        const chartHeight = data.length * 28 + 20
        initReportChart(rptRankChartRef.value, chartHeight).setOption(buildReportRankOption(data))
      }

      if (rptRseiChartRef.value && report.value?.ecology?.trendData?.length > 1) {
        initReportChart(rptRseiChartRef.value).setOption(buildReportRseiTrendOption(report.value.ecology.trendData))
      }

      if (rptGradeChartRef.value && report.value?.ecology?.gradeDistribution?.length) {
        initReportChart(rptGradeChartRef.value).setOption(buildReportGradeOption(report.value.ecology.gradeDistribution))
      }

      if (rptChangeChartRef.value && report.value?.ecology?.changeDistribution?.length) {
        initReportChart(rptChangeChartRef.value).setOption(buildReportChangeOption(report.value.ecology.changeDistribution))
      }

      if (rptIndustryChartRef.value && report.value?.socio?.gdp?.structure?.length) {
        initReportChart(rptIndustryChartRef.value).setOption(buildReportIndustryOption(report.value.socio.gdp.structure))
      }
    })
  }

  const tabChartRenderers = {
    ecology: {
      getRefs: () => [gradeChartRef, trendChartRef, changeChartRef, radarChartRef],
      render: renderEcologyCharts,
    },
    construction: {
      getRefs: () => [expBarChartRef, expModeBarRef],
      render: renderExpansionCharts,
    },
    socio: {
      getRefs: () => [industryPieRef, popBarRef, gdpBarRef],
      render: renderSocioCharts,
    },
    report: {
      getRefs: () => [rptRankChartRef, rptRseiChartRef, rptGradeChartRef, rptChangeChartRef, rptIndustryChartRef],
      render: renderReportCharts,
      dispose: disposeReportCharts,
    },
  }

  function replayChartsForTab(tabKey) {
    const entry = tabChartRenderers[tabKey]
    if (!entry || !report.value) return
    if (entry.dispose) {
      entry.dispose()
    } else {
      const elements = new Set(entry.getRefs().map(r => r.value).filter(Boolean))
      for (let i = chartInstances.length - 1; i >= 0; i--) {
        const inst = chartInstances[i]
        let dom = null
        try { dom = inst.getDom() } catch { continue }
        if (dom && elements.has(dom)) {
          try { inst.dispose() } catch {}
          chartInstances.splice(i, 1)
        }
      }
    }
    nextTick(() => entry.render())
  }

  function resizeCharts() {
    nextTick(() => {
      chartInstances.forEach(i => i.resize())
      rptChartInstances.forEach(i => i.resize())
    })
  }

  function disposeAllCharts() {
    disposeCharts()
    disposeReportCharts()
  }

  return {
    gradeChartRef,
    trendChartRef,
    changeChartRef,
    radarChartRef,
    expBarChartRef,
    expModeBarRef,
    scatterChartRef,
    industryPieRef,
    popBarRef,
    gdpBarRef,
    rptRankChartRef,
    rptRseiChartRef,
    rptGradeChartRef,
    rptChangeChartRef,
    rptIndustryChartRef,
    renderCharts,
    replayChartsForTab,
    resizeCharts,
    disposeCharts: disposeAllCharts,
  }
}
