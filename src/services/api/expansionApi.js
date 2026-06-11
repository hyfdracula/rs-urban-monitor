import api from './client.js'

export function getExpansion(params) {
  return api.get('/expansion', { params }).then(r => r.data)
}

export function getExpansionModes(params) {
  return api.get('/expansion/modes', { params }).then(r => r.data)
}

export function getHotspots(params) {
  return api.get('/expansion/hotspots', { params }).then(r => r.data)
}
