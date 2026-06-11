import assert from 'node:assert/strict'
import test from 'node:test'

import { isNearby, toTileCoord } from '../../src/composables/useCustomAreaMap.js'

test('converts longitude and latitude to slippy-map tile coordinates', () => {
  const coord = toTileCoord([0, 0], 1)

  assert.equal(coord.x, 1)
  assert.equal(coord.y, 1)
})

test('treats close map camera targets as nearby', () => {
  assert.equal(isNearby([116.4, 39.9], [116.5, 39.95], 8, 8), true)
})

test('treats distant map camera targets as not nearby', () => {
  assert.equal(isNearby([116.4, 39.9], [121.5, 31.2], 8, 8), false)
})
