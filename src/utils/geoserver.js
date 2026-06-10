import axios from 'axios'
import { GEOSERVER_CONFIG } from '../config/map.js'

// GeoServer WMS request helper
const geoserverClient = axios.create({
  baseURL: GEOSERVER_CONFIG.baseUrl,
  timeout: 30000,
})

/**
 * Build WMS tile URL for Mapbox raster source
 */
export function buildWmsTileUrl(layerName, options = {}) {
  // Manually build URL — avoid URLSearchParams which encodes {bbox-epsg-3857}
  const style = options.style || ''
  const fmt = options.format || 'image/png'
  return `${GEOSERVER_CONFIG.wmsUrl}?service=WMS&version=1.1.1&request=GetMap&layers=${encodeURIComponent(GEOSERVER_CONFIG.workspace + ':' + layerName)}&styles=${encodeURIComponent(style)}&srs=EPSG:3857&format=${encodeURIComponent(fmt)}&transparent=true&width=256&height=256&bbox={bbox-epsg-3857}`
}

/**
 * Normalize a backend WMS GetMap URL into a Mapbox raster tile URL.
 * Backend report URLs are single-image WMS templates; Mapbox needs WebMercator
 * tile bboxes and a transparent 256px image per tile.
 */
export function buildWmsTileUrlFromUrl(wmsUrl) {
  const fallback = `${wmsUrl}${wmsUrl?.includes('?') ? '&' : '?'}bbox={bbox-epsg-3857}`

  try {
    const origin = typeof window === 'undefined' ? GEOSERVER_CONFIG.wmsUrl : window.location.origin
    const parsed = new URL(wmsUrl, origin)
    const layers = parsed.searchParams.get('layers')
    if (!layers) return fallback

    const styles = parsed.searchParams.get('styles') || ''
    const format = parsed.searchParams.get('format') || 'image/png'
    return [
      `${GEOSERVER_CONFIG.wmsUrl}?service=WMS`,
      'version=1.1.1',
      'request=GetMap',
      `layers=${encodeURIComponent(layers)}`,
      `styles=${encodeURIComponent(styles)}`,
      'srs=EPSG:3857',
      `format=${encodeURIComponent(format)}`,
      'transparent=true',
      'width=256',
      'height=256',
      'bbox={bbox-epsg-3857}',
    ].join('&')
  } catch {
    return fallback
  }
}

/**
 * Build TMS tile URL for Mapbox vector tile source
 */
export function buildTmsTileUrl(layerName) {
  return `${GEOSERVER_CONFIG.tmsUrl}/${GEOSERVER_CONFIG.workspace}:${layerName}@EPSG:900913@png/{z}/{x}/{y}.png`
}

/**
 * Get feature info from WMS (click query)
 */
export async function getWmsFeatureInfo(layerName, lngLat, options = {}) {
  const params = new URLSearchParams({
    service: 'WMS',
    version: '1.1.1',
    request: 'GetFeatureInfo',
    layers: `${GEOSERVER_CONFIG.workspace}:${layerName}`,
    query_layers: `${GEOSERVER_CONFIG.workspace}:${layerName}`,
    srs: 'EPSG:4326',
    bbox: `${lngLat.lng - 0.01},${lngLat.lat - 0.01},${lngLat.lng + 0.01},${lngLat.lat + 0.01}`,
    width: '256',
    height: '256',
    x: '128',
    y: '128',
    info_format: options.format || 'application/json',
    feature_count: options.count || 10,
  })
  const response = await geoserverClient.get(`/wms?${params.toString()}`)
  return response.data
}

/**
 * Get WFS feature data for charts
 */
export async function getWfsFeatures(layerName, options = {}) {
  const params = new URLSearchParams({
    service: 'WFS',
    version: '1.0.0',
    request: 'GetFeature',
    typeName: `${GEOSERVER_CONFIG.workspace}:${layerName}`,
    outputFormat: 'application/json',
    maxFeatures: options.maxFeatures || 1000,
  })
  if (options.cql_filter) {
    params.append('cql_filter', options.cql_filter)
  }
  if (options.sortBy) {
    params.append('sortBy', options.sortBy)
  }
  const response = await geoserverClient.get(`/wfs?${params.toString()}`)
  return response.data
}

/**
 * Get layer legend from GeoServer
 */
export function getLegendUrl(layerName, options = {}) {
  const params = new URLSearchParams({
    service: 'WMS',
    version: '1.1.1',
    request: 'GetLegendGraphic',
    layer: `${GEOSERVER_CONFIG.workspace}:${layerName}`,
    format: 'image/png',
    width: '20',
    height: '20',
  })
  if (options.style) {
    params.append('style', options.style)
  }
  return `${GEOSERVER_CONFIG.wmsUrl}?${params.toString()}`
}

export default geoserverClient
