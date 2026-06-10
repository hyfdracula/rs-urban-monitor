<template>
  <Teleport to="body">
    <Transition name="compare-fade">
      <div v-if="visible" class="compare-overlay">
        <!-- Header bar -->
        <div class="compare-header">
          <div class="header-left">
            <span class="header-icon">⇄</span>
            <span class="header-title">双期对比</span>
            <span class="header-range">{{ yearRange[0] }} ⟷ {{ yearRange[1] }}</span>
          </div>
          <button class="close-btn" @click="close">✕</button>
        </div>

        <!-- Main content: two maps -->
        <div class="compare-body">
          <!-- Map A -->
          <div class="split-panel">
            <div class="panel-badge badge-start">
              <span class="badge-dot" />
              <span>{{ yearRange[0] }} 年</span>
            </div>
            <div ref="mapAContainer" class="map-half" />
          </div>

          <!-- Center divider with drag hint -->
          <div class="center-divider">
            <div class="divider-line" />
            <div class="divider-grip">⇔</div>
            <div class="divider-line" />
          </div>

          <!-- Map B -->
          <div class="split-panel">
            <div class="panel-badge badge-end">
              <span class="badge-dot" />
              <span>{{ yearRange[1] }} 年</span>
            </div>
            <div ref="mapBContainer" class="map-half" />
          </div>
        </div>

        <!-- Bottom: range timeline -->
        <div class="compare-footer">
          <RangeTimeline v-model="yearRange" @change="onRangeChange" />
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, onUnmounted } from 'vue'
import mapboxgl from 'mapbox-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import { MAPBOX_TOKEN, MAP_CENTER, MAP_ZOOM, MAP_BOUNDS, LAYER_CONFIG, TIME_PERIODS } from '../../config/map'
import { buildWmsTileUrl } from '../../utils/geoserver'
import RangeTimeline from '../map/RangeTimeline.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  defaultRange: { type: Array, default: () => [TIME_PERIODS[0], TIME_PERIODS[TIME_PERIODS.length - 1]] },
  /** Separate localStorage key per page so home/custom don't overwrite each other */
  storageKey: { type: String, default: 'compare-range' },
})

const emit = defineEmits(['update:modelValue'])

const mapAContainer = ref(null)
const mapBContainer = ref(null)
let mapA = null
let mapB = null
let syncing = false

/** Read saved range from localStorage, or fall back to defaultRange */
function loadRange(fallback) {
  try {
    const raw = localStorage.getItem(props.storageKey)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed) && parsed.length === 2) return parsed
    }
  } catch { /* ignore */ }
  return [...fallback]
}

/** Persist current range to localStorage */
function saveRange(range) {
  try {
    localStorage.setItem(props.storageKey, JSON.stringify(range))
  } catch { /* ignore */ }
}

const yearRange = ref(loadRange(props.defaultRange))

const visible = ref(false)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    // Restore from memory or use default
    yearRange.value = loadRange(props.defaultRange)
    nextTick(() => initMaps())
    // ESC to close
    document.addEventListener('keydown', onEsc)
  } else {
    // Save current selection before closing
    saveRange(yearRange.value)
    destroyMaps()
    document.removeEventListener('keydown', onEsc)
  }
})

watch(visible, (val) => { emit('update:modelValue', val) })

function onEsc(e) {
  if (e.key === 'Escape') close()
}

function close() {
  visible.value = false
}

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
  m.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right')
  m.addControl(new mapboxgl.ScaleControl({ maxWidth: 80 }), 'bottom-left')
  return m
}

function addYearLayer(m, year) {
  if (!m) return
  const layerConfig = LAYER_CONFIG.constructionLand
  const layer = layerConfig.layers.find(l => l.year === year)
  if (!layer) return

  const layerId = `construction-${year}`
  const sourceId = `source-${layerId}`
  if (m.getSource(sourceId)) {
    // Already added, ensure visible
    if (m.getLayer(layerId)) m.setLayoutProperty(layerId, 'visibility', 'visible')
    return
  }

  const tileUrl = buildWmsTileUrl(layer.layerName)
  m.addSource(sourceId, { type: 'raster', tiles: [tileUrl], tileSize: 256 })
  m.addLayer({
    id: layerId,
    type: 'raster',
    source: sourceId,
    paint: { 'raster-opacity': 0.75 },
  })
}

function clearLayers(m) {
  if (!m) return
  const style = m.getStyle()
  if (!style) return
  for (const l of style.layers) {
    if (l.id.startsWith('construction-')) {
      m.removeLayer(l.id)
      const srcId = `source-${l.id}`
      if (m.getSource(srcId)) m.removeSource(srcId)
    }
  }
}

function syncMaps(source, target) {
  if (syncing || !source || !target) return
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

function initMaps() {
  if (!mapAContainer.value || !mapBContainer.value) return

  mapA = initMap(mapAContainer.value)
  mapB = initMap(mapBContainer.value)

  mapA.on('load', () => addYearLayer(mapA, yearRange.value[0]))
  mapB.on('load', () => addYearLayer(mapB, yearRange.value[1]))

  mapA.on('move', () => syncMaps(mapA, mapB))
  mapB.on('move', () => syncMaps(mapB, mapA))
}

function destroyMaps() {
  mapA?.remove()
  mapB?.remove()
  mapA = null
  mapB = null
}

onUnmounted(() => {
  destroyMaps()
  document.removeEventListener('keydown', onEsc)
})
</script>

<style scoped>
.compare-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  background: #0a0a0a;
}

/* ===== Header ===== */
.compare-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 20px;
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-icon {
  font-size: 18px;
  color: #FFD43B;
}

.header-title {
  font-size: 15px;
  font-weight: 700;
  color: #eee;
}

.header-range {
  font-size: 13px;
  color: #888;
  margin-left: 4px;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: #888;
  font-size: 18px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #333;
  color: #fff;
}

/* ===== Body: split maps ===== */
.compare-body {
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
  width: 3px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: #1a1a1a;
  flex-shrink: 0;
}

.divider-line {
  flex: 1;
  width: 1px;
  background: #444;
}

.divider-grip {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #252525;
  border: 1px solid #444;
  border-radius: 50%;
  color: #888;
  font-size: 12px;
}

/* Panel badges */
.panel-badge {
  position: absolute;
  top: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  color: #ccc;
  z-index: 5;
}

.badge-start {
  left: 12px;
  border: 1px solid rgba(255, 107, 107, 0.3);
}

.badge-end {
  right: 12px;
  border: 1px solid rgba(77, 171, 247, 0.3);
}

.badge-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.badge-start .badge-dot {
  background: #FF6B6B;
}

.badge-end .badge-dot {
  background: #4DABF7;
}

/* ===== Footer ===== */
.compare-footer {
  flex-shrink: 0;
  background: #1a1a1a;
  border-top: 1px solid #333;
}

/* ===== Transition ===== */
.compare-fade-enter-active {
  transition: opacity 0.25s ease;
}

.compare-fade-leave-active {
  transition: opacity 0.2s ease;
}

.compare-fade-enter-from,
.compare-fade-leave-to {
  opacity: 0;
}
</style>
