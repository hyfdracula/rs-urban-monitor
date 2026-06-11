import api from './client.js'
import { createBoundaryUploadForm, createUploadRequestConfig } from '../../utils/uploadForm'

export function uploadGeoFile(formData, onProgress) {
  return api.post('/upload/geofile', formData, createUploadRequestConfig(onProgress)).then(r => r.data)
}

export function uploadBoundary(file, name, years, computeMode, onProgress, config) {
  const formData = createBoundaryUploadForm(file, name, years, computeMode, config)
  return api.post(
    '/upload/boundary',
    formData,
    createUploadRequestConfig(onProgress, 120000),
  ).then(r => r.data)
}
