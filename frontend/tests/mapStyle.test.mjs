import assert from 'node:assert/strict'
import test from 'node:test'

import {
  getInitialMapStyle,
  LOCAL_DARK_STYLE,
  MAPBOX_DARK_STYLE,
} from '../../src/utils/mapStyle.js'

test('uses the offline dark style when no Mapbox token is configured', () => {
  const style = getInitialMapStyle('')

  assert.equal(style, LOCAL_DARK_STYLE)
  assert.equal(style.version, 8)
  assert.equal(style.layers[0].type, 'background')
})

test('uses the offline style by default even when a Mapbox token is present', () => {
  assert.equal(getInitialMapStyle('pk.test-token'), LOCAL_DARK_STYLE)
})

test('uses the hosted Mapbox dark style only when explicitly enabled', () => {
  assert.equal(getInitialMapStyle('pk.test-token', true), MAPBOX_DARK_STYLE)
})
