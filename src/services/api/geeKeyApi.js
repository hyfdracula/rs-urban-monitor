import api from './client.js'

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
