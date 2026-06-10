import axios from 'axios'
import { getUserToken } from '../utils/auth'
import { createBoundaryUploadForm, createUploadRequestConfig } from '../utils/uploadForm'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
})

// 自动带用户 token，后端 GEE 接口需要这个来区分用户
api.interceptors.request.use((config) => {
  config.headers.Authorization = `Bearer ${getUserToken()}`
  return config
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
  return api.post('/upload/geofile', formData, createUploadRequestConfig(onProgress)).then(r => r.data)
}

// ========== 任务状态 ==========
export function getTaskStatus(taskId) {
  return api.get(`/tasks/${taskId}`).then(r => r.data)
}

// ========== GEE 密钥管理 ==========
export function saveGeeKey(serviceAccount, keyJson) {
  return api.post('/gee-key/save', {
    service_account: serviceAccount,
    key_json: typeof keyJson === 'string' ? keyJson : JSON.stringify(keyJson),
  }).then(r => r.data)
}

export function verifyGeeKey() {
  return api.post('/gee-key/verify').then(r => r.data)
}

export function getGeeKeyStatus() {
  return api.get('/gee-key/status').then(r => r.data)
}

export function deleteGeeKey() {
  return api.delete('/gee-key').then(r => r.data)
}

// ========== 系统状态 ==========
export function getSystemStatus() {
  return api.get('/system/status').then(r => r.data)
}

export function getSystemQuota() {
  return api.get('/system/quota').then(r => r.data)
}

// ========== 上传边界 & 计算 ==========
export function uploadBoundary(file, name, years, computeMode, onProgress, config) {
  const formData = createBoundaryUploadForm(file, name, years, computeMode, config)
  return api.post(
    '/upload/boundary',
    formData,
    createUploadRequestConfig(onProgress, 120000),
  ).then(r => r.data)
}

export function getComputeStatus(taskId) {
  return api.get(`/compute/${taskId}/status`).then(r => r.data)
}

export function getComputeReport(taskId) {
  return api.get(`/compute/${taskId}/report`).then(r => r.data)
}

export function getComputeCode(taskId) {
  return api.get(`/compute/${taskId}/code`).then(r => r.data)
}

// ========== 边界查询 ==========
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

// ========== 重新计算（复用已有边界） ==========
export function recomputeBoundary(boundaryId, { years, computeMode, name, indicators }) {
  return api.post(`/boundary/${boundaryId}/recompute`, {
    years,
    compute_mode: computeMode,
    name: name || null,
    indicators: indicators || [],
  }).then(r => r.data)
}

// ========== 计算任务列表 ==========
export function getComputeTasks() {
  return api.get('/compute/tasks').then(r => r.data)
}

// ========== 分析聚合接口 ==========
export function getAnalysis(taskId) {
  return api.get(`/analysis/${taskId}`).then(r => r.data)
}

// ========== 计算进度 ==========
export function getComputeProgress(taskId) {
  return api.get(`/compute/${taskId}/progress`).then(r => r.data)
}

export function cancelCompute(taskId) {
  return api.post(`/compute/${taskId}/cancel`).then(r => r.data)
}

export default api
