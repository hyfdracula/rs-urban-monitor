/**
 * 统一数据服务 — API first, mock fallback
 * 环境变量 VITE_USE_API=true 启用真实 API
 * FastAPI 未就绪时自动降级到 mock
 */
import * as api from '../api'
import * as mock from '../data/mockAnalysis'
import * as mockSE from '../data/mockSocioEconomic'

const useApi = import.meta.env.VITE_USE_API === 'true'

// Helper: try API → fallback mock
async function apiFirst(apiFn, mockFn, ...args) {
  if (!useApi) return mockFn(...args)
  try {
    const data = await apiFn(...args)
    if (data && Object.keys(data).length > 0) return data
  } catch (e) {
    console.warn('API unavailable, using mock:', e.message)
  }
  return mockFn(...args)
}

// ========== 扩张分析 ==========
export async function fetchExpansionData() {
  return apiFirst(api.getExpansion, mock.getExpansionData)
}

// ========== 生态评估 ==========
export async function fetchEcologyData() {
  return apiFirst(api.getEcology, mock.getEcologyData)
}

// ========== 社会经济 ==========
export async function fetchSocioEconomicData() {
  return apiFirst(api.getSocioEconomic, mockSE.getSocioEconomicData)
}

// ========== 热点 ==========
export async function fetchHotspotData() {
  return apiFirst(api.getHotspots, mock.getHotspotData)
}

// ========== 雷达图数据 ==========
export async function fetchRadarData() {
  return apiFirst(() => api.getEcology({ type: 'radar' }), mock.getRadarData)
}

// ========== 乡镇排名 ==========
export async function fetchTownshipRanking() {
  return apiFirst(() => api.getEcology({ type: 'ranking' }), mock.getTownshipRanking)
}

// ========== 总览仪表盘 ==========
export async function fetchOverviewData() {
  return apiFirst(api.getOverview, mock.getOverviewData)
}

// ========== 城市数据表 ==========
export async function fetchCityTableData(params) {
  return apiFirst(() => api.getCityTable(params), mock.getCityTableData)
}

// ========== 报告 ==========
export async function fetchReportData() {
  return apiFirst(api.getReport, mock.getReportData)
}

// ========== 文件上传 ==========
export async function uploadFile(formData, onProgress) {
  return api.uploadGeoFile(formData, onProgress)
}

// ========== 任务状态 ==========
export async function fetchTaskStatus(taskId) {
  return api.getTaskStatus(taskId)
}
