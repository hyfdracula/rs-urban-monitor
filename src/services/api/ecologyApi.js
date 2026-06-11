import api from './client.js'

export function getEcology(params) {
  return api.get('/ecology', { params }).then(r => r.data)
}

export function getRSEI(params) {
  return api.get('/ecology/rsei', { params }).then(r => r.data)
}

export function getRSEIChange(params) {
  return api.get('/ecology/rsei-change', { params }).then(r => r.data)
}
