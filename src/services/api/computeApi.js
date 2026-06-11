import api from './client.js'

export function getTaskStatus(taskId) {
  return api.get(`/tasks/${taskId}`).then(r => r.data)
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

export function getComputeTasks() {
  return api.get('/compute/tasks').then(r => r.data)
}

export function getComputeProgress(taskId) {
  return api.get(`/compute/${taskId}/progress`).then(r => r.data)
}

export function cancelCompute(taskId) {
  return api.post(`/compute/${taskId}/cancel`).then(r => r.data)
}
