import assert from 'node:assert/strict'
import test from 'node:test'

import { nextCustomLayerLoadState } from '../../src/utils/customLayerState.js'

test('keeps custom layer options when map is not ready yet', () => {
  const layers = [
    { type: 'built_2020', label: '建设用地 2020', wms_url: 'http://example.test/wms' },
  ]

  const state = nextCustomLayerLoadState(layers, false)

  assert.deepEqual(state.mapLayers, layers)
  assert.deepEqual(state.pendingLayers, layers)
  assert.equal(state.shouldRegister, false)
})

test('registers custom layers immediately when map is ready', () => {
  const layers = [
    { type: 'rsei_2020', label: 'RSEI 2020', wms_url: 'http://example.test/wms' },
  ]

  const state = nextCustomLayerLoadState(layers, true)

  assert.deepEqual(state.mapLayers, layers)
  assert.deepEqual(state.pendingLayers, [])
  assert.equal(state.shouldRegister, true)
})
