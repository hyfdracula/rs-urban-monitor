"""
GEE 代码生成服务
==============
将前端 geeTemplates/ 的 JavaScript 模板移植为 Python f-string 模板。
手动模式上传时调用 generate_gee_code() 生成完整 GEE JavaScript 代码。
"""

from __future__ import annotations

import json
import re
from typing import Any


# ─── 指标名称映射 ───

_INDICATOR_NAMES: dict[str, str] = {
    "rsei": "RSEI 遥感生态指数",
    "construction": "建设用地提取",
    "expansion": "扩张模式分类",
    "nightLight": "夜间灯光",
    "population": "人口密度",
    "gdp": "GDP 分布",
}


# ─── 主入口 ───


def generate_gee_code(
    geojson: dict[str, Any],
    boundary_name: str,
    years: list[int],
    indicators: list[str],
    satellite: str = "landsat-auto",
    export_format: str = "drive",
    export_prefix: str = "rs_urban",
) -> str:
    """根据配置生成完整的 GEE JavaScript 代码。"""
    # 扩张模式依赖建设用地：若选了 expansion 但没选 construction，自动补上
    effective_indicators = list(indicators)
    if "expansion" in effective_indicators and "construction" not in effective_indicators:
        effective_indicators.insert(
            effective_indicators.index("expansion"), "construction"
        )

    params = {
        "boundary_name": boundary_name or "自定义区域",
        "years": years,
        "indicators": effective_indicators,
        "satellite": satellite,
        "export_format": export_format,
        "export_prefix": export_prefix,
    }

    sections: list[str] = []
    sections.append(_build_header(params))
    sections.append(_build_boundary(geojson))
    sections.append(_build_cloud_mask(params))

    for ind in effective_indicators:
        template_fn = _TEMPLATES.get(ind)
        if template_fn:
            sections.append(template_fn(params))

    sections.append(_build_export(params))
    return "\n".join(sections)


# ─── 各模板函数 ───


def _build_header(params: dict) -> str:
    indicator_names = ", ".join(
        _INDICATOR_NAMES.get(i, i) for i in params["indicators"]
    )
    years_str = ", ".join(str(y) for y in params["years"])
    satellite_label = (
        "Sentinel-2 (2015+)"
        if params["satellite"] == "sentinel2"
        else "Landsat 自动选择"
    )
    export_label = (
        "Google Drive"
        if params["export_format"] == "drive"
        else "Earth Engine Asset"
    )

    return f"""// ================================================================
// Google Earth Engine 自动生成代码
// 由 RS Urban Monitor 手动模式生成
// ================================================================
//
// 研究区: {params['boundary_name']}
// 时间: {years_str}
// 分析指标: {indicator_names}
// 数据源: {satellite_label}
// 导出: {export_label}
//
// 使用方法:
// 1. 打开 https://code.earthengine.google.com/
// 2. 复制粘贴本代码
// 3. 点击 Run 运行
// 4. 在 Tasks 面板点击 Run 导出结果
// ================================================================

"""


def _build_boundary(geojson: dict | None) -> str:
    if not geojson:
        return "// WARNING: 未提供研究区边界\n"

    # 提取纯 geometry
    if geojson.get("type") == "FeatureCollection":
        features = geojson.get("features") or []
        if not features:
            return "// WARNING: FeatureCollection 为空\n"
        geometry = features[0]["geometry"]
    elif geojson.get("type") == "Feature":
        geometry = geojson["geometry"]
    else:
        geometry = geojson

    geometry_str = json.dumps(geometry)
    # 简化坐标精度到 5 位小数 (~1m)
    geometry_str = re.sub(r"(\d+\.\d{5})\d+", r"\1", geometry_str)

    return f"""// ========== 研究区边界 ==========
var boundary = ee.Geometry({geometry_str});
var roi = boundary;

Map.centerObject(boundary, 9);
Map.addLayer(boundary, {{color: 'white'}}, '研究区边界', false);

"""


def _build_cloud_mask(params: dict) -> str:
    # Sentinel-2 部分只在选了 sentinel2 时包含
    sentinel_section = ""
    if params["satellite"] == "sentinel2":
        sentinel_section = """
function maskCloudsSentinel2(image) {
  var qa = image.select('QA60');
  var cloudBit = 1 << 10;
  var cirrusBit = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBit).eq(0)
    .and(qa.bitwiseAnd(cirrusBit).eq(0));
  return image.updateMask(mask)
    .divide(10000);
}"""

    return f"""// ========== 云掩膜函数 ==========

function maskCloudsLandsat5(image) {{
  var qa = image.select('QA_PIXEL');
  var cloudShadow = 1 << 3;
  var clouds = 1 << 5;
  var mask = qa.bitwiseAnd(cloudShadow).eq(0)
    .and(qa.bitwiseAnd(clouds).eq(0));
  return image.updateMask(mask);
}}

function maskCloudsLandsat8(image) {{
  var qa = image.select('QA_PIXEL');
  var cloudShadow = 1 << 4;
  var clouds = 1 << 3;
  var mask = qa.bitwiseAnd(cloudShadow).eq(0)
    .and(qa.bitwiseAnd(clouds).eq(0));
  return image.updateMask(mask);
}}{sentinel_section}

"""


def _rsei_template(params: dict) -> str:
    sentinel_override = ""
    if params["satellite"] == "sentinel2":
        sentinel_override = """
    // Sentinel-2 override for 2015+
    if (year >= 2015) {
      collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(boundary)
        .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        .map(maskCloudsSentinel2);
    }"""

    year_calls = "\n".join(
        f"var rsei_{y} = calculateRSEI({y}, boundary);" for y in params["years"]
    )

    return f"""// ========== RSEI 遥感生态指数计算 ==========
// NDVI(绿度) + WET(湿度) + NDBSI(干度) + LST(热度) → PCA → RSEI

function normalize(image) {{
  var min = image.reduceRegion({{
    reducer: ee.Reducer.min(),
    geometry: boundary,
    scale: 30,
    maxPixels: 1e13
  }});
  var max = image.reduceRegion({{
    reducer: ee.Reducer.max(),
    geometry: boundary,
    scale: 30,
    maxPixels: 1e13
  }});
  return image.unitScale(min, max);
}}

function calculateRSEI(year, boundary) {{
  var startDate, endDate, collection;

  if (year <= 2011) {{
    collection = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat5);
  }} else if (year <= 2013) {{
    collection = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat5);
  }} else {{
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat8);
  }}{sentinel_override}

  var composite = collection.median().clip(boundary);

  // NDVI - 绿度
  var ndvi = composite.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI');

  // WET - 湿度 (Tasseled Cap Wetness)
  var wet = composite.expression(
    '0.1511*B2 + 0.1973*B3 + 0.3283*B4 + 0.3407*B5 + (-0.7117*B6) + (-0.4559*B7)', {{
    'B2': composite.select('SR_B2'),
    'B3': composite.select('SR_B3'),
    'B4': composite.select('SR_B4'),
    'B5': composite.select('SR_B5'),
    'B6': composite.select('SR_B6'),
    'B7': composite.select('SR_B7'),
  }}).rename('WET');

  // NDBSI - 干度 (IBI + SI)/2
  var mndwi = composite.normalizedDifference(['SR_B3', 'SR_B6']);
  var ndbi = composite.normalizedDifference(['SR_B6', 'SR_B5']);
  var si = composite.expression(
    '((B6 - B4) / (B6 + B4))', {{
    'B4': composite.select('SR_B4'),
    'B6': composite.select('SR_B6'),
  }});
  var ibi = ndbi.subtract(mndwi.add(si).divide(2));
  var ndbsi = ibi.rename('NDBSI');

  // LST - 热度
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
    .reduceRegion({{
      reducer: ee.Reducer.centeredCovariance(),
      geometry: boundary,
      scale: 30,
      maxPixels: 1e13
    }}).get('array'));

  var eigenvectors = ee.Tensor.pca(ee.Dictionary(pca).get('array'));

  var rsei = stack.arrayDotProduct(eigenvectors.slice(1, 0, 1).arrayProject([0]).arrayFlatten([['pc1']]))
    .rename('RSEI');

  return normalize(rsei).clip(boundary);
}}

// 生成 RSEI 影像
{year_calls}

"""


def _construction_template(params: dict) -> str:
    sentinel_override = ""
    if params["satellite"] == "sentinel2":
        sentinel_override = """
  if (year >= 2015) {
    collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
      .map(maskCloudsSentinel2);
  }"""

    year_calls = "\n".join(
        f"var construction_{y} = extractConstructionLand({y}, boundary);"
        for y in params["years"]
    )

    return f"""// ========== 建设用地提取 ==========
// 基于 MNDWI + NDVI + NDBI 阈值法提取不透水面

function extractConstructionLand(year, boundary) {{
  var startDate, endDate, collection;

  if (year <= 2011) {{
    collection = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat5);
  }} else if (year <= 2013) {{
    collection = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat5);
  }} else {{
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
      .filterBounds(boundary)
      .filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(year, 9, 30))
      .map(maskCloudsLandsat8);
  }}{sentinel_override}

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
}}

// 生成建设用地影像
{year_calls}

"""


def _expansion_template(params: dict) -> str:
    years = params["years"]
    if len(years) < 2:
        return "// 扩张模式分析需要至少 2 个时间节点，已跳过\n"

    sorted_years = sorted(years)
    comparisons = []
    for i in range(len(sorted_years) - 1):
        y1, y2 = sorted_years[i], sorted_years[i + 1]
        comparisons.append(
            f"// {y1} → {y2} 扩张模式\n"
            f"var expansion_mode_{y1}_{y2} = classifyExpansionMode(\n"
            f"  construction_{y1}, construction_{y2}\n"
            f");"
        )

    comparisons_str = "\n\n".join(comparisons)

    return f"""// ========== 城市扩张模式分类 ==========
// 边缘扩张(Edge) / 填充式(Infill) / 飞地式(Leapfrog)

function classifyExpansionMode(earlyConstruction, lateConstruction, bufferDist) {{
  bufferDist = bufferDist || 500;

  var newLand = lateConstruction.and(earlyConstruction.not())
    .rename('new_construction');

  var existingBuffer = earlyConstruction.reduceNeighborhood({{
    reducer: ee.Reducer.max(),
    kernel: ee.Kernel.circle(bufferDist, 'meters')
  }});

  var edge = newLand.and(existingBuffer);
  var leapfrog = newLand.and(existingBuffer.not());

  var existingExpand = earlyConstruction.reduceNeighborhood({{
    reducer: ee.Reducer.min(),
    kernel: ee.Kernel.circle(bufferDist * 0.5, 'meters')
  }});
  var infill = newLand.and(existingExpand);

  var mode = edge.multiply(1)
    .add(infill.multiply(2))
    .add(leapfrog.multiply(3))
    .rename('expansion_mode');

  return mode.selfMask();
}}

// 逐期扩张模式分类
{comparisons_str}

"""


def _nightlight_template(params: dict) -> str:
    year_calls = "\n".join(
        f"var ntl_{y} = extractNTL({y}, boundary);" for y in params["years"]
    )

    return """// ========== 夜间灯光数据提取 ==========
// DMSP-OLS (2000-2013) + VIIRS NTL (2014+)

function extractNTL(year, boundary) {
  var ntl;

  if (year <= 2013) {
    ntl = ee.ImageCollection('NOAA/DMSP-OLS/NIGHTTIME_LIGHTS')
      .filterMetadata('year', 'equals', year)
      .first()
      .select('stable_lights')
      .clip(boundary);
  } else {
    ntl = ee.ImageCollection('NOAA/VIIRS/DNB/ANNUAL_V22')
      .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 12, 31))
      .first()
      .select('average')
      .clip(boundary);
  }

  return ntl.rename('NTL');
}

// 生成夜间灯光影像
""" + year_calls + "\n\n"


def _population_template(params: dict) -> str:
    year_calls = "\n".join(
        f"var population_{y} = extractPopulation({y}, boundary);"
        for y in params["years"]
    )

    return """// ========== 人口密度数据提取 ==========
// WorldPop 100m 栅格人口数据

function extractPopulation(year, boundary) {
  var pop = ee.ImageCollection("WorldPop/GP/100m/pop")
    .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 12, 31))
    .filterBounds(boundary)
    .mosaic()
    .clip(boundary);

  return pop.rename('population');
}

// 生成人口密度影像
""" + year_calls + "\n\n"


def _gdp_template(params: dict) -> str:
    """GDP 模板 — 使用 Kummu et al. (2025) 1km 网格 GDP per capita 数据集。"""
    year_calls = "\n".join(
        f"var gdp_{y} = extractGDP({y}, boundary);" for y in params["years"]
    )

    return """// ========== GDP 分布数据提取 ==========
// 使用 Kummu et al. (2025) Gridded GDP per capita (PPP, constant 2021 USD)
// 数据源: projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022
// 波段: PPP_YYYY (覆盖 1990-2022)

function extractGDP(year, boundary) {
  if (year < 1990 || year > 2022) {
    print('GDP 数据仅覆盖 1990-2022，年份 ' + year + ' 不可用');
    return ee.Image.constant(0).rename('GDP_per_capita');
  }
  var gdpImg = ee.Image(
    'projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022'
  );
  return gdpImg.select('PPP_' + year).clip(boundary).rename('GDP_per_capita');
}

// 生成 GDP 影像
""" + year_calls + "\n\n"


def _build_export(params: dict) -> str:
    """生成导出代码 — Google Drive 或 Earth Engine Asset。"""
    years = params["years"]
    indicators = params["indicators"]
    export_format = params["export_format"]
    export_prefix = params["export_prefix"]

    # 收集所有要导出的影像变量
    images: list[dict[str, str]] = []
    for y in years:
        if "rsei" in indicators:
            images.append({"name": f"rsei_{y}", "var": f"rsei_{y}"})
        if "construction" in indicators:
            images.append({"name": f"construction_{y}", "var": f"construction_{y}"})
        if "nightLight" in indicators:
            images.append({"name": f"ntl_{y}", "var": f"ntl_{y}"})
        if "population" in indicators:
            images.append({"name": f"population_{y}", "var": f"population_{y}"})
        if "gdp" in indicators:
            images.append({"name": f"gdp_{y}", "var": f"gdp_{y}"})

    # 扩张模式是逐期对比
    if "expansion" in indicators:
        sorted_years = sorted(years)
        for i in range(len(sorted_years) - 1):
            y1, y2 = sorted_years[i], sorted_years[i + 1]
            images.append({
                "name": f"expansion_mode_{y1}_{y2}",
                "var": f"expansion_mode_{y1}_{y2}",
            })

    code = "// ========== 导出结果 ==========\n"

    if export_format == "drive":
        code += "// 导出到 Google Drive\n"
        for img in images:
            code += f"""
Export.image.toDrive({{
  image: {img['var']},
  description: '{export_prefix}_{img['name']}',
  folder: 'GEE_exports',
  region: boundary,
  scale: 30,
  maxPixels: 1e13,
  crs: 'EPSG:4326',
}});
"""
    else:
        code += "// 导出到 Earth Engine Asset\n"
        code += "// 请替换 YOUR_USERNAME 为你的 GEE 用户名\n"
        for img in images:
            code += f"""
Export.image.toAsset({{
  image: {img['var']},
  description: '{export_prefix}_{img['name']}',
  assetId: 'users/YOUR_USERNAME/{export_prefix}_{img['name']}',
  region: boundary,
  scale: 30,
  maxPixels: 1e13,
  crs: 'EPSG:4326',
}});
"""

    return code


# ─── 模板注册表 ───

_TEMPLATES: dict[str, Any] = {
    "rsei": _rsei_template,
    "construction": _construction_template,
    "expansion": _expansion_template,
    "nightLight": _nightlight_template,
    "population": _population_template,
    "gdp": _gdp_template,
}
