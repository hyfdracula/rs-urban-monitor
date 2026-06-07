<template>
  <div class="legend-wrapper">
    <div class="legend-bar">
      <h3 class="legend-title">图例</h3>
      <div v-for="item in legendItems" :key="item.id" class="legend-group">
        <div class="legend-row main">
          <span class="legend-swatch" :style="{ background: item.color }" />
          <span class="legend-label">{{ item.name }}</span>
        </div>
        <div v-if="item.children" class="legend-children">
          <div v-for="child in item.children" :key="child.key" class="legend-row sub">
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
import { activeLayerGroups } from '../../stores/layerState'
import { LAYER_CONFIG, RSEI_GRADES, ECO_CHANGE_CLASSES } from '../../config/map'

// Build legend items directly from LAYER_CONFIG — ensures ID match
// Generate 5 shade colors from a base hex color
function shadeColors(hex, count = 5) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return Array.from({ length: count }, (_, i) => {
    const t = 0.3 + (i / (count - 1)) * 0.7
    const rr = Math.round(r * t)
    const gg = Math.round(g * t)
    const bb = Math.round(b * t)
    return `#${rr.toString(16).padStart(2, '0')}${gg.toString(16).padStart(2, '0')}${bb.toString(16).padStart(2, '0')}`
  })
}

const allItems = Object.values(LAYER_CONFIG).map(g => {
  let children = null
  if (g.id === 'expansion-mode' && g.modes) {
    children = g.modes.map(m => ({ key: m.key, name: m.name, color: m.color }))
  } else if (g.id === 'rsei') {
    children = RSEI_GRADES.map(r => ({ key: r.key, name: `${r.name} (${r.range[0]}–${r.range[1]})`, color: r.color }))
  } else if (g.id === 'rsei-change') {
    children = ECO_CHANGE_CLASSES.map(c => ({ key: c.key, name: c.name, color: c.color }))
  } else if (g.layers && g.layers.length) {
    // Year-based layers — each year a different shade
    const shades = shadeColors(g.color, g.layers.length)
    children = g.layers.map((l, i) => ({ key: String(l.year), name: String(l.year), color: shades[i] }))
  }
  return { id: g.id, name: g.name, color: g.color, children }
})

const legendItems = computed(() => {
  if (!activeLayerGroups.length) return []
  return allItems.filter(item => activeLayerGroups.includes(item.id))
})
</script>

<style scoped>
.legend-wrapper {
  background: rgba(26,26,26,0.88);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  border: 1px solid #333;
  max-height: 260px;
  overflow-y: auto;
}

.legend-bar { padding: 10px 12px; }
.legend-title { font-size: 13px; font-weight: 600; color: #ddd; margin: 0 0 10px 0; }
.legend-group { margin-bottom: 6px; }
.legend-row { display: flex; align-items: center; gap: 8px; padding: 2px 0; }
.legend-row.main { padding: 3px 0; }
.legend-row.sub { padding-left: 12px; }
.legend-swatch { width: 16px; height: 16px; border-radius: 3px; flex-shrink: 0; }
.legend-swatch.small { width: 12px; height: 12px; border-radius: 2px; }
.legend-label { font-size: 12px; color: #bbb; line-height: 1.3; }
.legend-row.main .legend-label { font-weight: 600; color: #ddd; font-size: 13px; }
.legend-row.sub .legend-label { font-size: 11px; color: #999; }
.legend-children { margin-top: 2px; }
</style>
