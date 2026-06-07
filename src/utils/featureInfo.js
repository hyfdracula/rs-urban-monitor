import { getWmsFeatureInfo } from './geoserver'
import { DISTRICTS } from '../data/districts'

/**
 * Unified feature info query.
 * GeoServer first → mock fallback if empty.
 * Returns always { area, year, mode, city, category } shape.
 */
export async function queryFeature(lngLat) {
  // 1. Try GeoServer for each layer
  const layers = [
    'construction_land_2020',
    'test_construction_2020',
  ]

  for (const layer of layers) {
    try {
      const data = await getWmsFeatureInfo(layer, { lng: lngLat.lng, lat: lngLat.lat })
      if (data?.features?.length > 0) {
        return parseGeoServerResponse(data.features[0])
      }
    } catch {
      // try next layer or fallback
    }
  }

  // 2. Mock fallback — generates plausible data based on click location
  return mockFeature(lngLat)
}

function parseGeoServerResponse(feature) {
  const props = feature.properties || {}
  return {
    area: props.area || props.area_km2 || 0,
    year: props.year || props.period || 2020,
    mode: props.mode || props.expansion_type || '边缘扩张',
    city: props.city || props.district || '',
    category: '建设用地',
    source: 'geoserver',
  }
}

function mockFeature(lngLat) {
  // Find nearest city from DISTRICTS based on click position
  let nearest = DISTRICTS[0]
  let minDist = Infinity
  for (const d of DISTRICTS) {
    const dist = Math.hypot(d.center[0] - lngLat.lng, d.center[1] - lngLat.lat)
    if (dist < minDist) {
      minDist = dist
      nearest = d
    }
  }

  const modes = ['边缘扩张', '填充式扩张', '飞地式扩张']
  const years = [2000, 2005, 2010, 2015, 2020]
  const area = (Math.random() * 3 + 0.2).toFixed(2)

  return {
    area: parseFloat(area),
    year: years[Math.floor(Math.random() * years.length)],
    mode: modes[Math.floor(Math.random() * modes.length)],
    city: nearest.name,
    category: '建设用地',
    source: 'mock',
  }
}
