export function normalizeCustomLayers(layers) {
  return Array.isArray(layers) ? layers : []
}

export function nextCustomLayerLoadState(layers, hasMap) {
  const normalized = normalizeCustomLayers(layers)
  return {
    mapLayers: normalized,
    pendingLayers: hasMap ? [] : normalized,
    shouldRegister: hasMap && normalized.length > 0,
  }
}
