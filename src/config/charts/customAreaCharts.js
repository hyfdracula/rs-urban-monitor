const transparent = { backgroundColor: 'transparent' }

const axisLine = { lineStyle: { color: '#444' } }
const splitLine = { lineStyle: { color: '#333' } }
const reportSplitLine = { lineStyle: { color: '#2a2a2a' } }

const compactGrid = { left: '3%', right: '4%', bottom: '3%', top: '3%', containLabel: true }
const defaultGrid = { left: '3%', right: '4%', bottom: '3%', top: '12%', containLabel: true }

function linearGradient(x, y, x2, y2, colorStops) {
  return { type: 'linear', x, y, x2, y2, colorStops }
}

function valueAxis(axisLabel = { color: '#888', fontSize: 10 }) {
  return {
    type: 'value',
    axisLine,
    axisLabel,
    splitLine,
  }
}

function categoryAxis(data, axisLabel = { color: '#ccc', fontSize: 11 }) {
  return {
    type: 'category',
    data,
    axisLine,
    axisLabel,
    axisTick: { show: false },
  }
}

function reportAxis(extra = {}) {
  return {
    axisLabel: { color: '#aaa' },
    axisLine,
    splitLine: reportSplitLine,
    ...extra,
  }
}

function horizontalBarSeries(data, colors, borderRadius = [0, 3, 3, 0]) {
  return [{
    type: 'bar',
    data,
    itemStyle: {
      color: linearGradient(0, 0, 1, 0, [
        { offset: 0, color: colors[0] },
        { offset: 1, color: colors[1] },
      ]),
      borderRadius,
    },
    barWidth: '60%',
  }]
}

export function buildEcologyGradeOption(gradeData) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p) => `${p[0].name}<br/>面积: ${p[0].value} km²` },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: gradeData.map(d => d.grade + '\n' + (d.range || '')),
      axisLine,
      axisLabel: { color: '#ccc', fontSize: 10, lineHeight: 14 },
      name: '生态等级',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { color: '#888', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      name: '面积 (km²)',
      nameTextStyle: { color: '#888', fontSize: 10 },
      axisLabel: { color: '#888', fontSize: 10 },
      splitLine,
    },
    series: [{
      type: 'bar',
      barWidth: '50%',
      data: gradeData.map(d => ({ value: d.area, itemStyle: { color: d.color, borderRadius: [3, 3, 0, 0] } })),
    }],
  }
}

export function buildEcologyTrendOption(trendData) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: trendData.map(d => d.year), axisLine, axisLabel: { color: '#ccc', fontSize: 11 } },
    yAxis: { type: 'value', min: 0, max: 1, axisLabel: { color: '#888', fontSize: 10 }, splitLine },
    series: [{
      type: 'line',
      data: trendData.map(d => d.value),
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { color: '#51CF66', width: 2 },
      itemStyle: { color: '#51CF66' },
      areaStyle: {
        color: linearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(81,207,102,0.3)' },
          { offset: 1, color: 'rgba(81,207,102,0.05)' },
        ]),
      },
    }],
  }
}

export function buildEcologyChangeOption(changeDistribution) {
  return {
    ...transparent,
    tooltip: { trigger: 'item', formatter: '{b}: {c} km²' },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#1a1a1a', borderWidth: 2 },
      label: { show: true, fontSize: 10, color: '#ccc', formatter: '{b}\n{c}km²' },
      labelLine: { lineStyle: { color: '#666' } },
      data: changeDistribution.map(d => ({ name: d.name, value: d.area, itemStyle: { color: d.color } })),
    }],
  }
}

export function buildEcologyRadarOption(fourIndicators, studyArea = '研究区') {
  return {
    ...transparent,
    tooltip: {},
    radar: {
      center: ['50%', '50%'],
      radius: '60%',
      indicator: [
        { name: 'NDVI/绿度', max: 1 },
        { name: 'Wet/湿度', max: 1 },
        { name: 'NDBSI/干度', max: 1 },
        { name: 'LST/热度', max: 1 },
      ],
      axisName: { color: '#aaa', fontSize: 10 },
      shape: 'circle',
      splitNumber: 4,
      axisLine,
      splitLine,
      splitArea: { areaStyle: { color: ['#1a1a1a', '#1a1a1a'] } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [fourIndicators.ndvi || 0, fourIndicators.wet || 0, fourIndicators.ndbsi || 0, fourIndicators.lst || 0],
        name: studyArea || '研究区',
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 1.5, color: '#51CF66' },
        areaStyle: { color: 'rgba(81,207,102,0.2)' },
        itemStyle: { color: '#51CF66' },
      }],
    }],
  }
}

export function buildExpansionDistrictBarOption(districtData) {
  const data = districtData.map(d => d.value).reverse()

  return {
    ...transparent,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: compactGrid,
    xAxis: valueAxis(),
    yAxis: categoryAxis(districtData.map(d => d.name).reverse()),
    series: horizontalBarSeries(data, ['#FF6B6B', '#FFA94D']),
  }
}

export function buildIndustryPieOption(industryStructure) {
  return {
    ...transparent,
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '50%'],
      itemStyle: { borderRadius: 4, borderColor: '#1a1a1a', borderWidth: 2 },
      label: { show: true, fontSize: 11, color: '#ccc', formatter: '{b}\n{c}%' },
      labelLine: { lineStyle: { color: '#666' } },
      data: industryStructure.map(d => ({ name: d.name, value: d.value, itemStyle: { color: d.color } })),
    }],
  }
}

export function buildPopulationBarOption(data) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: compactGrid,
    xAxis: valueAxis(),
    yAxis: categoryAxis(data.map(d => d.name).reverse(), { color: '#ccc', fontSize: 10 }),
    series: horizontalBarSeries(data.map(d => d.value).reverse(), ['#748FFC', '#4DABF7']),
  }
}

export function buildGdpBarOption(data) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (p) => `${p[0].name}<br/>GDP: ${p[0].value} 亿人民币` },
    grid: compactGrid,
    xAxis: valueAxis(),
    yAxis: categoryAxis(data.map(d => d.name).reverse(), { color: '#ccc', fontSize: 10 }),
    series: horizontalBarSeries(data.map(d => d.value).reverse(), ['#F783AC', '#FF6B6B']),
  }
}

export function buildCouplingScatterOption(scatterData) {
  return {
    ...transparent,
    tooltip: { trigger: 'item', formatter: (p) => `${p.data[2]}<br/>建设用地: ${p.data[0]} km²<br/>RSEI: ${p.data[1]}` },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '10%', containLabel: true },
    xAxis: { name: '建设用地(km²)', nameTextStyle: { color: '#888' }, axisLine, axisLabel: { color: '#888' }, splitLine },
    yAxis: { name: 'RSEI 均值', nameTextStyle: { color: '#888' }, axisLine, axisLabel: { color: '#888' }, splitLine },
    series: [{
      type: 'scatter',
      symbolSize: 16,
      data: scatterData.map(d => [d.expansionRate, d.rseiChange, d.name]),
      itemStyle: {
        color: (p) => {
          const y = p.data[1]
          return y < -0.05 ? '#FF6B6B' : y < -0.02 ? '#FFD43B' : '#69DB7C'
        },
      },
    }],
  }
}

export function buildReportRankOption(data) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '8%', bottom: '15%', top: '6%', containLabel: true },
    xAxis: { type: 'value', ...reportAxis() },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name).reverse(),
      ...reportAxis({ axisLabel: { color: '#aaa', fontSize: 11 } }),
    },
    series: [{
      type: 'bar',
      data: data.map(d => d.value).reverse(),
      itemStyle: {
        color: linearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#FF6B6B' },
          { offset: 1, color: '#FFA94D' },
        ]),
        borderRadius: [0, 4, 4, 0],
      },
    }],
  }
}

export function buildReportRseiTrendOption(trendData) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis' },
    grid: defaultGrid,
    xAxis: { type: 'category', data: trendData.map(d => d.year), ...reportAxis() },
    yAxis: { type: 'value', min: 0, max: 1, ...reportAxis() },
    series: [{
      type: 'line',
      data: trendData.map(d => d.value),
      smooth: true,
      lineStyle: { color: '#51CF66', width: 2 },
      itemStyle: { color: '#51CF66' },
      areaStyle: {
        color: linearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(81,207,102,0.25)' },
          { offset: 1, color: 'rgba(81,207,102,0.03)' },
        ]),
      },
    }],
  }
}

export function buildReportGradeOption(gradeDistribution) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis' },
    grid: defaultGrid,
    xAxis: { type: 'category', data: gradeDistribution.map(d => d.grade), ...reportAxis() },
    yAxis: { type: 'value', ...reportAxis() },
    series: [{ type: 'bar', barWidth: '50%', data: gradeDistribution.map(d => ({ value: d.area, itemStyle: { color: d.color } })) }],
  }
}

export function buildReportChangeOption(changeDistribution) {
  return {
    ...transparent,
    tooltip: { trigger: 'axis' },
    grid: defaultGrid,
    xAxis: { type: 'category', data: changeDistribution.map(d => d.name), ...reportAxis() },
    yAxis: { type: 'value', ...reportAxis() },
    series: [{ type: 'bar', barWidth: '50%', data: changeDistribution.map(d => ({ value: d.area, itemStyle: { color: d.color } })) }],
  }
}

export function buildReportIndustryOption(structure) {
  return {
    ...transparent,
    tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '55%'],
      data: structure.map(d => ({ name: d.name, value: d.value, itemStyle: { color: d.color } })),
      label: { color: '#ccc', fontSize: 11, formatter: '{b}\n{c}%' },
    }],
  }
}

