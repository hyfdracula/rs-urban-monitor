<template>
  <div class="layer-control-wrapper">
    <div class="layer-control">
      <h3 class="panel-title">图层控制</h3>
      <div class="layer-groups">
        <div v-for="group in layerGroups" :key="group.id" class="layer-group">
          <div class="group-header" @click="toggleGroup(group.id)">
            <el-icon><component :is="group.icon" /></el-icon>
            <span class="group-name">{{ group.name }}</span>
            <el-icon class="expand-icon" :class="{ expanded: expandedGroups[group.id] }">
              <ArrowRight />
            </el-icon>
          </div>
          <div class="group-content" :class="{ expanded: expandedGroups[group.id] }">
            <div v-if="group.layers.length" class="year-layers">
              <div v-for="layer in group.layers" :key="layer.year" class="year-layer-item">
                <el-switch v-model="layer.visible" size="small" @change="(val) => toggleLayer(group.id, layer, val)" />
                <span class="year-label">{{ layer.year }}</span>
              </div>
            </div>
            <div v-if="group.modes" class="mode-layers">
              <div v-for="mode in group.modes" :key="mode.key" class="mode-item">
                <span class="mode-dot" :style="{ background: mode.color }" />
                <span class="mode-name">{{ mode.name }}</span>
                <el-switch v-model="modeVisible[group.id + '_' + mode.key]" size="small" @change="(val) => toggleModeLayer(group.id, mode, val)" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { setActiveYearLayers, setLayerActive } from '../../stores/layerState'
import { LAYER_CONFIG } from '../../config/map'
import { syncVisibleYearLayers } from '../../utils/timelineLayers'
import { OfficeBuilding, Expand, Share, Sunny, Switch, Position, MoonNight, User, TrendCharts, ArrowRight } from '@element-plus/icons-vue'

const emit = defineEmits(['layer-toggle', 'mode-toggle'])

const layerGroups = reactive(
  Object.values(LAYER_CONFIG).map(group => ({
    ...group,
    layers: group.layers.map(l => ({ ...l })),
  }))
)
const expandedGroups = reactive(
  Object.fromEntries(Object.keys(LAYER_CONFIG).map(id => [id, false]))
)
const modeVisible = reactive({})

function toggleGroup(groupId) { expandedGroups[groupId] = !expandedGroups[groupId] }
function updateActiveGroup(groupId) {
  const activeYears = layerGroups
    .find(g => g.id === groupId)
    ?.layers
    .filter(l => l.visible)
    .map(l => l.year) || []
  const hasYearLayer = activeYears.length > 0
  const hasModeLayer = Object.entries(modeVisible).some(([k, v]) => k.startsWith(groupId + '_') && v)
  setLayerActive(groupId, hasYearLayer || hasModeLayer)
  setActiveYearLayers(groupId, activeYears)
}

function toggleLayer(groupId, layer, visible) {
  emit('layer-toggle', { groupId, layerName: layer.layerName, year: layer.year, visible })
  updateActiveGroup(groupId)
}
function toggleModeLayer(groupId, mode, visible) {
  emit('mode-toggle', { groupId, modeKey: mode.key, visible })
  updateActiveGroup(groupId)
}

function syncGroupYear(groupId, year) {
  const group = layerGroups.find(g => g.id === groupId)
  const activeYears = syncVisibleYearLayers(group, year)
  setActiveYearLayers(groupId, activeYears)
}

defineExpose({ syncGroupYear })
</script>

<style scoped>
.layer-control-wrapper {
  background: rgba(26,26,26,0.92);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  border: 1px solid #333;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
}

.layer-control { padding: 10px; }
.panel-title { font-size: 13px; font-weight: 600; color: #ddd; margin: 0 0 10px 0; }
.layer-group { margin-bottom: 4px; border-radius: 6px; background: #252525; overflow: hidden; }
.group-header {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  cursor: pointer; transition: background 0.2s;
}
.group-header:hover { background: #2a2a2a; }
.group-name { flex: 1; font-size: 12px; color: #ccc; }
.expand-icon { color: #666; transition: transform 0.3s; }
.expand-icon.expanded { transform: rotate(90deg); }
.group-content {
  max-height: 0;
  overflow: hidden;
  padding: 0 10px;
  border-top: 1px solid transparent;
  transition: max-height 0.3s ease, padding 0.3s ease, border-color 0.3s ease;
}
.group-content.expanded {
  max-height: 300px;
  padding: 6px 10px 10px;
  border-top-color: #333;
}
.year-layer-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.year-label { font-size: 12px; color: #aaa; }
.mode-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.mode-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.mode-name { flex: 1; font-size: 12px; color: #aaa; }
</style>
