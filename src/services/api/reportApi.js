import api from './client.js'

export function getOverview(params) {
  return api.get('/overview', { params }).then(r => r.data)
}

export function getCityTable(params) {
  return api.get('/cities', { params }).then(r => r.data)
}

export function getReport(params) {
  return api.get('/report', { params }).then(r => r.data)
}

export function getAnalysis(taskId) {
  return api.get(`/analysis/${taskId}`).then(r => r.data)
}
