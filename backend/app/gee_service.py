"""
GEE 在线计算服务
==============
动态多年度计算：
- 根据用户选择年份自动选择 Landsat 数据源 (L5/L7/L8/L9)
- 传感器特定 WET 系数 (TM/ETM/OLI)
- 夜灯数据源 (DMSP-OLS / VIIRS)
- NDBI 建设用地分类
- WorldPop 人口估算
- 异步后台线程执行，支持取消
"""

from __future__ import annotations

import json
import logging
import os
import tempfile

from app.district_names import to_chinese_name, to_chinese_name_by_code
from typing import Any

from app import tasks
from app.database import get_db_context
from app.models import UserBoundary
from app.config import MAX_CONCURRENT_GEE_TASKS, PUBLIC_ACCOUNT_DAILY_LIMIT

logger = logging.getLogger("ueea2601.gee")


# ─── Landsat 数据源映射 ───

LANDSAT_SOURCES: dict[str, dict] = {
    "LT05": {
        "collection": "LANDSAT/LT05/C02/T1_L2",
        "bands": {
            "blue": "SR_B1", "green": "SR_B2", "red": "SR_B3",
            "nir": "SR_B4", "swir1": "SR_B5", "swir2": "SR_B7",
            "thermal": "ST_B6",
        },
        "sensor": "TM",
    },
    "LE07": {
        "collection": "LANDSAT/LE07/C02/T1_L2",
        "bands": {
            "blue": "SR_B1", "green": "SR_B2", "red": "SR_B3",
            "nir": "SR_B4", "swir1": "SR_B5", "swir2": "SR_B7",
            "thermal": "ST_B6",
        },
        "sensor": "ETM",
    },
    "LC08": {
        "collection": "LANDSAT/LC08/C02/T1_L2",
        "bands": {
            "blue": "SR_B2", "green": "SR_B3", "red": "SR_B4",
            "nir": "SR_B5", "swir1": "SR_B6", "swir2": "SR_B7",
            "thermal": "ST_B10",
        },
        "sensor": "OLI",
    },
    "LC09": {
        "collection": "LANDSAT/LC09/C02/T1_L2",
        "bands": {
            "blue": "SR_B2", "green": "SR_B3", "red": "SR_B4",
            "nir": "SR_B5", "swir1": "SR_B6", "swir2": "SR_B7",
            "thermal": "ST_B10",
        },
        "sensor": "OLI",
    },
}

# ─── WET 缆帽变换系数 ───

WET_COEFFICIENTS: dict[str, dict[str, float]] = {
    "TM": {
        "blue": 0.1509, "green": 0.1973, "red": 0.3279,
        "nir": 0.3406, "swir1": -0.7112, "swir2": -0.4572,
    },
    "ETM": {
        "blue": 0.1509, "green": 0.1973, "red": 0.3279,
        "nir": 0.3406, "swir1": -0.7112, "swir2": -0.4572,
    },
    "OLI": {
        "blue": 0.3029, "green": 0.2786, "red": 0.4733,
        "nir": 0.5599, "swir1": 0.5080, "swir2": -0.1872,
    },
}

# ─── 建设用地检测阈值 ───
BUILT_NDBSI_MIN = -0.2       # NDBSI > this → possibly built (从 -0.1 放宽)
BUILT_NDVI_MAX = 0.5         # NDVI < this → not dense vegetation (从 0.4 放宽)
BUILT_MNDWI_MAX = 0.3        # MNDWI < this → not water (不变)
BUILT_DW_PROB_MIN = 0.30     # Dynamic World built probability 阈值
BUILT_GHSL_COLLECTION = "JRC/GHSL/P2023A/GHS_BUILT_S"
BUILT_GHSL_YEARS = (1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030)
BUILT_GHSL_MIN_SURFACE_M2 = 1.0


def _get_landsat_source(year: int) -> tuple[str, dict, str]:
    """根据年份选择 Landsat 数据源、波段映射和传感器类型。"""
    if year >= 2021:
        src = LANDSAT_SOURCES["LC09"]
    elif year >= 2013:
        src = LANDSAT_SOURCES["LC08"]
    elif 1999 <= year <= 2003:
        src = LANDSAT_SOURCES["LE07"]
    else:
        src = LANDSAT_SOURCES["LT05"]
    return src["collection"], src["bands"], src["sensor"]


def _get_ntl_source(year: int) -> tuple[str | None, bool]:
    """根据年份选择夜灯数据源。返回 (collection_id, available)。
    使用 ImageCollection + filterDate 代替硬编码 image ID，避免 ID 格式错误。
    """
    if 1984 <= year <= 1991:
        return None, False
    if 1992 <= year <= 2013:
        return "NOAA/DMSP-OLS/NIGHTTIME_LIGHTS", True
    if year >= 2012:
        return "NOAA/VIIRS/DNB/ANNUAL_V21", True
    return None, False


def _get_gdp_band(year: int) -> str | None:
    """返回 Kummu et al. (2025) 1km 网格 GDP 数据集的 band name。

    数据源: Kummu et al. (2025) Gridded GDP per capita (PPP),
            Scientific Data (Nature), 30 arc-sec (~1km), 1990-2022.
    Asset: projects/sat-io/open-datasets/GRIDDED_HDI_GDP/adm2_gdp_perCapita_1990_2022
    Band:  PPP_YYYY (GDP per capita, PPP, constant 2021 USD)
    """
    if 1990 <= year <= 2022:
        return f"PPP_{year}"
    return None


class GEEOnlineService:

    def __init__(self) -> None:
        self._initialized = False

    def _init_with_key_json(self, key_json: str, service_account: str) -> str | None:
        """用 JSON 字符串密钥初始化 GEE，返回临时文件路径。

        失败时自动清理临时文件，不会残留敏感 JSON。
        """
        key_path = None
        try:
            import ee
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                f.write(key_json)
                key_path = f.name
            credentials = ee.ServiceAccountCredentials(service_account, key_path)
            ee.Initialize(credentials)
            return key_path
        except Exception as e:
            logger.error(f"GEE init with user key failed: {e}")
            if key_path:
                try:
                    os.unlink(key_path)
                except OSError:
                    pass
            return None

    @property
    def available(self) -> bool:
        return True

    # ─── 同步模式（兼容旧接口）───

    def submit_task(
        self,
        geojson: dict,
        boundary_id: int,
        task_id: str,
        user_key: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        """同步模式：兼容旧接口，只用2020年。"""
        if user_key is None:
            return {
                "success": False,
                "gee_tasks": [],
                "error": "请先在「GEE配置」页面上传并验证您的 GEE 密钥",
            }

        service_account, key_json = user_key
        temp_key_path = self._init_with_key_json(key_json, service_account)
        if temp_key_path is None:
            return {
                "success": False,
                "gee_tasks": [],
                "error": "GEE 初始化失败，请检查密钥是否有效",
            }

        try:
            result = self._run_single_year(geojson, boundary_id, 2020)
        finally:
            try:
                os.unlink(temp_key_path)
            except Exception:
                pass

        return result

    # ─── 异步多年度计算（后台线程）───

    def submit_task_async(
        self,
        geojson: dict,
        boundary_id: int,
        task_id: str,
        years: list[int],
        user_key: tuple[str, str],
        indicators: list[str] | None = None,
        cancel_event: Any = None,
    ) -> None:
        """异步计算：遍历用户选择的年份。由 tasks.start_background 调用。

        Args:
            indicators: 用户选择的指标列表。None 或空列表表示全选（向后兼容）。
        """
        import ee

        if not indicators:
            indicators = ["rsei", "construction", "expansion", "nightLight", "population", "gdp"]

        service_account, key_json = user_key
        temp_key_path = self._init_with_key_json(key_json, service_account)
        if temp_key_path is None:
            tasks.update_task(task_id, status="failed",
                              progress_info={"year": None, "step": "GEE 初始化失败", "percent": 0})
            return

        try:
            self._run_multi_year(geojson, boundary_id, task_id, years, cancel_event, indicators)
        finally:
            try:
                os.unlink(temp_key_path)
            except Exception:
                pass

    def _run_multi_year(
        self,
        geojson: dict,
        boundary_id: int,
        task_id: str,
        years: list[int],
        cancel_event: Any,
        indicators: list[str],
    ) -> None:
        """多年度 GEE 计算，逐年遍历。按 indicators 选择性计算。

        Args:
            indicators: 用户选择的指标列表。控制哪些计算步骤会被执行。
        """
        import ee

        boundary = ee.Geometry(geojson)
        yearly_results: dict[int, dict] = {}
        total_years = len(years)

        # 判断是否需要 Landsat 处理
        need_landsat = "rsei" in indicators or "construction" in indicators
        logger.info(f"Task {task_id}: indicators={indicators}, need_landsat={need_landsat}")

        for i, year in enumerate(years):
            # 检查取消
            if cancel_event and cancel_event.is_set():
                logger.info(f"Task {task_id} cancelled at year {year}")
                return

            logger.info(f"Task {task_id}: computing year {year} ({i+1}/{total_years})")

            try:
                result = self._compute_year_opt(
                    boundary, geojson, year,
                    indicators=indicators,
                    need_landsat=need_landsat,
                    task_id=task_id, year_index=i,
                    total_years=total_years, cancel_event=cancel_event,
                )
                yearly_results[year] = result
                logger.info(f"Year {year} done: built={result['built_area_km2']}km², "
                            f"rsei={result['rsei_mean']}, pop={result['population']}")
            except Exception as e:
                logger.error(f"Year {year} failed: {e}", exc_info=True)
                yearly_results[year] = {
                    "error": str(e),
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

        # 检查取消
        if cancel_event and cancel_event.is_set():
            return

        # 提取末年 RSEI 影像供区县分析复用（仅 rsei 选中时）
        last_year_data = yearly_results.get(years[-1], {})
        rsei_image = last_year_data.pop("_rsei_image", None)

        # 变化分析（仅 construction 选中且有 ≥2 年时）
        tasks.update_progress(task_id, None, "变化分析...", 73)
        if "construction" in indicators and len(years) >= 2:
            change_stats = self._compute_change(yearly_results, years)
        elif len(years) >= 2:
            # 非 construction 模式，仍然计算非建设用地的变化指标
            change_stats = self._compute_change_partial(yearly_results, years, indicators)
        else:
            change_stats = {"single_year": True}

        # 区县分析（按指标选择性调用）
        tasks.update_progress(task_id, None, "子区域分析...", 77)
        last_year = years[-1]
        built_image = yearly_results.get(last_year, {}).get("_images", {}).get("built") if "construction" in indicators else None
        district_stats = self._compute_district_stats(
            boundary, geojson, yearly_results, years,
            rsei_image=rsei_image if "rsei" in indicators else None,
            built_image=built_image,
            indicators=indicators,
        )

        # 提前获取边界信息（导出和报告都需要）
        with get_db_context() as db:
            b = db.query(UserBoundary).filter_by(id=boundary_id).first()
            boundary_name = b.name if b else "unknown"
            boundary_area_km2 = b.area_km2 if b else None

        # ── 导出栅格 → GeoServer ──
        wms_urls = {}
        try:
            # 收集每年的 ee.Image 引用（在 pop 掉之前）
            yearly_images = {}
            for y in years:
                yr_data = yearly_results.get(y, {})
                yearly_images[y] = yr_data.get("_images", {})

            # 多年份：计算并导出 new_built
            if len(years) >= 2:
                first_imgs = yearly_images.get(years[0], {})
                last_imgs = yearly_images.get(years[-1], {})
                new_built_img = self._compute_new_built(
                    first_imgs.get("built"),
                    last_imgs.get("built"),
                    boundary,
                )
                if new_built_img is not None:
                    yearly_images["_change"] = {"new_built": new_built_img}

            # 统计总栅格数（用于逐栅格进度更新）
            total_rasters = 0
            for y in years:
                imgs = yearly_images.get(y, {})
                if imgs:
                    total_rasters += len(imgs)
            change_imgs_count = 0
            change_imgs_dict = yearly_images.get("_change", {})
            if change_imgs_dict:
                change_imgs_count = len(change_imgs_dict)
                total_rasters += change_imgs_count

            raster_idx = [0]  # mutable counter

            def _export_progress():
                if total_rasters > 0:
                    pct = 80 + int((raster_idx[0] / total_rasters) * 10)
                    tasks.update_progress(task_id, None,
                        f"导出栅格数据... ({raster_idx[0]}/{total_rasters})", pct)

            # 逐年导出（逐栅格更新进度）
            tasks.update_progress(task_id, None,
                f"导出栅格数据... (0/{total_rasters})" if total_rasters else "导出栅格数据...", 80)
            all_exported: dict[str, str] = {}
            for y in years:
                imgs = yearly_images.get(y, {})
                if imgs:
                    exported = self._export_rasters(
                        boundary, boundary_id, y, imgs,
                        area_km2=boundary_area_km2,
                        progress_cb=_export_progress,
                        raster_idx=raster_idx,
                    )
                    all_exported.update(exported)

            # 导出变化图
            if change_imgs_dict:
                exported = self._export_rasters(
                    boundary, boundary_id, None, change_imgs_dict,
                    area_km2=boundary_area_km2,
                    progress_cb=_export_progress,
                    raster_idx=raster_idx,
                )
                all_exported.update(exported)

            # 发布到 GeoServer（逐图层更新进度）
            if all_exported:
                pub_total = len(all_exported)
                pub_idx = 0
                tasks.update_progress(task_id, None, f"发布地图图层... (0/{pub_total})", 91)
                from app.geoserver_service import geoserver
                for layer_type, file_path in all_exported.items():
                    try:
                        result = geoserver.publish_geotiff(
                            layer_name=f"b{boundary_id}_{layer_type}",
                            file_path=file_path,
                            title=f"{boundary_name} - {layer_type}",
                            layer_type=layer_type,
                        )
                        if result["success"]:
                            wms_urls[layer_type] = result["wms_url"]
                        else:
                            logger.warning(f"GeoServer publish failed for {layer_type}: {result.get('error')}")
                    except Exception as e:
                        logger.warning(f"GeoServer publish error for {layer_type}: {e}")
                    pub_idx += 1
                    pct = 91 + int((pub_idx / pub_total) * 4)
                    tasks.update_progress(task_id, None,
                        f"发布地图图层... ({pub_idx}/{pub_total})", pct)

                logger.info(f"Published {len(wms_urls)}/{pub_total} layers to GeoServer")
        except Exception as e:
            logger.warning(f"Raster export/publish failed (non-fatal): {e}", exc_info=True)
            # 导出失败不影响统计报告

        # 清理 yearly_results 中残留的 ee.Image 引用（不可序列化）
        for yr_data in yearly_results.values():
            yr_data.pop("_rsei_image", None)
            yr_data.pop("_images", None)

        # 生成报告
        tasks.update_progress(task_id, None, "生成报告...", 97)
        from app.report_service import generate_report

        ntl_missing = [y for y in years if 1984 <= y <= 1991]

        all_stats = {
            "yearly": yearly_results,
            "change": change_stats,
            "districts": district_stats,
            "years": years,
            "ntl_missing": ntl_missing,
        }

        report = generate_report(
            boundary_name=boundary_name,
            boundary_id=boundary_id,
            wms_urls=wms_urls,
            gee_stats=all_stats,
        )

        # 保存结果
        tasks.update_task(
            task_id,
            status="completed",
            report_data=report,
            wms_urls=wms_urls,
            progress_info={"year": None, "step": "完成", "percent": 100},
        )
        logger.info(f"Task {task_id} completed: {len(years)} years processed")

    def _compute_year_opt(self, boundary, geojson: dict, year: int,
                          indicators: list[str],
                          need_landsat: bool = True,
                          task_id: str = None, year_index: int = 0,
                          total_years: int = 1, cancel_event: Any = None) -> dict:
        """按用户选择的指标选择性计算单个年份。

        当 need_landsat=False 时跳过整个 Landsat 处理流程（节省大量时间）。
        """
        import ee

        def _progress(step_name: str, sub_ratio: float):
            if task_id is None:
                return
            if cancel_event and cancel_event.is_set():
                return
            base = int((year_index / total_years) * 70)
            end = int(((year_index + 1) / total_years) * 70)
            percent = base + int((end - base) * sub_ratio)
            tasks.update_progress(task_id, year, f"{year}年 · {step_name}", percent)

        # 默认值
        result = {
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
        images = {}
        rsei_image = None

        # ── Landsat 处理（仅 rsei 或 construction 需要时）──
        if need_landsat:
            _progress("构建影像合成", 0.0)
            collection_id, band_map, sensor = _get_landsat_source(year)
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
                rsei = self._compute_rsei(composite, boundary)
                rsei_stats = rsei.reduceRegion(
                    ee.Reducer.mean().combine(ee.Reducer.minMax(), "", True),
                    boundary, 500, maxPixels=1e12, bestEffort=True, tileScale=4,
                ).getInfo()
                logger.info(f"[{year}] rsei_stats={rsei_stats}")
                if rsei_stats:
                    result["rsei_mean"] = round(float(rsei_stats.get("RSEI_mean", 0)), 4)
                rsei_image = rsei
                images["rsei"] = rsei
                images["ndvi"] = ndvi
            else:
                _progress("跳过 RSEI（未选择）", 0.35)

            # 建设用地（仅选中时计算）
            if "construction" in indicators:
                _progress("计算建设用地...", 0.55)
                built_area, built_binary = self._compute_built_up(composite, band_map, boundary, year)
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
                result["population"] = self._get_population(boundary, year)
            logger.info(f"[{year}] population={result['population']}")
        else:
            _progress("跳过人口（未选择）", 0.60)

        # ── GDP（独立，依赖人口作为 fallback）──
        if "gdp" in indicators:
            _progress("提取 GDP 数据...", 0.75)
            gdp_pc_ppp, gdp_image = self._get_gdp_image_and_stats(boundary, year)

            gdp_total_ppp = None
            if gdp_image is not None and 2000 <= year <= 2020:
                gdp_total_ppp = self._compute_gdp_total(gdp_image, boundary, year)
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
            ntl_collection, ntl_ok = _get_ntl_source(year)
            result["ntl_available"] = ntl_ok
            if ntl_ok and ntl_collection:
                result["ntl_sum"] = self._get_ntl_sum(boundary, ntl_collection, year)
        else:
            _progress("跳过夜灯（未选择）", 0.90)

        _progress("完成", 1.0)
        logger.info(f"[{year}] DONE: rsei={result['rsei_mean']}, built={result['built_area_km2']}, "
                     f"pop={result['population']}, gdp={result['gdp_per_capita']}, ntl={result['ntl_sum']}")

        result["_rsei_image"] = rsei_image
        result["_images"] = images
        return result

    def _compute_change_partial(self, yearly_results: dict, years: list[int], indicators: list[str]) -> dict:
        """计算年际变化指标（部分指标模式）。仅计算已选指标的变化。"""
        first_year = years[0]
        last_year = years[-1]
        first = yearly_results.get(first_year, {})
        last = yearly_results.get(last_year, {})

        change = {
            "first_year": first_year,
            "last_year": last_year,
        }

        # 建设用地变化（仅 construction）
        if "construction" in indicators:
            built_first = first.get("built_area_km2", 0)
            built_last = last.get("built_area_km2", 0)
            change["new_built_area"] = round(built_last - built_first, 2)
            if built_first > 0 and last_year > first_year:
                cagr = ((built_last / built_first) ** (1 / (last_year - first_year)) - 1) * 100
                change["expansion_rate"] = round(cagr, 2)
            else:
                change["expansion_rate"] = 0.0
            change["built_first"] = built_first
            change["built_last"] = built_last
        else:
            change["new_built_area"] = 0
            change["expansion_rate"] = 0.0
            change["built_first"] = 0
            change["built_last"] = 0

        # RSEI 变化（仅 rsei）
        if "rsei" in indicators:
            rsei_first = first.get("rsei_mean", 0)
            rsei_last = last.get("rsei_mean", 0)
            change["rsei_change"] = round(rsei_last - rsei_first, 4)
        else:
            change["rsei_change"] = 0

        # 人口变化（仅 population）
        if "population" in indicators:
            pop_first = first.get("population", 0)
            pop_last = last.get("population", 0)
            change["pop_growth_rate"] = round(((pop_last / max(pop_first, 1)) - 1) * 100, 2) if pop_first > 0 else None
        else:
            change["pop_growth_rate"] = None

        # 夜灯变化（仅 nightLight）
        if "nightLight" in indicators:
            ntl_first = first.get("ntl_sum")
            ntl_last = last.get("ntl_sum")
            ntl_change = None
            if ntl_first and ntl_last and ntl_first > 0:
                ntl_change = round(((ntl_last / ntl_first) - 1) * 100, 2)
            change["ntl_change_rate"] = ntl_change
        else:
            change["ntl_change_rate"] = None

        return change

    def _compute_year(self, boundary, geojson: dict, year: int,
                      task_id: str = None, year_index: int = 0,
                      total_years: int = 1, cancel_event: Any = None) -> dict:
        """计算单个年份的所有指标。"""
        import ee

        def _progress(step_name: str, sub_ratio: float):
            """上报子步骤进度。sub_ratio 0.0~1.0 代表本年内的比例。"""
            if task_id is None:
                return
            if cancel_event and cancel_event.is_set():
                return
            base = int((year_index / total_years) * 70)
            end = int(((year_index + 1) / total_years) * 70)
            percent = base + int((end - base) * sub_ratio)
            tasks.update_progress(task_id, year, f"{year}年 · {step_name}", percent)

        collection_id, band_map, sensor = _get_landsat_source(year)
        wet_coeff = WET_COEFFICIENTS.get(sensor, WET_COEFFICIENTS["TM"])

        # 构建合成影像（时间窗口统一 ±3 年，确保影像数量充足）
        _progress("构建影像合成", 0.0)
        window = 3
        start_date = f"{year - window}-01-01"
        end_date = f"{year + window}-12-31"
        cloud_threshold = 50 if year <= 1995 else 40  # 放宽云阈值，保证可用影像

        collection = (
            ee.ImageCollection(collection_id)
            .filterBounds(boundary)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUD_COVER", cloud_threshold))
        )

        # 先查影像数量，确认 composite 非空
        img_count = collection.size().getInfo()
        logger.info(f"[{year}] 影像数量={img_count}, 集合={collection_id}, "
                    f"窗口={start_date}~{end_date}, 云阈值={cloud_threshold}")

        # 关键优化：先取 median 合成单张影像，再算指数
        # 旧写法 collection.map(calc_indices).median() 对每张影像都算指数 → 内存爆炸
        median = collection.median().clip(boundary)

        # Landsat C2 L2 缩放（必须先转成真实反射率/温度，否则 WET/NDVI 全错）
        #   反射率 = DN * 0.0000275 - 0.2
        #   热红外(K) = DN * 0.00341802 + 149.0
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

        # 指数统计（大区域用粗分辨率算均值，bestEffort 超限自动降采样）
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
        rsei = self._compute_rsei(composite, boundary)
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
        built_area, built_binary = self._compute_built_up(composite, band_map, boundary, year)
        logger.info(f"[{year}] built_area={built_area}")

        # 人口 (WorldPop 2000-2020)
        _progress("提取人口数据...", 0.60)
        population = 0
        if 2000 <= year <= 2020:
            population = self._get_population(boundary, year)
        logger.info(f"[{year}] population={population}")

        # GDP per capita (Kummu et al. 2025, 1km 网格, 1990-2022)
        _progress("提取 GDP 数据...", 0.75)
        gdp_pc_ppp, gdp_image = self._get_gdp_image_and_stats(boundary, year)

        # 总 GDP：优先用 GDP_pc × 人口栅格 → sum（考虑空间分布）
        # 回退到 mean(GDP_pc) × total_population（简单近似）
        gdp_total_ppp = None
        if gdp_image is not None and 2000 <= year <= 2020:
            gdp_total_ppp = self._compute_gdp_total(gdp_image, boundary, year)
        if gdp_total_ppp is None and gdp_pc_ppp and population > 0:
            gdp_total_ppp = round(gdp_pc_ppp * population, 0)

        # PPP 国际美元 → 人民币（世界银行 PPP 转换因子 ≈ 4.2）
        from app.config import GDP_USD_TO_RMB as _rate
        gdp_per_capita = round(gdp_pc_ppp * _rate) if gdp_pc_ppp else None
        gdp_total = round(gdp_total_ppp * _rate) if gdp_total_ppp else None
        logger.info(f"[{year}] gdp_pc={gdp_pc_ppp} PPP$ → {gdp_per_capita} RMB, "
                     f"gdp_total={gdp_total} RMB")

        # 夜灯
        _progress("提取夜灯数据...", 0.90)
        ntl_collection, ntl_ok = _get_ntl_source(year)
        ntl_sum = None
        if ntl_ok and ntl_collection:
            ntl_sum = self._get_ntl_sum(boundary, ntl_collection, year)

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
            "_rsei_image": rsei,  # ee.Image，供区县分析复用（不序列化）
            "_images": {          # ee.Image 引用集合，供栅格导出（不序列化）
                "rsei": rsei,
                "ndvi": ndvi,
                "built": built_binary,
                "gdp": gdp_image,   # Kummu GDP per capita, None if unavailable
            },
        }

    def _sum_built_area(self, built_binary, boundary, scale: int = 30) -> float:
        """Sum built_binary pixel area in km².

        built_binary must already be renamed to "built".
        """
        import ee
        pixel_area = ee.Image.pixelArea().divide(1e6)
        result = built_binary.multiply(pixel_area).reduceRegion(
            ee.Reducer.sum(), boundary, scale,
            maxPixels=1e12, bestEffort=True, tileScale=4,
        ).getInfo()
        if result:
            val = result.get("built")
            if val is not None:
                return round(float(val), 2)
        return 0.0

    def _sum_built_surface_area(self, built_surface, boundary, scale: int = 100) -> float:
        """Sum GHSL built_surface values in km².

        GHSL GHS_BUILT_S stores built-up surface area in m² per 100 m cell.
        """
        import ee

        result = built_surface.reduceRegion(
            ee.Reducer.sum(), boundary, scale,
            maxPixels=1e12, bestEffort=True, tileScale=4,
        ).getInfo()
        if result:
            val = result.get("built_surface")
            if val is not None:
                return round(float(val) / 1e6, 2)
        return 0.0

    def _get_ghsl_built(self, boundary, year: int):
        """GHSL built-up surface time series → (area_km2, binary_mask, ghsl_year)."""
        import ee

        ghsl_year = min(BUILT_GHSL_YEARS, key=lambda item: abs(item - year))
        image = (
            ee.ImageCollection(BUILT_GHSL_COLLECTION)
            .filter(ee.Filter.eq("system:index", str(ghsl_year)))
            .first()
            .select("built_surface")
        )
        area = self._sum_built_surface_area(image, boundary, scale=100)
        built_binary = (
            image.gt(BUILT_GHSL_MIN_SURFACE_M2)
            .unmask(0)
            .toByte()
            .rename("built")
            .reproject("EPSG:4326", None, 100)
        )
        return area, built_binary, ghsl_year

    def _get_dynamic_world_built(self, boundary, year: int):
        """Dynamic World built probability median ≥ threshold → binary mask.

        Returns ee.Image renamed "built", or None if no data for this year.
        """
        import ee
        dw_col = (
            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
            .filterBounds(boundary)
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .select("built")
        )
        count = dw_col.size().getInfo()
        if count == 0:
            logger.info(f"Dynamic World: no data for year={year}")
            return None
        dw_median = dw_col.median()
        return dw_median.gte(BUILT_DW_PROB_MIN).unmask(0).toByte().rename("built")

    def _compute_built_up(self, composite, band_map, boundary, year: int) -> tuple[float, Any]:
        """计算建设用地面积。三源竞争选优：WorldCover / Dynamic World / NDBI。

        所有候选源都计算，按优先级选最佳。
        如果高优先级结果异常偏低（< 次优先级 30%），降级。

        Returns:
            (built_area_km2, built_binary_eeImage) 二元组。
        """
        import ee

        candidates = []  # [(source_name, area_km2, built_binary_eeImage)]

        # ── Source 1: GHSL built-up surface (100m, 5-year time series) ──
        try:
            ghsl_area, ghsl_built, ghsl_year = self._get_ghsl_built(boundary, year)
            candidates.append(("GHSL", ghsl_area, ghsl_built))
            logger.info(f"GHSL built source year={ghsl_year} requested={year} area={ghsl_area}km²")
        except Exception as e:
            logger.warning(f"GHSL built-up failed for {year}: {e}")

        # ── Source 2: ESA WorldCover (10m, class 50) — 仅 2020 ──
        if year == 2020:
            try:
                wc = ee.Image("ESA/WorldCover/v100/2020")
                wc_built = wc.eq(50).unmask(0).toByte().rename("built")
                wc_area = self._sum_built_area(wc_built, boundary, scale=30)
                candidates.append(("WorldCover", wc_area, wc_built))
            except Exception as e:
                logger.warning(f"WorldCover failed for {year}: {e}")

        # ── Source 3: Dynamic World (10m, built probability) — 动态检查可用性 ──
        try:
            dw_built = self._get_dynamic_world_built(boundary, year)
            if dw_built is not None:
                dw_area = self._sum_built_area(dw_built, boundary, scale=30)
                candidates.append(("DynamicWorld", dw_area, dw_built))
        except Exception as e:
            logger.warning(f"Dynamic World failed for {year}: {e}")

        # ── Source 4: NDBI + NDVI + MNDWI (Landsat 30m) — 始终计算 ──
        try:
            ndbsi = composite.select("NDBSI")
            ndvi_band = composite.select("NDVI")
            green = composite.select(band_map["green"]).multiply(0.0000275).add(-0.2)
            swir1 = composite.select(band_map["swir1"]).multiply(0.0000275).add(-0.2)
            mndwi = green.subtract(swir1).divide(green.add(swir1)).rename("MNDWI")
            ndbi_built = (
                ndbsi.gt(BUILT_NDBSI_MIN)
                .And(ndvi_band.lt(BUILT_NDVI_MAX))
                .And(mndwi.lt(BUILT_MNDWI_MAX))
            ).unmask(0).toByte().rename("built")
            ndbi_area = self._sum_built_area(ndbi_built, boundary, scale=30)
            candidates.append(("NDBI", ndbi_area, ndbi_built))
        except Exception as e:
            logger.warning(f"NDBI built-up failed for {year}: {e}")

        # ── 选最优结果 ──
        # 优先级: GHSL > WorldCover > DynamicWorld > NDBI
        # GHSL 是跨年度一致时间序列，不因 NDBI 偏大而降级。
        priority_order = ["GHSL", "WorldCover", "DynamicWorld", "NDBI"]
        if not candidates:
            logger.warning(f"built-up: all sources failed for year={year}")
            return 0.0, None

        ordered = sorted(candidates, key=lambda item: priority_order.index(item[0]))
        nonzero = [item for item in ordered if item[1] > 0]
        best = nonzero[0] if nonzero else ordered[0]

        # 非 GHSL 高优先级数据源面积异常偏低时，向低优先级但更完整的候选降级。
        if best[0] != "GHSL":
            for src_name, area, binary in (nonzero[1:] if nonzero else ordered[1:]):
                if best[1] > 0 and area > 0 and best[1] < area * 0.3:
                    logger.warning(
                        f"built-up: {best[0]} area={best[1]} suspiciously low vs "
                        f"{src_name} area={area}, using {src_name}"
                    )
                    best = (src_name, area, binary)

        src_name, area, binary = best
        logger.info(
            f"built-up: source={src_name} year={year} area={area}km² "
            f"(candidates: {[(c[0], c[1]) for c in candidates]})"
        )
        return area, binary

    def _get_population(self, boundary, year: int) -> int:
        """WorldPop 人口估算。"""
        import ee

        try:
            pop = (
                ee.ImageCollection("WorldPop/GP/100m/pop")
                .filterBounds(boundary)
                .filter(ee.Filter.eq("year", year))
                .first()
            )
            if pop:
                pop_result = pop.reduceRegion(
                    ee.Reducer.sum(), boundary, 100, maxPixels=1e12,
                    bestEffort=True, tileScale=4,
                ).getInfo()
                if pop_result:
                    vals = list(pop_result.values())
                    if vals and vals[0] is not None:
                        return round(float(vals[0]))
        except Exception as e:
            logger.warning(f"Population failed for {year}: {e}")
        return 0

    def _get_gdp_image_and_stats(
        self, boundary, year: int,
    ) -> tuple[float | None, Any]:
        """从 Kummu et al. (2025) 1km 网格数据集提取区域人均 GDP。

        Returns:
            (gdp_per_capita_mean, gdp_ee_image) 二元组。
            gdp_ee_image 为 ee.Image (renamed "GDP") 或 None。
        """
        import ee

        band_name = _get_gdp_band(year)
        if not band_name:
            return None, None

        try:
            gdp_img = ee.Image(
                "projects/sat-io/open-datasets/GRIDDED_HDI_GDP/"
                "adm2_gdp_perCapita_1990_2022"
            )
            gdp_band = gdp_img.select(band_name).clip(boundary)

            stats = gdp_band.reduceRegion(
                ee.Reducer.mean(),
                boundary,
                1000,
                maxPixels=1e12,
                bestEffort=True,
                tileScale=4,
            ).getInfo()

            if stats and stats.get(band_name) is not None:
                value = float(stats[band_name])
                if value > 0:
                    return round(value, 1), gdp_band.rename("GDP")
        except Exception as e:
            logger.warning(f"GDP per capita extraction failed for {year}: {e}")
        return None, None

    def _compute_gdp_total(
        self,
        gdp_image,   # ee.Image (GDP per capita, renamed "GDP")
        boundary,    # ee.Geometry
        year: int,
    ) -> float | None:
        """栅格相乘法计算总 GDP：GDP per capita × 人口栅格 → sum。

        比 mean(GDP_pc) × total_population 更准确，
        因为它考虑了 GDP 和人口的空间分布相关性。
        仅在 WorldPop 有数据的年份（2000-2020）可用。

        Returns:
            总 GDP（PPP 国际美元）或 None。
        """
        import ee
        try:
            pop = (
                ee.ImageCollection("WorldPop/GP/100m/pop")
                .filterBounds(boundary)
                .filter(ee.Filter.eq("year", year))
                .first()
            )
            gdp_total_img = gdp_image.multiply(pop)
            result = gdp_total_img.reduceRegion(
                ee.Reducer.sum(), boundary, 100,
                maxPixels=1e12, bestEffort=True, tileScale=4,
            ).getInfo()
            if result:
                vals = list(result.values())
                if vals and vals[0] is not None:
                    return round(float(vals[0]))
        except Exception as e:
            logger.warning(f"GDP total (raster multiply) failed for {year}: {e}")
        return None

    def _get_gdp_per_capita(self, boundary, year: int) -> float | None:
        """只返回 GDP 统计值的便捷方法（区县分析等场景）。"""
        value, _ = self._get_gdp_image_and_stats(boundary, year)
        return value

    def _get_ntl_sum(self, boundary, ntl_collection: str, year: int) -> float | None:
        """获取夜灯总亮度。用 ImageCollection + filterDate 取该年份影像。"""
        import ee

        try:
            ntl_img = (
                ee.ImageCollection(ntl_collection)
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .first()
            )
            if ntl_img is None:
                logger.warning(f"NTL: no image in {ntl_collection} for {year}")
                return None
            ntl_result = ntl_img.select([0]).reduceRegion(
                ee.Reducer.sum(), boundary, 1000, maxPixels=1e12,
                bestEffort=True, tileScale=4,
            ).getInfo()
            if ntl_result:
                vals = list(ntl_result.values())
                if vals and vals[0] is not None:
                    return round(float(vals[0]), 2)
        except Exception as e:
            logger.warning(f"NTL failed for {ntl_collection} ({year}): {e}")
        return None

    def _compute_rsei(self, composite, boundary):
        """简化版 RSEI：NDVI + Wet + (1-NDBSI) + (1-LST) 加权。"""
        import ee

        def _norm(img, band):
            s = img.select(band).reduceRegion(
                ee.Reducer.minMax(), boundary, 500, maxPixels=1e12,
                bestEffort=True, tileScale=4,
            )
            return img.select(band).subtract(ee.Number(s.get(band + "_min"))).divide(
                ee.Number(s.get(band + "_max")).subtract(ee.Number(s.get(band + "_min")))
            )

        ndvi_n = _norm(composite, "NDVI").rename("NDVI_n")
        wet_n = _norm(composite, "WET").rename("WET_n")
        ndbsi_n = ee.Image(1).subtract(_norm(composite, "NDBSI")).rename("NDBSI_n")
        lst_n = ee.Image(1).subtract(_norm(composite, "LST")).rename("LST_n")

        rsei = (
            ndvi_n.multiply(0.4)
            .add(wet_n.multiply(0.3))
            .add(ndbsi_n.multiply(0.2))
            .add(lst_n.multiply(0.1))
            .rename("RSEI")
        )
        return rsei

    def _compute_change(self, yearly_results: dict, years: list[int]) -> dict:
        """计算年际变化指标。"""
        first_year = years[0]
        last_year = years[-1]
        first = yearly_results.get(first_year, {})
        last = yearly_results.get(last_year, {})

        # 建设用地变化
        built_first = first.get("built_area_km2", 0)
        built_last = last.get("built_area_km2", 0)
        new_built = round(built_last - built_first, 2)

        # 年均扩张速率（复合增长率）
        if built_first > 0 and last_year > first_year:
            cagr = ((built_last / built_first) ** (1 / (last_year - first_year)) - 1) * 100
            expansion_rate = round(cagr, 2)
        else:
            expansion_rate = 0.0

        # RSEI 变化
        rsei_first = first.get("rsei_mean", 0)
        rsei_last = last.get("rsei_mean", 0)
        rsei_change = round(rsei_last - rsei_first, 4)

        # 人口变化
        pop_first = first.get("population", 0)
        pop_last = last.get("population", 0)
        pop_growth = round(((pop_last / max(pop_first, 1)) - 1) * 100, 2) if pop_first > 0 else None

        # 夜灯变化
        ntl_first = first.get("ntl_sum")
        ntl_last = last.get("ntl_sum")
        ntl_change = None
        if ntl_first and ntl_last and ntl_first > 0:
            ntl_change = round(((ntl_last / ntl_first) - 1) * 100, 2)

        return {
            "first_year": first_year,
            "last_year": last_year,
            "new_built_area": new_built,
            "expansion_rate": expansion_rate,
            "rsei_change": rsei_change,
            "pop_growth_rate": pop_growth,
            "ntl_change_rate": ntl_change,
            "built_first": built_first,
            "built_last": built_last,
        }

    def _compute_district_stats(
        self, boundary, geojson: dict, yearly_results: dict, years: list[int],
        rsei_image=None, built_image=None, indicators: list[str] | None = None,
    ) -> list[dict]:
        """子区域（区县）分析。

        优先使用自定义县级区划 Asset（含中文名），
        若 Asset 不存在则回退到 FAO/GAUL/2015/level2（地级市粒度）。

        Args:
            rsei_image: 末年已算好的 RSEI ee.Image，用于逐区县 clip 求均值。
            built_image: 末年已算好的 built_binary ee.Image，用于逐区县 clip 求面积。
                         为 None 时区县建设用地为 0。
            indicators: 用户选择的指标列表。None 表示全选（向后兼容）。
        """
        import ee

        from app.config import COUNTY_ASSET_ID

        if not indicators:
            indicators = ["rsei", "construction", "expansion", "nightLight", "population", "gdp"]

        districts = []
        last_year = years[-1]
        last_data = yearly_results.get(last_year, {})

        try:
            # ── 尝试使用自定义县级 Asset ──
            county_fc = None
            use_county_asset = False
            try:
                county_fc = ee.FeatureCollection(COUNTY_ASSET_ID)
                # 用 size() 验证 Asset 存在且非空
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
            min_overlap_ratio = 0.03  # 至少 3% 面积在研究区内

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

            for feat in district_features["features"][:30]:  # 最多30个区县
                props = feat.get("properties", {})

                # ── 区县名称：优先用中文名字段 ──
                name = ""
                if use_county_asset:
                    # 自定义 Asset 直接有中文名
                    name = (
                        props.get("name")
                        or props.get("NAME")
                        or props.get("name_CHN")
                        or ""
                    )
                if not name:
                    # GAUL 回退路径
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
                    # 区县建设用地：clip 主 built_binary（仅 construction 选中时）
                    built_km2 = 0.0
                    if "construction" in indicators and built_image is not None:
                        try:
                            built_district = built_image.clip(analysis_geom)
                            built_km2 = self._sum_built_area(built_district, analysis_geom, scale=30)
                        except Exception as e:
                            logger.warning(f"District {name} built clip failed: {e}")

                    # 区县 RSEI：clip 全局 RSEI 影像 + 求均值（仅 rsei 选中时）
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

                    # 区县 GDP per capita（仅 gdp 选中时，PPP → 人民币）
                    d_gdp_pc = None
                    if "gdp" in indicators:
                        d_gdp_pc_ppp = self._get_gdp_per_capita(analysis_geom, last_year)
                        from app.config import GDP_USD_TO_RMB as _rate2
                        d_gdp_pc = round(d_gdp_pc_ppp * _rate2) if d_gdp_pc_ppp else None

                    # 区县人口（仅 population 选中时）
                    d_pop = 0
                    if "population" in indicators:
                        d_pop = self._district_population(analysis_geom, last_year)

                    # 区县夜灯（仅 nightLight 选中时）
                    d_ntl = 0.0
                    if "nightLight" in indicators:
                        d_ntl = self._district_ntl(analysis_geom, last_year)

                    districts.append({
                        "name": name,
                        "built_area_km2": built_km2,
                        "rsei_mean": rsei_mean,
                        "population": d_pop,
                        "ntl_sum": d_ntl,
                        "gdp_per_capita": d_gdp_pc,
                        "gdp_total": None,  # filled below
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

    def _district_population(self, district_geom, year: int) -> int:
        """WorldPop 人口栅格按区县求和。"""
        import ee
        if not (2000 <= year <= 2020):
            return 0
        try:
            wp = ee.ImageCollection("WorldPop/GP/100m/pop")\
                .filter(ee.Filter.eq("year", year)).first()
            result = wp.reduceRegion(
                ee.Reducer.sum(), district_geom, 100,
                maxPixels=1e12, bestEffort=True, tileScale=4,
            ).getInfo()
            if result:
                vals = list(result.values())
                if vals and vals[0] is not None:
                    return round(float(vals[0]))
        except Exception as e:
            logger.warning(f"District population failed: {e}")
        return 0

    def _district_ntl(self, district_geom, year: int) -> float:
        """夜灯 NTL 按区县求和（GDP 代理指标）。"""
        import ee
        ntl_id, ntl_ok = _get_ntl_source(year)
        if not ntl_ok or not ntl_id:
            return 0.0
        try:
            ntl_img = (
                ee.ImageCollection(ntl_id)
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .first()
            )
            result = ntl_img.select([0]).reduceRegion(
                ee.Reducer.sum(), district_geom, 500,
                maxPixels=1e12, bestEffort=True, tileScale=4,
            ).getInfo()
            if result:
                vals = list(result.values())
                if vals and vals[0] is not None:
                    return round(float(vals[0]), 1)
        except Exception as e:
            logger.warning(f"District NTL failed: {e}")
        return 0.0

    # ──────────────────────────────────────────────
    # 栅格导出方法
    # ──────────────────────────────────────────────

    def _export_rasters(
        self,
        boundary,          # ee.Geometry
        boundary_id: int,
        year: int | None,  # None 表示多年份变化图（如 new_built）
        images: dict,      # {"rsei": ee.Image, "ndvi": ee.Image, "built": ee.Image}
        scale: int = 30,   # Landsat 分辨率（米）
        area_km2: float | None = None,  # 上传时预计算的面积
        progress_cb: Any = None,  # 每导出一个栅格后回调
        raster_idx: list[int] | None = None,  # mutable counter for progress
    ) -> dict[str, str]:   # {"rsei_2020": "/path/to/rsei_2020.tif", ...}
        """导出栅格为 GeoTIFF 文件。

        使用 ee.Image.getDownloadURL(format='GEO_TIFF') 同步下载。
        根据预计算的边界面积自动选择合适的 scale，避免反复重试。

        Args:
            boundary: ee.Geometry 边界
            boundary_id: 边界 ID（用于目录命名）
            year: 年份，None 表示变化图
            images: {layer_key: ee.Image} dict
            scale: 默认导出分辨率（米），仅小区域使用
            area_km2: 上传时预计算的边界面积（km²）

        Returns:
            {layer_type: file_path} dict。失败的图层不包含在返回值中。
        """
        import ee
        import requests
        import math
        from pathlib import Path
        from app.config import RESULTS_DIR

        # 创建输出目录
        out_dir = Path(RESULTS_DIR) / f"b{boundary_id}"
        out_dir.mkdir(parents=True, exist_ok=True)

        # ── 根据面积计算最优 scale ──
        # GEE getDownloadURL 上限约 48 MB。
        # 公式：scale = ceil(sqrt(area_m2 / max_pixels))
        # max_pixels = safe_bytes / bytes_per_pixel = 35e6 / 4 ≈ 8.75e6
        if area_km2 and area_km2 > 0:
            area_m2 = area_km2 * 1e6
        else:
            # fallback: 通过 GEE API 计算
            try:
                area_m2 = boundary.area(maxError=1).getInfo()
            except Exception:
                area_m2 = 1000 * 1e6  # fallback 1000 km²
            area_km2 = area_m2 / 1e6

        SAFE_BYTES = 35_000_000
        BYTES_PER_PIXEL = 4
        max_pixels = SAFE_BYTES // BYTES_PER_PIXEL

        # 直接算出保证不超限的 scale（考虑波段数）
        band_count = max(img.bandNames().length().getInfo() for img in images.values() if img is not None) if images else 1
        if band_count <= 0:
            band_count = 1
        effective_max_pixels = max_pixels // band_count
        opt_scale = max(scale, int(math.ceil(math.sqrt(area_m2 / effective_max_pixels) / 10) * 10))
        opt_scale = min(opt_scale, 2000)  # 不超过 2km

        logger.info(f"Export scale chosen: {opt_scale}m for area={area_km2:.0f}km² (bands={band_count})")

        # ── 某些数据源分辨率远低于 Landsat 30m，强制最低导出分辨率避免浪费 ──
        LAYER_MIN_SCALES: dict[str, int] = {
            "built": 100,      # GHSL 100m 栅格
            "new_built": 100,  # 变化图通常由 built 二值图计算
            "gdp": 500,        # Kummu 1km 栅格
            "population": 200, # WorldPop 100m 栅格
        }

        exported: dict[str, str] = {}

        for layer_key, img in images.items():
            if img is None:
                logger.warning(f"Skip export: {layer_key} image is None")
                continue

            # 构建图层名：rsei_2020, built_2010, new_built 等
            if year is not None:
                layer_name = f"{layer_key}_{year}"
            else:
                layer_name = layer_key

            file_path = out_dir / f"{layer_name}.tif"

            # 对低分辨率数据源，提高最低导出 scale
            layer_min = LAYER_MIN_SCALES.get(layer_key, scale)
            effective_opt = max(opt_scale, layer_min)

            # clip + unmask(-9999)：确保边界外像素为明确 sentinel 值，
            # 而非依赖 GeoTIFF mask 编码（部分 GEE 版本 getDownloadURL 不会写 NoData）
            img_clipped = img.clip(boundary).unmask(-9999)

            # 尝试序列：effective_opt → 2x → 4x → 1km → 2km
            scales_to_try = list(dict.fromkeys([
                effective_opt, effective_opt * 2, effective_opt * 4, 1000, 2000,
            ]))

            for try_scale in scales_to_try:
                try:
                    url = img_clipped.getDownloadURL({
                        "scale": try_scale,
                        "region": boundary,
                        "format": "GEO_TIFF",
                        "name": layer_name,
                    })

                    logger.info(f"Exporting {layer_name} at {try_scale}m...")
                    resp = requests.get(url, timeout=300)
                    if resp.status_code == 200:
                        with open(file_path, "wb") as f:
                            f.write(resp.content)
                        exported[layer_name] = str(file_path)
                        logger.info(f"Exported: {file_path} ({len(resp.content)} bytes, {try_scale}m)")
                        if raster_idx is not None:
                            raster_idx[0] += 1
                        if progress_cb:
                            progress_cb()
                        break
                    else:
                        if try_scale < scales_to_try[-1]:
                            logger.warning(f"Export {layer_name} at {try_scale}m got HTTP {resp.status_code}, retrying...")
                            continue
                        else:
                            logger.warning(f"Export {layer_name} failed: HTTP {resp.status_code}")
                            break

                except Exception as e:
                    if try_scale < scales_to_try[-1]:
                        logger.warning(f"Export {layer_name} at {try_scale}m error: {e}, retrying...")
                        continue
                    else:
                        logger.warning(f"Export {layer_name} failed: {e}")
                        break

            # 失败也推进进度，避免卡住
            if layer_key not in exported:
                if raster_idx is not None:
                    raster_idx[0] += 1
                if progress_cb:
                    progress_cb()

        return exported

    def _compute_new_built(
        self,
        first_built,   # ee.Image (0/1), 首年份建设用地
        last_built,    # ee.Image (0/1), 末年份建设用地
        boundary,      # ee.Geometry
    ) -> Any:         # ee.Image (0/1)
        """计算新增建设用地：末年份是建设用地且首年份不是。

        Returns:
            ee.Image (0/1 二值)，或 None（输入无效时）。
        """
        import ee

        if first_built is None or last_built is None:
            return None

        try:
            # new_built = last_built AND (NOT first_built)
            new_built = last_built.And(first_built.Not()).unmask(0).toByte().rename("built")
            return new_built.clip(boundary)
        except Exception as e:
            logger.warning(f"Compute new_built failed: {e}")
            return None

    def _run_single_year(self, geojson: dict, boundary_id: int, year: int) -> dict:
        """兼容旧接口：单年同步计算。"""
        import ee

        try:
            boundary = ee.Geometry(geojson)
            result = self._compute_year(boundary, geojson, year)

            stats = {
                "ndvi": {"NDVI_mean": result["ndvi_mean"]},
                "rsei": {"RSEI_mean": result["rsei_mean"]},
                "lst": {"LST_mean": result["lst_mean"]},
                "built_area_km2": result["built_area_km2"],
                "population": result["population"],
            }

            return {
                "success": True,
                "gee_tasks": [],
                "error": None,
                "stats": stats,
                "sync_mode": True,
            }
        except Exception as e:
            logger.error(f"Single year computation failed: {e}")
            return {"success": False, "gee_tasks": [], "error": str(e)}

    def check_all_tasks(self, gee_tasks: list[dict]) -> dict:
        """同步模式下无需检查，直接返回完成。"""
        return {"all_completed": True, "completed": 0, "total": 0, "details": []}

    def download_results(self, boundary_id: int, task_id: str, gee_tasks: list) -> dict:
        """同步模式不下载。"""
        return {}

    def get_user_quota(self, user_token: str) -> dict | None:
        """查询用户自有 GEE 密钥的配额信息。

        GEE 没有公开的配额查询 API，这里返回密钥状态和基于当前任务数的估算。
        """
        from app.gee_key_service import gee_key_service

        user_key = gee_key_service.get_valid_key(user_token)
        if user_key is None:
            return None

        # 查当前该用户的 processing 任务数
        with get_db_context() as db:
            processing_count = db.query(UserBoundary).filter(
                UserBoundary.status == "processing",
            ).count()

        return {
            "status": "active",
            "concurrent_tasks": processing_count,
            "max_concurrent": MAX_CONCURRENT_GEE_TASKS,
            "remaining_slots": max(0, MAX_CONCURRENT_GEE_TASKS - processing_count),
            "daily_limit": None,  # 用户自有密钥无日限
            "note": "用户自有密钥，受 GEE 项目配额约束",
        }

    def get_public_quota(self) -> dict:
        """查询公共账号的配额估算。

        GEE 没有公开的配额查询 API，返回基于配置的估算值。
        """
        with get_db_context() as db:
            processing_count = db.query(UserBoundary).filter(
                UserBoundary.status == "processing",
                UserBoundary.compute_mode == "online",
            ).count()

        return {
            "status": "active",
            "concurrent_tasks": processing_count,
            "max_concurrent": MAX_CONCURRENT_GEE_TASKS,
            "remaining_slots": max(0, MAX_CONCURRENT_GEE_TASKS - processing_count),
            "daily_limit": PUBLIC_ACCOUNT_DAILY_LIMIT,
        }


gee_online = GEEOnlineService()
