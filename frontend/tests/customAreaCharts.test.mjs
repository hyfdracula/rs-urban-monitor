import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildCouplingScatterOption,
  buildEcologyRadarOption,
  buildExpansionDistrictBarOption,
  buildReportRankOption,
} from '../../src/config/charts/customAreaCharts.js'

test('builds reversed district bar data for horizontal charts', () => {
  const option = buildExpansionDistrictBarOption([
    { name: 'A区', value: 10 },
    { name: 'B区', value: 20 },
  ])

  assert.deepEqual(option.yAxis.data, ['B区', 'A区'])
  assert.deepEqual(option.series[0].data, [20, 10])
  assert.equal(option.series[0].itemStyle.color.type, 'linear')
  assert.deepEqual(option.series[0].itemStyle.color.colorStops.map(stop => stop.color), ['#FF6B6B', '#FFA94D'])
})

test('fills missing radar indicator values with zero', () => {
  const option = buildEcologyRadarOption({ ndvi: 0.7, lst: 0.3 }, '测试区')

  assert.equal(option.series[0].data[0].name, '测试区')
  assert.deepEqual(option.series[0].data[0].value, [0.7, 0, 0, 0.3])
})

test('keeps coupling scatter color thresholds stable', () => {
  const option = buildCouplingScatterOption([
    { name: '低值', expansionRate: 1, rseiChange: -0.06 },
    { name: '中值', expansionRate: 2, rseiChange: -0.03 },
    { name: '高值', expansionRate: 3, rseiChange: 0.01 },
  ])
  const color = option.series[0].itemStyle.color

  assert.deepEqual(option.series[0].data[0], [1, -0.06, '低值'])
  assert.equal(color({ data: [1, -0.06] }), '#FF6B6B')
  assert.equal(color({ data: [2, -0.03] }), '#FFD43B')
  assert.equal(color({ data: [3, 0.01] }), '#69DB7C')
})

test('builds report rank bars with report-specific radius', () => {
  const option = buildReportRankOption([
    { name: '一区', value: 5 },
    { name: '二区', value: 8 },
  ])

  assert.deepEqual(option.yAxis.data, ['二区', '一区'])
  assert.deepEqual(option.series[0].data, [8, 5])
  assert.deepEqual(option.series[0].itemStyle.borderRadius, [0, 4, 4, 0])
})
