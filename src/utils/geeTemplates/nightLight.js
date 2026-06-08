/**
 * Nighttime light template.
 * DMSP-OLS (2000-2013) + VIIRS NTL (2014+).
 */

export function nightLightTemplate(params) {
  const { timePeriods } = params

  let code = `
// ========== 夜间灯光数据提取 ==========
// DMSP-OLS (2000-2013) + VIIRS NTL (2014+)

function extractNTL(year, boundary) {
  var ntl;

  if (year <= 2013) {
    // DMSP-OLS 年度合成
    ntl = ee.ImageCollection('NOAA/DMSP-OLS/NIGHTTIME_LIGHTS')
      .filterMetadata('year', 'equals', year)
      .first()
      .select('stable_lights')
      .clip(boundary);
  } else {
    // VIIRS NTL 年度合成
    var viirs = ee.ImageCollection('NOAA/VIIRS/DNB/ANNUAL_V22')
      .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 12, 31))
      .first()
      .select('average')
      .clip(boundary);
    ntl = viirs;
  }

  return ntl.rename('NTL');
}
`

  const yearCalls = timePeriods.map(year =>
    `var ntl_${year} = extractNTL(${year}, boundary);`
  ).join('\n')

  code += `\n// 生成夜间灯光影像\n${yearCalls}\n`

  return code
}
