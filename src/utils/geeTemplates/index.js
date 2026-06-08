/**
 * GEE Code Generator — Main Entry
 *
 * Takes form data from the ManualModeWizard and generates
 * complete Google Earth Engine JavaScript code.
 *
 * No cloud LLM needed — pure template string interpolation.
 */

import { buildCloudMask } from './cloudMask'
import { rseiTemplate } from './rsei'
import { constructionTemplate } from './constructionLand'
import { expansionTemplate } from './expansionMode'
import { nightLightTemplate } from './nightLight'
import { populationTemplate } from './population'
import { gdpTemplate } from './gdp'
import { buildExport } from './export'

const templates = {
  rsei: rseiTemplate,
  construction: constructionTemplate,
  expansion: expansionTemplate,
  nightLight: nightLightTemplate,
  population: populationTemplate,
  gdp: gdpTemplate,
}

function buildHeader(params) {
  const indicators = params.indicators.map(i => {
    const names = {
      rsei: 'RSEI 遥感生态指数',
      construction: '建设用地提取',
      expansion: '扩张模式分类',
      nightLight: '夜间灯光',
      population: '人口密度',
      gdp: 'GDP 分布',
    }
    return names[i] || i
  })

  return `// ================================================================
// Google Earth Engine 自动生成代码
// 由 RS Urban Monitor 手动模式生成
// ================================================================
//
// 研究区: ${params.boundaryName || '自定义区域'}
// 时间: ${params.timePeriods.join(', ')}
// 分析指标: ${indicators.join(', ')}
// 数据源: ${params.satellite === 'sentinel2' ? 'Sentinel-2 (2015+)' : 'Landsat 自动选择'}
// 导出: ${params.exportFormat === 'drive' ? 'Google Drive' : 'Earth Engine Asset'}
//
// 使用方法:
// 1. 打开 https://code.earthengine.google.com/
// 2. 复制粘贴本代码
// 3. 点击 Run 运行
// 4. 在 Tasks 面板点击 Run 导出结果
// ================================================================

`
}

function buildBoundary(params) {
  const geoJSON = params.boundaryGeoJSON
  if (!geoJSON) return '// WARNING: 未提供研究区边界\n'

  let geometryStr
  if (geoJSON.type === 'FeatureCollection') {
    geometryStr = JSON.stringify(geoJSON.features[0].geometry)
  } else if (geoJSON.type === 'Feature') {
    geometryStr = JSON.stringify(geoJSON.geometry)
  } else {
    geometryStr = JSON.stringify(geoJSON)
  }

  // Simplify coordinates to 5 decimal places (~1m precision)
  geometryStr = geometryStr.replace(/(\d+\.\d{5})\d+/g, '$1')

  return `// ========== 研究区边界 ==========
var boundary = ee.Geometry(${geometryStr});
var roi = boundary;

Map.centerObject(boundary, 9);
Map.addLayer(boundary, {color: 'white'}, '研究区边界', false);

`
}

/**
 * Generate complete GEE JavaScript code from form data.
 * @param {Object} formData - From ManualModeWizard
 * @returns {string} Complete GEE JavaScript code
 */
export function generateGEECode(formData) {
  const sections = []

  // 1. Header
  sections.push(buildHeader(formData))

  // 2. Boundary
  sections.push(buildBoundary(formData))

  // 3. Cloud mask functions
  sections.push(buildCloudMask(formData))

  // 4. Indicator templates
  for (const indicator of formData.indicators) {
    if (templates[indicator]) {
      sections.push(templates[indicator](formData))
    }
  }

  // 5. Export
  sections.push(buildExport(formData))

  return sections.join('\n')
}
