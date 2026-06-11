import { ref } from 'vue'
import mapboxgl from 'mapbox-gl'

import { buildWmsTileUrlFromUrl } from '../utils/geoserver.js'
import { nextCustomLayerLoadState } from '../utils/customLayerState.js'

export function useCustomAreaMap() {
  const mapInstance = ref(null)
  const pendingBoundary = ref(null)
  const mapLayers = ref([])
  const visibleTypes = ref([])
  const pendingMapLayers = ref([])
  const addedLayerIds = []

  function onMapLoaded(map) {
    mapInstance.value = map
    if (pendingBoundary.value) {
      addBoundaryGeoJSON(pendingBoundary.value)
      pendingBoundary.value = null
    }
    if (pendingMapLayers.value.length) {
      const layers = pendingMapLayers.value
      pendingMapLayers.value = []
      registerMapLayers(layers)
    }
  }

  function addMapLayers(layers) {
    clearRegisteredMapLayers()
    const nextState = nextCustomLayerLoadState(layers, !!mapInstance.value)
    mapLayers.value = nextState.mapLayers
    pendingMapLayers.value = nextState.pendingLayers
    visibleTypes.value = []
    if (nextState.shouldRegister) registerMapLayers(nextState.mapLayers)
  }

  function registerMapLayers(layers) {
    if (!mapInstance.value) return

    for (const layer of layers) {
      if (!layer.wms_url) continue

      const sourceId = `custom-${layer.type}`
      const layerId = `custom-${layer.type}`
      mapInstance.value.addSource(sourceId, {
        type: 'raster',
        tiles: [buildWmsTileUrlFromUrl(layer.wms_url)],
        tileSize: 256,
      })
      mapInstance.value.addLayer({
        id: layerId,
        type: 'raster',
        source: sourceId,
        paint: { 'raster-opacity': 0.7 },
      })
      addedLayerIds.push(layerId)

      const isVisible = visibleTypes.value.includes(layer.type)
      mapInstance.value.setLayoutProperty(layerId, 'visibility', isVisible ? 'visible' : 'none')
    }
  }

  function clearRegisteredMapLayers() {
    if (!mapInstance.value) {
      addedLayerIds.length = 0
      return
    }

    for (const layerId of addedLayerIds) {
      let sourceId = null
      try { sourceId = mapInstance.value.getLayer(layerId)?.source } catch {}
      try { mapInstance.value.removeLayer(layerId) } catch {}
      if (sourceId) {
        try { mapInstance.value.removeSource(sourceId) } catch {}
      }
    }
    addedLayerIds.length = 0
  }

  function removeMapLayers() {
    pendingMapLayers.value = []
    clearRegisteredMapLayers()
    mapLayers.value = []
    visibleTypes.value = []
  }

  function onLayerToggle({ type, visible }) {
    if (!mapInstance.value) return

    const layerId = `custom-${type}`
    try {
      if (visible) {
        mapInstance.value.setLayoutProperty(layerId, 'visibility', 'visible')
        if (!visibleTypes.value.includes(type)) visibleTypes.value = [...visibleTypes.value, type]
      } else {
        mapInstance.value.setLayoutProperty(layerId, 'visibility', 'none')
        visibleTypes.value = visibleTypes.value.filter(t => t !== type)
      }
    } catch (error) {
      console.warn('layer toggle failed:', error)
    }
  }

  function removeBoundaryLayers() {
    if (!mapInstance.value) return

    try {
      if (mapInstance.value.getLayer('boundary-fill')) mapInstance.value.removeLayer('boundary-fill')
      if (mapInstance.value.getLayer('boundary-line')) mapInstance.value.removeLayer('boundary-line')
      if (mapInstance.value.getSource('boundary-src')) mapInstance.value.removeSource('boundary-src')
    } catch {}
  }

  function addBoundaryGeoJSON(geojson, onSettled) {
    if (!mapInstance.value) {
      pendingBoundary.value = geojson
      if (onSettled) onSettled()
      return
    }

    let bounds = null
    try {
      let coords = null
      if (geojson.type === 'FeatureCollection' && geojson.features?.[0]) coords = geojson.features[0].geometry.coordinates[0]
      else if (geojson.type === 'Polygon') coords = geojson.coordinates[0]
      else if (geojson.type === 'MultiPolygon') coords = geojson.coordinates[0][0]
      if (coords?.length) {
        bounds = new mapboxgl.LngLatBounds(coords[0], coords[0])
        for (const [lng, lat] of coords) bounds.extend([lng, lat])
      }
    } catch {}

    removeBoundaryLayers()

    let targetCamera = { center: [116.4, 39.9], zoom: 7 }
    if (bounds) {
      const camera = mapInstance.value.cameraForBounds(bounds, { padding: 80 })
      if (camera) targetCamera = camera
    }

    const currentCenter = mapInstance.value.getCenter()
    const near = isNearby(
      [currentCenter.lng, currentCenter.lat],
      [targetCamera.center[0], targetCamera.center[1]],
      mapInstance.value.getZoom(),
      targetCamera.zoom,
    )

    if (near) {
      mapInstance.value.flyTo({
        center: targetCamera.center,
        zoom: targetCamera.zoom,
        duration: 1500,
        essential: true,
      })
      mapInstance.value.once('moveend', () => {
        if (!mapInstance.value) return
        addBoundaryLayers(geojson, 0, 0)
        fadeBoundaryIn(0.15, 1, 600, onSettled)
      })
    } else {
      mapInstance.value.jumpTo({
        center: targetCamera.center,
        zoom: targetCamera.zoom,
      })
      addBoundaryLayers(geojson, 0, 0)
      fadeBoundaryIn(0.15, 1, 600, onSettled)
    }
  }

  function addBoundaryLayers(geojson, fillOpacity, lineOpacity) {
    if (!mapInstance.value) return

    try {
      let data = geojson
      if (geojson.type === 'Polygon' || geojson.type === 'MultiPolygon') {
        data = { type: 'FeatureCollection', features: [{ type: 'Feature', properties: {}, geometry: geojson }] }
      }
      mapInstance.value.addSource('boundary-src', { type: 'geojson', data })
      mapInstance.value.addLayer({
        id: 'boundary-fill',
        type: 'fill',
        source: 'boundary-src',
        paint: { 'fill-color': '#FF9F43', 'fill-opacity': fillOpacity },
      })
      mapInstance.value.addLayer({
        id: 'boundary-line',
        type: 'line',
        source: 'boundary-src',
        paint: { 'line-color': '#FF9F43', 'line-width': 2, 'line-opacity': lineOpacity },
      })
    } catch (error) {
      console.warn('boundary error:', error)
    }
  }

  function fadeBoundaryIn(fillTarget, lineTarget, duration, onDone) {
    const start = performance.now()

    function animate(now) {
      const t = Math.min((now - start) / duration, 1)
      const ease = t * (2 - t)
      if (mapInstance.value) {
        try {
          mapInstance.value.setPaintProperty('boundary-fill', 'fill-opacity', fillTarget * ease)
          mapInstance.value.setPaintProperty('boundary-line', 'line-opacity', lineTarget * ease)
        } catch {}
      }
      if (t < 1) requestAnimationFrame(animate)
      else if (onDone) requestAnimationFrame(() => onDone())
    }

    requestAnimationFrame(animate)
  }

  return {
    mapLayers,
    visibleTypes,
    onMapLoaded,
    addMapLayers,
    removeMapLayers,
    onLayerToggle,
    addBoundaryGeoJSON,
  }
}

export function isNearby(center1, center2, zoom1, zoom2) {
  const refZoom = 8
  const t1 = toTileCoord(center1, refZoom)
  const t2 = toTileCoord(center2, refZoom)
  const tileDist = Math.max(Math.abs(t1.x - t2.x), Math.abs(t1.y - t2.y))
  const zoomDiff = Math.abs(zoom1 - zoom2)
  return tileDist <= 2 && zoomDiff <= 1
}

export function toTileCoord([lng, lat], zoom) {
  const n = Math.pow(2, zoom)
  const x = ((lng + 180) / 360) * n
  const y = (1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * n
  return { x, y }
}
