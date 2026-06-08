<template>
  <div
    ref="mapContainer"
    class="map-container"
  >
    <!-- Loading skeleton (full screen grid) -->
    <div v-if="loading" class="map-skeleton">
      <div class="skeleton-pulse" />
      <div class="skeleton-grid-full">
        <div v-for="r in 12" :key="r" class="sk-row">
          <div v-for="c in 8" :key="c" class="sk-cell" :style="{ animationDelay: ((r+c)*0.06) + 's' }" />
        </div>
      </div>
      <div class="skeleton-label">加载地图数据…</div>
    </div>

    <!-- Feature popup on click -->
    <FeaturePopup
      v-if="popupFeature"
      :feature="popupFeature"
      :style="popupStyle"
      @close="closePopup"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, inject } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { MAPBOX_TOKEN, MAP_CENTER, MAP_ZOOM, MAP_BOUNDS } from '../../config/map'
import { buildWmsTileUrl } from '../../utils/geoserver'
import { queryFeature } from '../../utils/featureInfo'
import FeaturePopup from './FeaturePopup.vue'

const props = defineProps({
  activeLayers: { type: Array, default: () => [] },
  selectedYear: { type: Number, default: 2020 },
  compareYear: { type: Number, default: null },
})

const emit = defineEmits(['map-loaded', 'feature-click', 'year-change'])

const mapContainer = ref(null)
const loading = ref(true)
let map = null

// ResizeObserver: map auto-resizes when container size changes (e.g. panel collapse)
let resizeObserver = null

// Popup state
const popupFeature = ref(null)
const popupPosition = ref({ x: 0, y: 0 })

const popupStyle = computed(() => ({
  left: popupPosition.value.x + 'px',
  top: popupPosition.value.y + 'px',
  transform: 'translate(-50%, -110%)',
  position: 'absolute',
  zIndex: 10,
}))

async function onMapClick(e) {
  emit('feature-click', { lngLat: e.lngLat, point: e.point })

  try {
    const result = await queryFeature(e.lngLat)
    if (result) {
      popupFeature.value = result
      popupPosition.value = { x: e.point.x, y: e.point.y }
    }
  } catch {
    // silent fail
  }
}

function closePopup() {
  popupFeature.value = null
}

onMounted(() => {
  mapboxgl.accessToken = MAPBOX_TOKEN

  map = new mapboxgl.Map({
    container: mapContainer.value,
    style: 'mapbox://styles/mapbox/dark-v11',
    center: MAP_CENTER,
    zoom: MAP_ZOOM,
    minZoom: 4,
    maxZoom: 18,
    attributionControl: false,
  })

  map.addControl(new mapboxgl.NavigationControl(), 'bottom-right')
  map.addControl(new mapboxgl.ScaleControl(), 'bottom-left')

  map.on('load', () => {
    loading.value = false
    emit('map-loaded', map)
  })

  map.on('click', onMapClick)

  // Watch container size changes and auto-resize map
  resizeObserver = new ResizeObserver(() => { map?.resize() })
  resizeObserver.observe(mapContainer.value)
})

onUnmounted(() => {
  resizeObserver?.disconnect()
  if (map) {
    map.remove()
    map = null
  }
})

function addWmsLayer(layerId, geoServerLayer, options = {}) {
  if (!map) return
  const sourceId = `source-${layerId}`
  const tileUrl = buildWmsTileUrl(geoServerLayer, { style: options.style })
  if (map.getSource(sourceId)) { map.removeLayer(layerId); map.removeSource(sourceId) }
  map.addSource(sourceId, { type: 'raster', tiles: [tileUrl], tileSize: 256 })
  map.addLayer({ id: layerId, type: 'raster', source: sourceId,
    paint: { 'raster-opacity': options.opacity ?? 0.7 } })
}

function removeLayer(layerId) {
  if (!map) return
  const sourceId = `source-${layerId}`
  if (map.getLayer(layerId)) map.removeLayer(layerId)
  if (map.getSource(sourceId)) map.removeSource(sourceId)
}

function setLayerVisibility(layerId, visible) {
  if (!map || !map.getLayer(layerId)) return
  map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none')
}

function setLayerOpacity(layerId, opacity) {
  if (!map || !map.getLayer(layerId)) return
  map.setPaintProperty(layerId, 'raster-opacity', opacity)
}

function flyTo(center, zoom) {
  if (!map) return
  map.flyTo({ center, zoom, duration: 1500 })
}

function fitBounds(bounds, options = {}) {
  if (!map) return
  map.fitBounds(bounds, { padding: 50, duration: 1500, ...options })
}

defineExpose({ map, addWmsLayer, removeLayer, setLayerVisibility, setLayerOpacity, flyTo, fitBounds })
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
  background: #0d0d0d;
}

/* Loading skeleton */
.map-skeleton {
  position: absolute;
  inset: 0;
  background: #0d0d0d;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 5;
  transition: opacity 0.4s ease;
}

.skeleton-pulse {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #333 0deg, #666 90deg, #333 180deg, #555 270deg, #333 360deg);
  animation: sk-spin 1.5s linear infinite;
  opacity: 0.3;
  mask: radial-gradient(transparent 55%, black 60%);
  -webkit-mask: radial-gradient(transparent 55%, black 60%);
}

@keyframes sk-spin {
  to { transform: translate(-50%, -50%) rotate(360deg); }
}

.skeleton-grid-full {
  position: absolute;
  inset: 0;
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-template-rows: repeat(12, 1fr);
  gap: 6px;
  padding: 12px;
}

.sk-row {
  display: contents;
}

.sk-cell {
  aspect-ratio: 1;
  background: #1a1a1a;
  border-radius: 4px;
  border: 1px solid #252525;
  animation: sk-flicker 1.2s ease infinite;
}

@keyframes sk-flicker {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 0.7; }
}

.skeleton-label {
  margin-top: 18px;
  font-size: 13px;
  color: #555;
  letter-spacing: 1px;
}
</style>
