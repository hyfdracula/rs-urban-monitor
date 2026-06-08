/**
 * GDP spatial distribution template.
 */

export function gdpTemplate(params) {
  const { timePeriods } = params

  let code = `
// ========== GDP 分布数据提取 ==========
// 使用 GHSL - Global Human Settlement Layer GDP proxy
// 或使用 Kummu et al. GDP 栅格数据

function extractGDP(year, boundary) {
  // 使用 LandScan 或 GHSL 作为 GDP 空间化代理
  // 这里用夜间灯光作为 GDP 代理 (NTL 与 GDP 高度相关)
  var ntl;

  if (year <= 2013) {
    ntl = ee.ImageCollection('NOAA/DMSP-OLS/NIGHTTIME_LIGHTS')
      .filterMetadata('year', 'equals', year)
      .first()
      .select('stable_lights');
  } else {
    ntl = ee.ImageCollection('NOAA/VIIRS/DNB/ANNUAL_V22')
      .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 12, 31))
      .first()
      .select('average');
  }

  // 标准化到 GDP 指数 (0-1)
  var min = ntl.reduceRegion({
    reducer: ee.Reducer.min(),
    geometry: boundary,
    scale: 500,
    maxPixels: 1e13
  });
  var max = ntl.reduceRegion({
    reducer: ee.Reducer.max(),
    geometry: boundary,
    scale: 500,
    maxPixels: 1e13
  });

  var gdp = ntl.unitScale(min, max).rename('GDP_index').clip(boundary);
  return gdp;
}
`

  const yearCalls = timePeriods.map(year =>
    `var gdp_${year} = extractGDP(${year}, boundary);`
  ).join('\n')

  code += `\n// 生成 GDP 代理影像\n${yearCalls}\n`

  return code
}
