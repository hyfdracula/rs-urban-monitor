import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
})

// ========== 城市扩张 ==========
export function getExpansion(params) {
  return api.get('/expansion', { params }).then(r => r.data)
}
export function getExpansionModes(params) {
  return api.get('/expansion/modes', { params }).then(r => r.data)
}
export function getHotspots(params) {
  return api.get('/expansion/hotspots', { params }).then(r => r.data)
}

// ========== 生态环境 ==========
export function getEcology(params) {
  return api.get('/ecology', { params }).then(r => r.data)
}
export function getRSEI(params) {
  return api.get('/ecology/rsei', { params }).then(r => r.data)
}
export function getRSEIChange(params) {
  return api.get('/ecology/rsei-change', { params }).then(r => r.data)
}

// ========== 社会经济 ==========
export function getSocioEconomic(params) {
  return api.get('/socio', { params }).then(r => r.data)
}

// ========== 综合报告 ==========
export function getOverview(params) {
  return api.get('/overview', { params }).then(r => r.data)
}
export function getCityTable(params) {
  return api.get('/cities', { params }).then(r => r.data)
}

// ========== 文件上传 ==========
export function uploadGeoFile(formData, onProgress) {
  return api.post('/upload/geofile', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  }).then(r => r.data)
}

// ========== 任务状态 ==========
export function getTaskStatus(taskId) {
  return api.get(`/tasks/${taskId}`).then(r => r.data)
}

export default api
