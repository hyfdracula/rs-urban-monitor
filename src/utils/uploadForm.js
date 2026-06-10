export function createBoundaryUploadForm(file, name, years, computeMode, config) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('name', name)
  formData.append('years', JSON.stringify(years || [2020]))
  formData.append('compute_mode', computeMode || 'online')
  if (config) {
    formData.append('config', JSON.stringify(config))
  }
  return formData
}

export function createUploadRequestConfig(onProgress, timeout) {
  const requestConfig = {}
  if (onProgress) requestConfig.onUploadProgress = onProgress
  if (timeout) requestConfig.timeout = timeout
  return requestConfig
}
