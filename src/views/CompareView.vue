<template>
  <div class="compare-view">
    <!-- Top row: two maps -->
    <div class="maps-row">
      <!-- Map A (Start year) -->
      <div class="split-panel">
        <div class="panel-label left">前一期</div>
        <div ref="mapAContainer" class="map-half" />
      </div>

      <!-- Divider -->
      <div class="center-divider" />

      <!-- Map B (End year) -->
      <div class="split-panel">
        <div class="panel-label right">后一期</div>
        <div ref="mapBContainer" class="map-half" />
      </div>
    </div>

    <!-- Bottom: range timeline -->
    <RangeTimeline
      v-model="yearRange"
      @change="onRangeChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { MAPBOX_TOKEN, MAP_CENTER, MAP_ZOOM, MAP_BOUNDS, LAYER_CONFIG } from '../config/map'
import { buildWmsTileUrl } from '../utils/geoserver'
import RangeTimeline from '../components/map/RangeTimeline.vue'

const mapAContainer = ref(null)
const mapBContainer = ref(null)
let mapA = null
let mapB = null
let syncing = false

const yearRange = ref([2000, 2020])

function initMap(container) {
  mapboxgl.accessToken = MAPBOX_TOKEN
  const m = new mapboxgl.Map({
    container,
    style: 'mapbox://styles/mapbox/dark-v11',
    center: MAP_CENTER,
    zoom: MAP_ZOOM,
    maxBounds: MAP_BOUNDS,
    attributionControl: false,
  })
  m.addControl(new mapboxgl.NavigationControl(), 'bottom-right')
  m.addControl(new mapboxgl.ScaleControl(), 'bottom-left')
  return m
}

function addYearLayer(m, year) {
  if (!m) return
  const layerConfig = LAYER_CONFIG.constructionLand
  const layer = layerConfig.layers.find(l => l.year === year)
  if (!layer) return

  const layerId = `construction-${year}`
  const sourceId = `source-${layerId}`
  if (m.getSource(sourceId)) return

  const tileUrl = buildWmsTileUrl(layer.layerName)
  m.addSource(sourceId, { type: 'raster', tiles: [tileUrl], tileSize: 256 })
  m.addLayer({
    id: layerId,
    type: 'raster',
    source: sourceId,
    paint: { 'raster-opacity': 0.7 },
  })
}

function clearLayers(m) {
  if (!m) return
  const layers = m.getStyle()?.layers || []
  for (const l of layers) {
    if (l.id.startsWith('construction-')) {
      m.removeLayer(l.id)
      const srcId = `source-${l.id}`
      if (m.getSource(srcId)) m.removeSource(srcId)
    }
  }
}

function syncMaps(source, target) {
  if (syncing) return
  syncing = true
  target.jumpTo({
    center: source.getCenter(),
    zoom: source.getZoom(),
    bearing: source.getBearing(),
    pitch: source.getPitch(),
  })
  syncing = false
}

function onRangeChange({ start, end }) {
  clearLayers(mapA)
  clearLayers(mapB)
  addYearLayer(mapA, start)
  addYearLayer(mapB, end)
}

onMounted(async () => {
  await nextTick()
  if (!mapAContainer.value || !mapBContainer.value) return

  mapA = initMap(mapAContainer.value)
  mapB = initMap(mapBContainer.value)

  mapA.on('load', () => addYearLayer(mapA, yearRange.value[0]))
  mapB.on('load', () => addYearLayer(mapB, yearRange.value[1]))

  mapA.on('move', () => syncMaps(mapA, mapB))
  mapB.on('move', () => syncMaps(mapB, mapA))
})

onUnmounted(() => {
  mapA?.remove()
  mapB?.remove()
})
</script>

<style scoped>
.compare-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.maps-row {
  flex: 1;
  display: flex;
  min-height: 0;
}

.split-panel {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.map-half {
  width: 100%;
  height: 100%;
}

.center-divider {
  width: 2px;
  background: #444;
  flex-shrink: 0;
}

.panel-label {
  position: absolute;
  top: 12px;
  padding: 5px 12px;
  background: rgba(0, 0, 0, 0.75);
  color: #bbb;
  font-size: 12px;
  font-weight: 600;
  border-radius: 6px;
  z-index: 5;
}

.panel-label.left { left: 12px; }
.panel-label.right { right: 12px; }
</style>
