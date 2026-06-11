"""
区县（子区域）分析
==================
从 gee_service.py 拆出的纯函数，负责逐区县 clip 求指标。

优先使用自定义县级区划 Asset（含中文名），
若 Asset 不存在则回退到 FAO/GAUL/2015/level2（地级市粒度）。
"""

from __future__ import annotations

import logging
from typing import Any

from app.district_names import to_chinese_name_by_code
from app.gee.built import sum_built_area
from app.gee.socio import (
    district_ntl,
    district_population,
    get_gdp_per_capita,
)

logger = logging.getLogger("ueea2601.gee.district")


def compute_district_stats(
    boundary,
    geojson: dict,
    yearly_results: dict,
    years: list[int],
    rsei_image=None,
    built_image=None,
    indicators: list[str] | None = None,
) -> list[dict]:
    """子区域（区县）分析。

    Args:
        boundary: ee.Geometry 边界
        geojson: 边界 GeoJSON
        yearly_results: {year: result_dict} 逐年计算结果
        years: 年份列表
        rsei_image: 末年已算好的 RSEI ee.Image，用于逐区县 clip 求均值。
        built_image: 末年已算好的 built_binary ee.Image，用于逐区县 clip 求面积。
                     为 None 时区县建设用地为 0。
        indicators: 用户选择的指标列表。None 表示全选（向后兼容）。

    Returns:
        区县统计列表 [{"name", "built_area_km2", "rsei_mean", ...}, ...]
    """
    import ee

    from app.config import COUNTY_ASSET_ID

    if not indicators:
        indicators = ["rsei", "construction", "expansion", "nightLight", "population", "gdp"]

    districts: list[dict] = []
    last_year = years[-1]
    last_data = yearly_results.get(last_year, {})

    try:
        # ── 尝试使用自定义县级 Asset ──
        county_fc = None
        use_county_asset = False
        try:
            county_fc = ee.FeatureCollection(COUNTY_ASSET_ID)
            size = county_fc.size().getInfo()
            if size and size > 0:
                use_county_asset = True
                logger.info(f"Using county asset: {COUNTY_ASSET_ID} ({size} features)")
            else:
                logger.warning(f"County asset empty: {COUNTY_ASSET_ID}, falling back to GAUL")
        except Exception as e:
            logger.warning(f"County asset not available ({COUNTY_ASSET_ID}): {e}, falling back to GAUL")

        # ── 选择数据源 ──
        if use_county_asset:
            base_fc = county_fc.filterBounds(boundary)
        else:
            base_fc = ee.FeatureCollection("FAO/GAUL/2015/level2").filterBounds(boundary)

        # ── 空间过滤：排除与用户边界重叠比例过低的区县 ──
        min_overlap_ratio = 0.03

        def _add_overlap(feature):
            geom = feature.geometry()
            inter = geom.intersection(boundary, ee.ErrorMargin(1))
            ratio = inter.area(1).divide(geom.area(1).max(1))
            return feature.set('_overlap', ratio)

        try:
            scored_fc = base_fc.map(_add_overlap)
            filtered_fc = scored_fc.filter(ee.Filter.gt('_overlap', min_overlap_ratio))
        except Exception:
            logger.warning("Overlap ratio filtering failed, falling back to raw filterBounds")
            filtered_fc = base_fc

        district_features = filtered_fc.getInfo()

        if not district_features or not district_features.get("features"):
            logger.info("No district features found within boundary (after overlap filtering)")
            return []

        for feat in district_features["features"][:30]:
            props = feat.get("properties", {})

            # ── 区县名称：优先用中文名字段 ──
            name = ""
            if use_county_asset:
                name = (
                    props.get("name")
                    or props.get("NAME")
                    or props.get("name_CHN")
                    or ""
                )
            if not name:
                adm2_code = props.get("ADM2_CODE")
                name_en = (
                    props.get("ADM2_NAME")
                    or props.get("NAME2")
                    or props.get("ADM1_NAME")
                    or props.get("NAME1")
                    or "unknown"
                )
                name = to_chinese_name_by_code(adm2_code, name_en)

            district_geom = ee.Geometry(feat["geometry"])
            analysis_geom = district_geom.intersection(boundary, ee.ErrorMargin(1))

            try:
                # 区县建设用地
                built_km2 = 0.0
                if "construction" in indicators and built_image is not None:
                    try:
                        built_district = built_image.clip(analysis_geom)
                        built_km2 = sum_built_area(built_district, analysis_geom, scale=30)
                    except Exception as e:
                        logger.warning(f"District {name} built clip failed: {e}")

                # 区县 RSEI
                rsei_mean = 0.0
                if "rsei" in indicators and rsei_image is not None:
                    try:
                        rsei_district = rsei_image.clip(analysis_geom)
                        rsei_result = rsei_district.reduceRegion(
                            ee.Reducer.mean(), analysis_geom, 500,
                            maxPixels=1e12, bestEffort=True, tileScale=4,
                        ).getInfo()
                        if rsei_result:
                            rsei_mean = round(float(rsei_result.get("RSEI", 0)), 4)
                    except Exception as e:
                        logger.warning(f"District {name} RSEI failed: {e}")
                        rsei_mean = last_data.get("rsei_mean", 0)
                elif "rsei" in indicators:
                    rsei_mean = last_data.get("rsei_mean", 0)

                # 区县 GDP per capita
                d_gdp_pc = None
                if "gdp" in indicators:
                    d_gdp_pc_ppp = get_gdp_per_capita(analysis_geom, last_year)
                    from app.config import GDP_USD_TO_RMB as _rate2
                    d_gdp_pc = round(d_gdp_pc_ppp * _rate2) if d_gdp_pc_ppp else None

                # 区县人口
                d_pop = 0
                if "population" in indicators:
                    d_pop = district_population(analysis_geom, last_year)

                # 区县夜灯
                d_ntl = 0.0
                if "nightLight" in indicators:
                    d_ntl = district_ntl(analysis_geom, last_year)

                districts.append({
                    "name": name,
                    "built_area_km2": built_km2,
                    "rsei_mean": rsei_mean,
                    "population": d_pop,
                    "ntl_sum": d_ntl,
                    "gdp_per_capita": d_gdp_pc,
                    "gdp_total": None,
                })
                # 计算区县总 GDP（人民币）
                d = districts[-1]
                if d_gdp_pc and d_pop > 0:
                    d["gdp_total"] = round(d_gdp_pc * d_pop, 0)
            except Exception as e:
                logger.warning(f"District {name} failed: {e}")
                districts.append({
                    "name": name,
                    "built_area_km2": 0,
                    "rsei_mean": 0,
                    "population": 0,
                    "ntl_sum": 0,
                    "gdp_per_capita": None,
                    "gdp_total": None,
                })

    except Exception as e:
        logger.warning(f"District analysis failed: {e}")

    return districts
