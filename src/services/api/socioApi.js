import api from './client.js'

export function getSocioEconomic(params) {
  return api.get('/socio', { params }).then(r => r.data)
}
