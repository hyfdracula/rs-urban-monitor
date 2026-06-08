/**
 * Cloud masking functions for GEE.
 * Returns GEE JavaScript code strings for Landsat 5/7/8 and Sentinel-2.
 */

export function buildCloudMask(params) {
  return `
// ========== 云掩膜函数 ==========

function maskCloudsLandsat5(image) {
  var qa = image.select('QA_PIXEL');
  var cloudShadow = 1 << 3;
  var clouds = 1 << 5;
  var mask = qa.bitwiseAnd(cloudShadow).eq(0)
    .and(qa.bitwiseAnd(clouds).eq(0));
  return image.updateMask(mask);
}

function maskCloudsLandsat8(image) {
  var qa = image.select('QA_PIXEL');
  var cloudShadow = 1 << 4;
  var clouds = 1 << 3;
  var mask = qa.bitwiseAnd(cloudShadow).eq(0)
    .and(qa.bitwiseAnd(clouds).eq(0));
  return image.updateMask(mask);
}

function maskCloudsSentinel2(image) {
  var qa = image.select('QA60');
  var cloudBit = 1 << 10;
  var cirrusBit = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBit).eq(0)
    .and(qa.bitwiseAnd(cirrusBit).eq(0));
  return image.updateMask(mask)
    .divide(10000);
}
`.trim()
}
