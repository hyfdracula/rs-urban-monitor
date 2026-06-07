import { reactive } from 'vue'

// Shared reactive state: which layer group IDs are currently visible
export const activeLayerGroups = reactive([])
export const activeYearLayerGroups = reactive([])
export const activeYearLayers = reactive({})

export function setLayerActive(groupId, active) {
  const idx = activeLayerGroups.indexOf(groupId)
  if (active && idx < 0) activeLayerGroups.push(groupId)
  if (!active && idx >= 0) activeLayerGroups.splice(idx, 1)
}

export function setActiveYearLayers(groupId, years) {
  const uniqueYears = [...new Set(years)]
  activeYearLayers[groupId] = uniqueYears

  const idx = activeYearLayerGroups.indexOf(groupId)
  if (uniqueYears.length > 0 && idx < 0) activeYearLayerGroups.push(groupId)
  if (uniqueYears.length === 0 && idx >= 0) activeYearLayerGroups.splice(idx, 1)
}
