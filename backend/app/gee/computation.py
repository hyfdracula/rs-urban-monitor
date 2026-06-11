"""
年度指标计算
============
从 gee_service.py 拆出的纯函数，负责单年度 GEE 指标计算。

两个入口：
- compute_year_optimal: 按用户选择指标选择性计算（_compute_year_opt）
- compute_year_full:    全指标计算（_compute_year，向后兼容）
"""

from __future__ import annotations

import logging
from typing import Any

from app import tasks
from app.gee.built import (
    compute_built_up,
    sum_built_area,
)
from app.gee.data_sources import (
    WET_COEFFICIENTS,
    get_landsat_source,
    get_ntl_source,
)
from app.gee.indices import compute_rsei
from app.gee.socio import (
    compute_gdp_total,
    get_gdp_image_and_stats,
    get_ntl_sum,
    get_population,
)

logger = logging.getLogger("ueea2601.gee.computation")


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _make_progress_cb(task_id: str | None, year: int,
                      year_index: int, total_years: int,
                      cancel_event: Any = None):
    """构造年度内进度回调。

    进度区间映射：year_index/total_years 占总进度的 0~70%，
    每年内再按 sub_ratio 0.0~1.0 细分。
    """
    def _progress(step_name: str, sub_ratio: float):
        if task_id is None:
            return
        if cancel_event and cancel_event.is_set():
            return
        base = int((year_index / total_years) * 70)
        end = int(((year_index + 1) / total_years) * 70)
        percent = base + int((end - base) * sub_ratio)
        tasks.update_progress(task_id, year, f"{year}年 · {step_name}", percent)
    return _progress


def _build_landsat_composite(ee, boundary, year: int,
                             progress_cb=None) -> tuple:
    """构建 Landsat 合成影像，返回 (bands_dict, composite, band_map, img_count)。

    bands_dict: {"blue": ee.Image, "nir": ee.Image, ...}
    composite:  median.addBands([ndvi, wet, ndbsi, lst])
    band_map:   原始波段映射
    """
    collection_id, band_map, sensor = get_landsat_source(year)
    wet_coeff = WET_COEFFICIENTS.get(sensor, WET_COEFFICIENTS["TM"])

    window = 3
    start_date = f"{year - window}-01-01"
    end_date = f"{year + window}-12-31"
    cloud_threshold = 50 if year <= 1995 else 40

    collection = (
        ee.ImageCollection(collection_id)
        .filterBounds(boundary)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUD_COVER", cloud_threshold))
    )

    img_count = collection.size().getInfo()
    logger.info(f"[{year}] 影像数量={img_count}, 集合={collection_id}, "
                f"窗口={start_date}~{end_date}, 云阈值={cloud_threshold}")

    median = collection.median().clip(boundary)

    # Landsat C2 L2 缩放
    b = {}
    for k, band_name in band_map.items():
        if k == "thermal":
            b[k] = median.select(band_name).multiply(0.00341802).add(149.0).rename(band_name)
        else:
            b[k] = median.select(band_name).multiply(0.0000275).add(-0.2).rename(band_name)

    ndvi = b["nir"].subtract(b["red"]).divide(b["nir"].add(b["red"])).rename("NDVI")
    wet = (
        b["blue"].multiply(wet_coeff["blue"])
        .add(b["green"].multiply(wet_coeff["green"]))
        .add(b["red"].multiply(wet_coeff["red"]))
        .add(b["nir"].multiply(wet_coeff["nir"]))
        .add(b["swir1"].multiply(wet_coeff["swir1"]))
        .add(b["swir2"].multiply(wet_coeff["swir2"]))
    ).rename("WET")
    ibi = (b["nir"].multiply(2).subtract(b["red"]).subtract(b["swir1"])).divide(
        b["nir"].multiply(2).add(b["red"]).add(b["swir1"])
    )
    si = (
        (b["swir1"].subtract(b["red"])).divide(b["swir1"].add(b["red"]))
    ).add(
        (b["swir1"].subtract(b["nir"])).divide(b["swir1"].add(b["nir"]))
    )
    ndbsi = ibi.add(si).divide(2).rename("NDBSI")
    lst = b["thermal"].subtract(273.15).rename("LST")
    composite = median.addBands([ndvi, wet, ndbsi, lst])

    return b, composite, band_map, img_count


# ---------------------------------------------------------------------------
# 公开接口
# ---------------------------------------------------------------------------

def compute_year_optimal(
    boundary,
    geojson: dict,
    year: int,
    indicators: list[str],
    need_landsat: bool = True,
    task_id: str | None = None,
    year_index: int = 0,
    total_years: int = 1,
    cancel_event: Any = None,
) -> dict:
    """按用户选择的指标选择性计算单个年份。

    当 need_landsat=False 时跳过整个 Landsat 处理流程（节省大量时间）。
    """
    import ee

    _progress = _make_progress_cb(task_id, year, year_index, total_years, cancel_event)

    # 默认值
    result: dict[str, Any] = {
        "built_area_km2": 0,
        "ndvi_mean": 0,
        "rsei_mean": 0,
        "lst_mean": 0,
        "wet_mean": 0,
        "ndbsi_mean": 0,
        "population": 0,
        "gdp_per_capita": None,
        "gdp_total": None,
        "ntl_sum": None,
        "ntl_available": False,
    }
    images: dict[str, Any] = {}
    rsei_image = None

    # ── Landsat 处理（仅 rsei 或 construction 需要时）──
    if need_landsat:
        _progress("构建影像合成", 0.0)
        b, composite, band_map, _ = _build_landsat_composite(ee, boundary, year)

        # RSEI（仅选中时计算）
        if "rsei" in indicators:
            _progress("计算指数统计...", 0.15)
            index_stats = composite.select(["NDVI", "WET", "NDBSI", "LST"]).reduceRegion(
                ee.Reducer.mean(), boundary, 500,
                maxPixels=1e12, bestEffort=True, tileScale=4,
            ).getInfo()
            logger.info(f"[{year}] index_stats={index_stats}")

            if index_stats:
                result["ndvi_mean"] = round(float(index_stats.get("NDVI", 0)), 4)
                result["wet_mean"] = round(float(index_stats.get("WET", 0)), 4)
                result["ndbsi_mean"] = round(float(index_stats.get("NDBSI", 0)), 4)
                result["lst_mean"] = round(float(index_stats.get("LST", 0)), 1)

            _progress("计算 RSEI...", 0.35)
            rsei = compute_rsei(composite, boundary)
            rsei_stats = rsei.reduceRegion(
                ee.Reducer.mean().combine(ee.Reducer.minMax(), "", True),
                boundary, 500, maxPixels=1e12, bestEffort=True, tileScale=4,
            ).getInfo()
            logger.info(f"[{year}] rsei_stats={rsei_stats}")
            if rsei_stats:
                result["rsei_mean"] = round(float(rsei_stats.get("RSEI_mean", 0)), 4)
            rsei_image = rsei
            images["rsei"] = rsei
            images["ndvi"] = composite.select("NDVI")
        else:
            _progress("跳过 RSEI（未选择）", 0.35)

        # 建设用地（仅选中时计算）
        if "construction" in indicators:
            _progress("计算建设用地...", 0.55)
            built_area, built_binary = compute_built_up(composite, band_map, boundary, year)
            result["built_area_km2"] = built_area
            images["built"] = built_binary
            logger.info(f"[{year}] built_area={built_area}")
        else:
            _progress("跳过建设用地（未选择）", 0.55)
    else:
        _progress("跳过 Landsat 处理（无需 Landsat 指标）", 0.5)
        logger.info(f"[{year}] Landsat skipped (no rsei/construction selected)")

    # ── 人口（独立，需先于 GDP 计算）──
    if "population" in indicators:
        _progress("提取人口数据...", 0.60)
        if 2000 <= year <= 2020:
            result["population"] = get_population(boundary, year)
        logger.info(f"[{year}] population={result['population']}")
    else:
        _progress("跳过人口（未选择）", 0.60)

    # ── GDP（独立，依赖人口作为 fallback）──
    if "gdp" in indicators:
        _progress("提取 GDP 数据...", 0.75)
        gdp_pc_ppp, gdp_image = get_gdp_image_and_stats(boundary, year)

        gdp_total_ppp = None
        if gdp_image is not None and 2000 <= year <= 2020:
            gdp_total_ppp = compute_gdp_total(gdp_image, boundary, year)
        if gdp_total_ppp is None and gdp_pc_ppp and result["population"] > 0:
            gdp_total_ppp = round(gdp_pc_ppp * result["population"], 0)

        from app.config import GDP_USD_TO_RMB as _rate
        result["gdp_per_capita"] = round(gdp_pc_ppp * _rate) if gdp_pc_ppp else None
        result["gdp_total"] = round(gdp_total_ppp * _rate) if gdp_total_ppp else None
        if gdp_image is not None:
            images["gdp"] = gdp_image
        logger.info(f"[{year}] gdp_pc={gdp_pc_ppp}, gdp_total={result['gdp_total']}")
    else:
        _progress("跳过 GDP（未选择）", 0.75)

    # ── 夜灯（独立）──
    if "nightLight" in indicators:
        _progress("提取夜灯数据...", 0.90)
        ntl_collection, ntl_ok = get_ntl_source(year)
        result["ntl_available"] = ntl_ok
        if ntl_ok and ntl_collection:
            result["ntl_sum"] = get_ntl_sum(boundary, ntl_collection, year)
    else:
        _progress("跳过夜灯（未选择）", 0.90)

    _progress("完成", 1.0)
    logger.info(f"[{year}] DONE: rsei={result['rsei_mean']}, built={result['built_area_km2']}, "
                f"pop={result['population']}, gdp={result['gdp_per_capita']}, ntl={result['ntl_sum']}")

    result["_rsei_image"] = rsei_image
    result["_images"] = images
    return result


def compute_year_full(
    boundary,
    geojson: dict,
    year: int,
    task_id: str | None = None,
    year_index: int = 0,
    total_years: int = 1,
    cancel_event: Any = None,
) -> dict:
    """计算单个年份的所有指标（向后兼容老接口）。"""
    import ee

    _progress = _make_progress_cb(task_id, year, year_index, total_years, cancel_event)

    _progress("构建影像合成", 0.0)
    b, composite, band_map, _ = _build_landsat_composite(ee, boundary, year)

    # 指数统计
    _progress("计算指数统计...", 0.15)
    index_stats = composite.select(["NDVI", "WET", "NDBSI", "LST"]).reduceRegion(
        ee.Reducer.mean(),
        boundary,
        500,
        maxPixels=1e12,
        bestEffort=True,
        tileScale=4,
    ).getInfo()
    logger.info(f"[{year}] index_stats={index_stats}")

    ndvi_mean = 0.0
    wet_mean = 0.0
    ndbsi_mean = 0.0
    lst_mean = 0.0
    if index_stats:
        ndvi_mean = round(float(index_stats.get("NDVI", 0)), 4)
        wet_mean = round(float(index_stats.get("WET", 0)), 4)
        ndbsi_mean = round(float(index_stats.get("NDBSI", 0)), 4)
        lst_mean = round(float(index_stats.get("LST", 0)), 1)

    # RSEI
    _progress("计算 RSEI...", 0.35)
    rsei = compute_rsei(composite, boundary)
    rsei_stats = rsei.reduceRegion(
        ee.Reducer.mean().combine(ee.Reducer.minMax(), "", True),
        boundary,
        500,
        maxPixels=1e12,
        bestEffort=True,
        tileScale=4,
    ).getInfo()
    logger.info(f"[{year}] rsei_stats={rsei_stats}")
    rsei_mean = 0.0
    if rsei_stats:
        rsei_mean = round(float(rsei_stats.get("RSEI_mean", 0)), 4)

    # 建设用地面积
    _progress("计算建设用地...", 0.55)
    built_area, built_binary = compute_built_up(composite, band_map, boundary, year)
    logger.info(f"[{year}] built_area={built_area}")

    # 人口 (WorldPop 2000-2020)
    _progress("提取人口数据...", 0.60)
    population = 0
    if 2000 <= year <= 2020:
        population = get_population(boundary, year)
    logger.info(f"[{year}] population={population}")

    # GDP per capita (Kummu et al. 2025, 1km 网格, 1990-2022)
    _progress("提取 GDP 数据...", 0.75)
    gdp_pc_ppp, gdp_image = get_gdp_image_and_stats(boundary, year)

    gdp_total_ppp = None
    if gdp_image is not None and 2000 <= year <= 2020:
        gdp_total_ppp = compute_gdp_total(gdp_image, boundary, year)
    if gdp_total_ppp is None and gdp_pc_ppp and population > 0:
        gdp_total_ppp = round(gdp_pc_ppp * population, 0)

    from app.config import GDP_USD_TO_RMB as _rate
    gdp_per_capita = round(gdp_pc_ppp * _rate) if gdp_pc_ppp else None
    gdp_total = round(gdp_total_ppp * _rate) if gdp_total_ppp else None
    logger.info(f"[{year}] gdp_pc={gdp_pc_ppp} PPP$ → {gdp_per_capita} RMB, "
                f"gdp_total={gdp_total} RMB")

    # 夜灯
    _progress("提取夜灯数据...", 0.90)
    ntl_collection, ntl_ok = get_ntl_source(year)
    ntl_sum = None
    if ntl_ok and ntl_collection:
        ntl_sum = get_ntl_sum(boundary, ntl_collection, year)

    _progress("完成", 1.0)
    logger.info(f"[{year}] DONE: ndvi={ndvi_mean}, rsei={rsei_mean}, "
                f"built={built_area}, pop={population}, ntl={ntl_sum}")

    return {
        "built_area_km2": built_area,
        "ndvi_mean": ndvi_mean,
        "rsei_mean": rsei_mean,
        "lst_mean": lst_mean,
        "wet_mean": wet_mean,
        "ndbsi_mean": ndbsi_mean,
        "population": population,
        "gdp_per_capita": gdp_per_capita,
        "gdp_total": gdp_total,
        "ntl_sum": ntl_sum,
        "ntl_available": ntl_ok,
        "_rsei_image": rsei,
        "_images": {
            "rsei": rsei,
            "ndvi": composite.select("NDVI"),
            "built": built_binary,
            "gdp": gdp_image,
        },
    }
