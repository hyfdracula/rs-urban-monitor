<template>
  <div class="layer-control-wrapper">
    <div class="layer-control">
      <h3 class="panel-title">图层控制</h3>
      <div v-if="!groupedLayers.length" class="empty-hint">请先选择研究区</div>
      <div class="layer-groups">
        <div v-for="group in groupedLayers" :key="group.name" class="layer-group">
          <div class="group-header" @click="toggleGroup(group.name)">
            <span class="group-name">{{ group.name }}</span>
            <span class="group-count">{{ group.layers.length }}</span>
            <el-icon class="expand-icon" :class="{ expanded: expandedGroups[group.name] }">
              <ArrowRight />
            </el-icon>
          </div>
          <div class="group-content" :class="{ expanded: expandedGroups[group.name] }">
            <div v-for="layer in group.layers" :key="layer.type" class="layer-item">
              <el-switch
                :model-value="visibleTypes.includes(layer.type)"
                size="small"
                @change="(val) => onToggle(layer.type, val)"
              />
              <span class="layer-label">{{ layer.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { ArrowRight } from '@element-plus/icons-vue'

const props = defineProps({
  /** report.map_layers — [{type, label, group, wms_url, visible}, …] */
  mapLayers: { type: Array, default: () => [] },
  /** Currently visible layer types */
  visibleTypes: { type: Array, default: () => [] },
})

const emit = defineEmits(['layer-toggle'])

// Group layers by their `group` field
const groupedLayers = computed(() => {
  if (!props.mapLayers?.length) return []
  const map = new Map()
  for (const layer of props.mapLayers) {
    const g = layer.group || '其他'
    if (!map.has(g)) map.set(g, [])
    map.get(g).push(layer)
  }
  return Array.from(map.entries()).map(([name, layers]) => ({ name, layers }))
})

// Track which groups are expanded
const expandedGroups = reactive({})

// Auto-expand groups when layers change
watch(groupedLayers, (groups) => {
  const validNames = new Set(groups.map(g => g.name))
  for (const key of Object.keys(expandedGroups)) {
    if (!validNames.has(key)) delete expandedGroups[key]
  }
  for (const g of groups) {
    if (!(g.name in expandedGroups)) {
      expandedGroups[g.name] = true
    }
  }
}, { immediate: true })

function toggleGroup(name) {
  expandedGroups[name] = !expandedGroups[name]
}

function onToggle(type, visible) {
  emit('layer-toggle', { type, visible })
}
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
.empty-hint { font-size: 12px; color: #666; padding: 8px 0; }

.layer-group { margin-bottom: 4px; border-radius: 6px; background: #252525; overflow: hidden; }
.group-header {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  cursor: pointer; transition: background 0.2s;
}
.group-header:hover { background: #2a2a2a; }
.group-name { flex: 1; font-size: 12px; color: #ccc; }
.group-count {
  font-size: 10px; color: #888; background: #333;
  padding: 1px 6px; border-radius: 8px; min-width: 18px; text-align: center;
}
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
  max-height: 400px;
  padding: 6px 10px 10px;
  border-top-color: #333;
  overflow-y: auto;
}

.layer-item { display: flex; align-items: center; gap: 8px; padding: 4px 0; }
.layer-label { font-size: 12px; color: #aaa; }
</style>
