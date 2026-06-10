<template>
  <div class="legend-wrapper" v-if="visibleLegends.length">
    <div class="legend-bar">
      <h3 class="legend-title">图例</h3>
      <div v-for="item in visibleLegends" :key="item.type" class="legend-group">
        <div class="legend-row main">
          <span class="legend-swatch" :style="{ background: item.accent }" />
          <span class="legend-label">{{ item.label }}</span>
        </div>
        <!-- Gradient bar for continuous layers -->
        <div v-if="item.gradient" class="legend-gradient-row">
          <div class="gradient-bar" :style="{ background: item.gradient }" />
          <div class="gradient-labels">
            <span v-for="lbl in item.labels" :key="lbl" class="grad-lbl">{{ lbl }}</span>
          </div>
        </div>
        <!-- Categorical items (e.g. RSEI class) -->
        <div v-if="item.children" class="legend-children">
          <div v-for="child in item.children" :key="child.name" class="legend-row sub">
            <span class="legend-swatch small" :style="{ background: child.color }" />
            <span class="legend-label">{{ child.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** report.map_layers */
  mapLayers: { type: Array, default: () => [] },
  /** Currently visible layer type strings */
  visibleTypes: { type: Array, default: () => [] },
})

// ── Color definitions matching backend sld_templates.py ──

const LEGEND_DEFS = {
  rsei: {
    accent: '#1A9641',
    gradient: 'linear-gradient(to right, #D7191C, #FDAE61, #FFFFBF, #A6D96A, #1A9641)',
    labels: ['差 0', '0.25', '0.5', '0.75', '优 1'],
  },
  rsei_class: {
    accent: '#A6D96A',
    children: [
      { name: '差 (<0.4)', color: '#D7191C' },
      { name: '中 (0.4-0.6)', color: '#FDAE61' },
      { name: '良 (0.6-0.8)', color: '#A6D96A' },
      { name: '优 (>0.8)', color: '#1A9641' },
    ],
  },
  built: { accent: '#FF6B6B' },
  new_built: { accent: '#FF0000' },
  ndvi: {
    accent: '#5EAA4A',
    gradient: 'linear-gradient(to right, #FFFFFF, #D7C5A0, #BEDE8B, #5EAA4A, #1E6B31, #004D18)',
    labels: ['-0.2', '0', '0.2', '0.4', '0.6', '0.8'],
  },
  lst: {
    accent: '#FEE661',
    gradient: 'linear-gradient(to right, #2B3990, #3F8EB0, #7EC87E, #FEE661, #E6371E)',
    labels: ['5°C', '15', '25', '35', '45'],
  },
  viirs: {
    accent: '#FFCC00',
    gradient: 'linear-gradient(to right, #000000, #332200, #664400, #CC8800, #FFCC00, #FFFFFF)',
    labels: ['0', '5', '15', '30', '50', '80'],
  },
  ntl: {
    accent: '#FFCC00',
    gradient: 'linear-gradient(to right, #000000, #332200, #664400, #CC8800, #FFCC00, #FFFFFF)',
    labels: ['0', '5', '15', '30', '50', '80'],
  },
  population: {
    accent: '#6A51A3',
    gradient: 'linear-gradient(to right, #F2F0F7, #DADAEB, #9E9AC8, #6A51A3, #3F007D)',
    labels: ['0', '10', '30', '60', '100'],
  },
  gdp: {
    accent: '#FC4E2A',
    gradient: 'linear-gradient(to right, #FFFFCC, #FFEDA0, #FEB24C, #FC4E2A, #E31A1C, #800026)',
    labels: ['0', '5k', '15k', '30k', '60k', '100k'],
  },
}

/** Match layer.type to a LEGEND_DEFS key (longer prefix first). */
const PREFIX_ORDER = [
  'rsei_class', 'rsei', 'new_built', 'built', 'ndvi',
  'lst', 'viirs', 'ntl', 'population', 'gdp',
]

function matchDef(layerType) {
  for (const prefix of PREFIX_ORDER) {
    if (layerType === prefix || layerType.startsWith(prefix + '_')) {
      return { key: prefix, def: LEGEND_DEFS[prefix] }
    }
  }
  return null
}

const visibleLegends = computed(() => {
  if (!props.visibleTypes.length || !props.mapLayers.length) return []
  const result = []
  for (const type of props.visibleTypes) {
    const layer = props.mapLayers.find(l => l.type === type)
    if (!layer) continue
    const matched = matchDef(type)
    if (matched) {
      result.push({
        type,
        label: layer.label,
        accent: matched.def.accent,
        gradient: matched.def.gradient || null,
        labels: matched.def.labels || null,
        children: matched.def.children || null,
      })
    } else {
      // Unknown type: show a simple color dot
      result.push({ type, label: layer.label, accent: '#888' })
    }
  }
  return result
})
</script>

<style scoped>
.legend-wrapper {
  position: absolute;
  bottom: 40px;
  left: 12px;
  z-index: 10;
  background: rgba(26,26,26,0.88);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  border: 1px solid #333;
  max-height: 400px;
  overflow-y: auto;
}

.legend-bar { padding: 10px 12px; }
.legend-title { font-size: 13px; font-weight: 600; color: #ddd; margin: 0 0 10px 0; }

.legend-group { margin-bottom: 8px; }
.legend-group:last-child { margin-bottom: 0; }

.legend-row { display: flex; align-items: center; gap: 8px; padding: 2px 0; }
.legend-row.main { padding: 3px 0; }
.legend-row.sub { padding-left: 12px; }

.legend-swatch { width: 16px; height: 16px; border-radius: 3px; flex-shrink: 0; }
.legend-swatch.small { width: 12px; height: 12px; border-radius: 2px; }
.legend-label { font-size: 12px; color: #bbb; line-height: 1.3; }
.legend-row.main .legend-label { font-weight: 600; color: #ddd; font-size: 13px; }
.legend-row.sub .legend-label { font-size: 11px; color: #999; }

.legend-children { margin-top: 2px; }

/* Gradient bar */
.legend-gradient-row { margin: 4px 0 2px 24px; }
.gradient-bar { height: 8px; border-radius: 4px; }
.gradient-labels { display: flex; justify-content: space-between; margin-top: 2px; }
.grad-lbl { font-size: 9px; color: #777; }
</style>
