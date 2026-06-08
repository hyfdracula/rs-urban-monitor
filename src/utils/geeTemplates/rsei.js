/**
 * RSEI (Remote Sensing Ecological Index) template.
 * Calculates NDVI, WET, NDBSI, LST → PCA → RSEI.
 */

export function rseiTemplate(params) {
  const { timePeriods, satellite } = params

  let code = `
// ========== RSEI 遥感生态指数计算 ==========
// NDVI(绿度) + WET(湿度) + NDBSI(干度) + LST(热度) → PCA → RSEI

function normalize(image) {
  var min = image.reduceRegion({
    reducer: ee.Reducer.min(),
    geometry: boundary,
    scale: 30,
    maxPixels: 1e13
  });
  var max = image.reduceRegion({
    reducer: ee.Reducer.max(),
    geometry: boundary,
    scale: 30,
    maxPixels: 1e13
  });
  return image.unitScale(min, max);
}

function calculateRSEI(year, boundary) {
  var startDate, endDate, collection;

  if (year <= 2011) {
    // Landsat 5
    startDate = ee.Date.fromYMD(year, 6, 1);
    endDate = ee.Date.fromYMD(year, 9, 30);
    collection = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(startDate, endDate)
      .map(maskCloudsLandsat5);
  } else if (year <= 2013) {
    // Landsat 7 (SLC-off, use with caution)
    startDate = ee.Date.fromYMD(year, 6, 1);
    endDate = ee.Date.fromYMD(year, 9, 30);
    collection = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(startDate, endDate)
      .map(maskCloudsLandsat5);
  } else {
    // Landsat 8
    startDate = ee.Date.fromYMD(year, 6, 1);
    endDate = ee.Date.fromYMD(year, 9, 30);
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(startDate, endDate)
      .map(maskCloudsLandsat8);
  }${satellite === 'sentinel2' ? `
  // Sentinel-2 override for 2015+
  if (year >= 2015) {
    collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .map(maskCloudsSentinel2);
  }` : ''}

  var composite = collection.median().clip(boundary);

  // NDVI - 绿度
  var ndvi = composite.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');

  // WET - 湿度 (Tasseled Cap Wetness)
  var wet = composite.expression(
    '0.1511*B2 + 0.1973*B3 + 0.3283*B4 + 0.3407*B5 + (-0.7117*B6) + (-0.4559*B7)', {
    'B2': composite.select('SR_B2'),
    'B3': composite.select('SR_B3'),
    'B4': composite.select('SR_B4'),
    'B5': composite.select('SR_B5'),
    'B6': composite.select('SR_B6'),
    'B7': composite.select('SR_B7'),
  }).rename('WET');

  // NDBSI - 干度 (IBI + SI)/2
  var mndwi = composite.normalizedDifference(['SR_B3', 'SR_B6']);
  var ndbi = composite.normalizedDifference(['SR_B6', 'SR_B5']);
  var si = composite.expression(
    '((B6 - B4) / (B6 + B4))', {
    'B4': composite.select('SR_B4'),
    'B6': composite.select('SR_B6'),
  });
  var ibi = ndbi.subtract(mndwi.add(si).divide(2));
  var ndbsi = ibi.rename('NDBSI');

  // LST - 热度 (simplified, use thermal band)
  var lst = composite.select('ST_B10')
    .multiply(0.00341802).add(149.0).subtract(273.15)
    .rename('LST');

  // Normalize each indicator
  var ndvi_norm = normalize(ndvi);
  var wet_norm = normalize(wet);
  var ndbsi_norm = normalize(ndbsi);
  var lst_norm = normalize(lst);

  // Stack and PCA
  var stack = ndvi_norm.addBands([wet_norm, ndbsi_norm, lst_norm]);
  var pca = ee.Image(stack.toArray()
    .reduceRegion({
      reducer: ee.Reducer.centeredCovariance(),
      geometry: boundary,
      scale: 30,
      maxPixels: 1e13
    }).get('array'));

  var eigenvectors = ee.Tensor.pca(ee.Dictionary(pca).get('array'));

  // Get first principal component (PC1)
  var rsei = stack.arrayDotProduct(eigenvectors.slice(1, 0, 1).arrayProject([0]).arrayFlatten([['pc1']]))
    .rename('RSEI');

  return normalize(rsei).clip(boundary);
}
`

  // Generate per-year calls
  const yearCalls = timePeriods.map(year =>
    `var rsei_${year} = calculateRSEI(${year}, boundary);`
  ).join('\n')

  code += `\n// 生成 RSEI 影像\n${yearCalls}\n`

  return code
}
