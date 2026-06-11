import assert from 'node:assert/strict'
import test from 'node:test'

import {
  addYearToSelection,
  analyzeDataAvailability,
  getGdpWarning,
  getLandsatSensor,
  isDisabledYearDate,
  removeYearFromSelection,
} from '../../src/utils/uploadYears.js'

test('maps years to expected Landsat sensors', () => {
  assert.equal(getLandsatSensor(2022), 'Landsat 9 OLI-2')
  assert.equal(getLandsatSensor(2015), 'Landsat 8 OLI')
  assert.equal(getLandsatSensor(2000), 'Landsat 7 ETM+')
  assert.equal(getLandsatSensor(1990), 'Landsat 5 TM')
})

test('builds data availability warnings for unsupported GDP years', () => {
  const result = analyzeDataAvailability([1985, 2013, 2024])

  assert.equal(result.hasBlocker, true)
  assert.equal(result.sensorMap[2013], 'Landsat 8 OLI')
  assert.ok(result.warnings.some(warning => warning.title === 'GDP 数据缺失'))
  assert.ok(getGdpWarning([2024]).includes('2024'))
})

test('adds, sorts, removes, and caps selected years', () => {
  const added = addYearToSelection([2020, 2000], new Date('2010-01-01'), 2026)
  assert.deepEqual(added, { years: [2000, 2010, 2020], warning: '' })

  const capped = addYearToSelection([2000, 2005, 2010, 2015, 2020], new Date('2021-01-01'), 2026)
  assert.equal(capped.warning, '最多选择5个年份')
  assert.deepEqual(capped.years, [2000, 2005, 2010, 2015, 2020])

  assert.deepEqual(removeYearFromSelection([2000, 2010, 2020], 2010), [2000, 2020])
})

test('rejects dates outside the supported year range', () => {
  assert.equal(isDisabledYearDate(new Date('1983-01-01'), 2026), true)
  assert.equal(isDisabledYearDate(new Date('2027-01-01'), 2026), true)
  assert.equal(isDisabledYearDate(new Date('2020-01-01'), 2026), false)
})
