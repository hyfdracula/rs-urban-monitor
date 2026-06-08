/**
 * Construction land extraction template.
 * Uses impervious surface classification from Landsat.
 */

export function constructionTemplate(params) {
  const { timePeriods, satellite } = params

  let code = `
// ========== 建设用地提取 ==========
// 基于 MNDWI + NDVI + NDBI 阈值法提取不透水面

function extractConstructionLand(year, boundary) {
  var startDate, endDate, collection;

  if (year <= 2011) {
    collection = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat5);
  } else if (year <= 2013) {
    collection = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat5);
  } else {
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat8);
  }${satellite === 'sentinel2' ? `
  if (year >= 2015) {
    collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .map(maskCloudsSentinel2);
  }` : ''}

  var composite = collection.median().clip(boundary);

  var mndwi = composite.normalizedDifference(['SR_B3', 'SR_B6']);
  var ndvi = composite.normalizedDifference(['SR_B5', 'SR_B4']);
  var ndbi = composite.normalizedDifference(['SR_B6', 'SR_B5']);

  // 建设用地: MNDWI < 0, NDVI < 0.2, NDBI > 0
  var construction = mndwi.lt(0)
    .and(ndvi.lt(0.2))
    .and(ndbi.gt(0))
    .rename('construction');

  return construction.clip(boundary).selfMask();
}
`

  const yearCalls = timePeriods.map(year =>
    `var construction_${year} = extractConstructionLand(${year}, boundary);`
  ).join('\n')

  code += `\n// 生成建设用地影像\n${yearCalls}\n`

  return code
}
