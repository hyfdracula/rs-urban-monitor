import { LAYER_CONFIG } from '../config/map.js'

export function getYearLayerId(groupId, year) {
  return `${groupId}-${year}`
}

export function getYearLayer(groupId, year, layerConfig = LAYER_CONFIG) {
  const group = Object.values(layerConfig).find(item => item.id === groupId)
  const layer = group?.layers?.find(item => item.year === year)

  if (!layer) return null

  return {
    groupId,
    year: layer.year,
    layerName: layer.layerName,
  }
}

export function buildYearLayerTransition({ groupId, fromYear, toYear, activeYears = [], layerConfig = LAYER_CONFIG }) {
  const nextLayer = getYearLayer(groupId, toYear, layerConfig)

  if (!nextLayer) {
    return {
      removeLayerIds: [],
      addLayer: null,
    }
  }

  const yearsToRemove = new Set(activeYears)
  if (fromYear != null) yearsToRemove.add(fromYear)
  yearsToRemove.delete(nextLayer.year)

  const removeLayerIds = [...yearsToRemove]
    .filter(year => getYearLayer(groupId, year, layerConfig))
    .map(year => getYearLayerId(groupId, year))

  return {
    removeLayerIds,
    addLayer: {
      id: getYearLayerId(groupId, nextLayer.year),
      layerName: nextLayer.layerName,
      year: nextLayer.year,
    },
  }
}

export function syncVisibleYearLayers(group, year) {
  if (!group?.layers?.length) return []

  for (const layer of group.layers) {
    layer.visible = layer.year === year
  }

  return group.layers
    .filter(layer => layer.visible)
    .map(layer => layer.year)
}
