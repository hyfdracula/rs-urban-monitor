/**
 * Export template.
 * Generates Export.image.toDrive() or Export.image.toAsset() calls.
 */

export function buildExport(params) {
  const { exportFormat, exportPrefix, timePeriods, indicators } = params

  const images = []

  for (const year of timePeriods) {
    if (indicators.includes('rsei')) images.push({ name: `rsei_${year}`, varName: `rsei_${year}` })
    if (indicators.includes('construction')) images.push({ name: `construction_${year}`, varName: `construction_${year}` })
    if (indicators.includes('nightLight')) images.push({ name: `ntl_${year}`, varName: `ntl_${year}` })
    if (indicators.includes('population')) images.push({ name: `population_${year}`, varName: `population_${year}` })
    if (indicators.includes('gdp')) images.push({ name: `gdp_${year}`, varName: `gdp_${year}` })
  }

  // Expansion mode is pairwise
  if (indicators.includes('expansion')) {
    const sorted = [...timePeriods].sort((a, b) => a - b)
    for (let i = 0; i < sorted.length - 1; i++) {
      images.push({
        name: `expansion_mode_${sorted[i]}_${sorted[i + 1]}`,
        varName: `expansion_mode_${sorted[i]}_${sorted[i + 1]}`,
      })
    }
  }

  let code = `// ========== 导出结果 ==========\n`

  if (exportFormat === 'drive') {
    code += `// 导出到 Google Drive\n`
    for (const img of images) {
      code += `
Export.image.toDrive({
  image: ${img.varName},
  description: '${exportPrefix}_${img.name}',
  folder: 'GEE_exports',
  region: boundary,
  scale: 30,
  maxPixels: 1e13,
  crs: 'EPSG:4326',
});\n`
    }
  } else {
    code += `// 导出到 Earth Engine Asset
// 请替换 YOUR_USERNAME 为你的 GEE 用户名\n`
    for (const img of images) {
      code += `
Export.image.toAsset({
  image: ${img.varName},
  description: '${exportPrefix}_${img.name}',
  assetId: 'users/YOUR_USERNAME/${exportPrefix}_${img.name}',
  region: boundary,
  scale: 30,
  maxPixels: 1e13,
  crs: 'EPSG:4326',
});\n`
    }
  }

  return code
}
