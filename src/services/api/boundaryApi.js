import api from './client.js'

export function getBoundary(id) {
  return api.get(`/boundary/${id}`).then(r => r.data)
}

export function getBoundaryList() {
  return api.get('/boundary/list').then(r => r.data)
}

export function deleteBoundary(id) {
  return api.delete(`/boundary/${id}`).then(r => r.data)
}

export function renameBoundary(id, name) {
  return api.put(`/boundary/${id}/rename`, { name }).then(r => r.data)
}

export function recomputeBoundary(boundaryId, { years, computeMode, name, indicators }) {
  return api.post(`/boundary/${boundaryId}/recompute`, {
    years,
    compute_mode: computeMode,
    name: name || null,
    indicators: indicators || [],
  }).then(r => r.data)
}
