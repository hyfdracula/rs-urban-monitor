import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildYearLayerTransition,
  getYearLayer,
  getYearLayerId,
  syncVisibleYearLayers,
} from '../src/utils/timelineLayers.js'

test('finds the GeoServer layer for a time-aware group and year', () => {
  const layer = getYearLayer('construction-land', 2020)

  assert.deepEqual(layer, {
    groupId: 'construction-land',
    year: 2020,
    layerName: 'test_construction_2020',
  })
})

test('builds the map operations needed when the timeline year changes', () => {
  const transition = buildYearLayerTransition({
    groupId: 'rsei',
    fromYear: 2020,
    toYear: 2015,
  })

  assert.deepEqual(transition, {
    removeLayerIds: ['rsei-2020'],
    addLayer: {
      id: 'rsei-2015',
      layerName: 'rsei_2015',
      year: 2015,
    },
  })
})

test('ignores groups that do not have year-based layers', () => {
  const transition = buildYearLayerTransition({
    groupId: 'expansion-mode',
    fromYear: 2020,
    toYear: 2015,
  })

  assert.deepEqual(transition, {
    removeLayerIds: [],
    addLayer: null,
  })
})

test('removes every active stale year layer for the same group', () => {
  const transition = buildYearLayerTransition({
    groupId: 'construction-land',
    activeYears: [2005, 2010, 2020],
    toYear: 2015,
  })

  assert.deepEqual(transition.removeLayerIds, [
    'construction-land-2005',
    'construction-land-2010',
    'construction-land-2020',
  ])
  assert.deepEqual(transition.addLayer, {
    id: 'construction-land-2015',
    layerName: 'construction_land_2015',
    year: 2015,
  })
})

test('uses stable map layer ids for year layers', () => {
  assert.equal(getYearLayerId('population', 2005), 'population-2005')
})

test('marks only the selected timeline year visible in a layer group', () => {
  const group = {
    id: 'construction-land',
    layers: [
      { year: 2000, visible: false },
      { year: 2015, visible: false },
      { year: 2020, visible: true },
    ],
  }

  const activeYears = syncVisibleYearLayers(group, 2015)

  assert.deepEqual(activeYears, [2015])
  assert.deepEqual(
    group.layers.map(layer => ({ year: layer.year, visible: layer.visible })),
    [
      { year: 2000, visible: false },
      { year: 2015, visible: true },
      { year: 2020, visible: false },
    ],
  )
})
