import axios from 'axios'

import { getUserToken } from '../../utils/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  config.headers.Authorization = `Bearer ${getUserToken()}`
  return config
})

export default api
