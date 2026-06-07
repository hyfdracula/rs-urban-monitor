import assert from 'node:assert/strict'
import test from 'node:test'

import {
  getEcologyData,
  getExpansionData,
  getReportData,
} from '../src/data/mockAnalysis.js'

test('mock analysis data provides shared expansion, ecology, and report datasets', () => {
  const expansion = getExpansionData()
  const ecology = getEcologyData()
  const report = getReportData()

  assert.equal(expansion.totalArea, 1285.6)
  assert.equal(expansion.modeDistribution.length, 3)
  assert.deepEqual(expansion.districtRanking[0].center, [121.47, 31.23])

  assert.equal(ecology.rseiMean, 0.55)
  assert.deepEqual(ecology.trendData.map(item => item.year), [2000, 2005, 2010, 2015, 2020])
  assert.equal(ecology.changeDistribution.length, 5)

  assert.equal(report.studyArea.length > 0, true)
  assert.equal(report.timeRange, '2000-2020')
  assert.deepEqual(
    report.modeDistribution.map(item => item.name),
    expansion.modeDistribution.map(item => item.name),
  )
  assert.deepEqual(
    report.rseiTrend.map(item => item.value),
    ecology.trendData.map(item => item.value),
  )
})
