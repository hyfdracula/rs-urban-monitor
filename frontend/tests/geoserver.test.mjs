import assert from 'node:assert/strict'
import test from 'node:test'

import { buildWmsTileUrlFromUrl } from '../../src/utils/geoserver.js'

test('normalizes backend WMS urls for Mapbox raster tiles', () => {
  const tileUrl = buildWmsTileUrlFromUrl(
    'http://localhost:8080/geoserver/ueea2601/wms?service=WMS&version=1.1.0&request=GetMap&layers=ueea2601:b46_rsei_2020&styles=&width=512&height=512&srs=EPSG:4326&format=image/png',
  )

  assert.match(tileUrl, /^http:\/\/127\.0\.0\.1:5173\/geoserver\/ueea2601\/wms\?/)
  assert.match(tileUrl, /version=1\.1\.1/)
  assert.match(tileUrl, /layers=ueea2601%3Ab46_rsei_2020/)
  assert.match(tileUrl, /srs=EPSG:3857/)
  assert.match(tileUrl, /transparent=true/)
  assert.match(tileUrl, /width=256/)
  assert.match(tileUrl, /height=256/)
  assert.match(tileUrl, /bbox=\{bbox-epsg-3857\}/)
  assert.doesNotMatch(tileUrl, /EPSG:4326/)
})
