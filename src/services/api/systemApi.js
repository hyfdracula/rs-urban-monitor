import api from './client.js'

export function getSystemStatus() {
  return api.get('/system/status').then(r => r.data)
}

export function getSystemQuota() {
  return api.get('/system/quota').then(r => r.data)
}
