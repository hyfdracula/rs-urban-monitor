export const MAPBOX_DARK_STYLE = 'mapbox://styles/mapbox/dark-v11'

export const LOCAL_DARK_STYLE = {
  version: 8,
  name: 'Local Dark',
  glyphs: 'mapbox://fonts/mapbox/{fontstack}/{range}.pbf',
  sources: {},
  layers: [
    {
      id: 'background',
      type: 'background',
      paint: {
        'background-color': '#0d0f10',
      },
    },
  ],
}

export function getInitialMapStyle(mapboxToken, useHostedStyle = false) {
  return useHostedStyle && String(mapboxToken || '').trim() ? MAPBOX_DARK_STYLE : LOCAL_DARK_STYLE
}

export function installMapStyleFallback(map, onReady) {
  if (!map) return

  let ready = false
  let fallbackApplied = false

  const markReady = () => {
    if (ready) return
    ready = true
    onReady?.()
  }

  map.once('load', markReady)

  map.on('error', (event) => {
    if (ready || fallbackApplied) return
    const message = event?.error?.message || ''
    const status = event?.error?.status || event?.error?.statusCode
    const shouldFallback = !status || status === 401 || status === 403 || /mapbox|style|network|fetch/i.test(message)

    if (!shouldFallback || typeof map.setStyle !== 'function') return
    fallbackApplied = true
    map.setStyle(LOCAL_DARK_STYLE)
  })
}
