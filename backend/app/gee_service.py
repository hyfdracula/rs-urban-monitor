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
from app.gee.built import (
    compute_built_up as _compute_built_up_impl,
    compute_new_built as _compute_new_built_impl,
    sum_built_area as _sum_built_area_impl,
)
from app.gee.change import (
    compute_change as _compute_change_impl,
    compute_change_partial as _compute_change_partial_impl,
)
from app.gee.data_sources import (
    WET_COEFFICIENTS,
    get_landsat_source as _get_landsat_source,
    get_ntl_source as _get_ntl_source,
)
from app.gee.indices import compute_rsei as _compute_rsei_impl
from app.gee.socio import (
    compute_gdp_total as _compute_gdp_total_impl,
    district_ntl as _district_ntl_impl,
    district_population as _district_population_impl,
    get_gdp_image_and_stats as _get_gdp_image_and_stats_impl,
    get_gdp_per_capita as _get_gdp_per_capita_impl,
    get_ntl_sum as _get_ntl_sum_impl,
    get_population as _get_population_impl,
)

logger = logging.getLogger("ueea2601.gee")


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
            change_stats = _compute_change_impl(yearly_results, years)
        elif len(years) >= 2:
            # 非 construction 模式，仍然计算非建设用地的变化指标
            change_stats = _compute_change_partial_impl(yearly_results, years, indicators)
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
                new_built_img = _compute_new_built_impl(
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
                rsei = _compute_rsei_impl(composite, boundary)
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
                built_area, built_binary = _compute_built_up_impl(composite, band_map, boundary, year)
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
                result["population"] = _get_population_impl(boundary, year)
            logger.info(f"[{year}] population={result['population']}")
        else:
            _progress("跳过人口（未选择）", 0.60)

        # ── GDP（独立，依赖人口作为 fallback）──
        if "gdp" in indicators:
            _progress("提取 GDP 数据...", 0.75)
            gdp_pc_ppp, gdp_image = _get_gdp_image_and_stats_impl(boundary, year)

            gdp_total_ppp = None
            if gdp_image is not None and 2000 <= year <= 2020:
                gdp_total_ppp = _compute_gdp_total_impl(gdp_image, boundary, year)
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
                result["ntl_sum"] = _get_ntl_sum_impl(boundary, ntl_collection, year)
        else:
            _progress("跳过夜灯（未选择）", 0.90)

        _progress("完成", 1.0)
        logger.info(f"[{year}] DONE: rsei={result['rsei_mean']}, built={result['built_area_km2']}, "
                     f"pop={result['population']}, gdp={result['gdp_per_capita']}, ntl={result['ntl_sum']}")

        result["_rsei_image"] = rsei_image
        result["_images"] = images
        return result

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
        rsei = _compute_rsei_impl(composite, boundary)
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
        built_area, built_binary = _compute_built_up_impl(composite, band_map, boundary, year)
        logger.info(f"[{year}] built_area={built_area}")

        # 人口 (WorldPop 2000-2020)
        _progress("提取人口数据...", 0.60)
        population = 0
        if 2000 <= year <= 2020:
            population = _get_population_impl(boundary, year)
        logger.info(f"[{year}] population={population}")

        # GDP per capita (Kummu et al. 2025, 1km 网格, 1990-2022)
        _progress("提取 GDP 数据...", 0.75)
        gdp_pc_ppp, gdp_image = _get_gdp_image_and_stats_impl(boundary, year)

        # 总 GDP：优先用 GDP_pc × 人口栅格 → sum（考虑空间分布）
        # 回退到 mean(GDP_pc) × total_population（简单近似）
        gdp_total_ppp = None
        if gdp_image is not None and 2000 <= year <= 2020:
            gdp_total_ppp = _compute_gdp_total_impl(gdp_image, boundary, year)
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
            ntl_sum = _get_ntl_sum_impl(boundary, ntl_collection, year)

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
                            built_km2 = _sum_built_area_impl(built_district, analysis_geom, scale=30)
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
                        d_gdp_pc_ppp = _get_gdp_per_capita_impl(analysis_geom, last_year)
                        from app.config import GDP_USD_TO_RMB as _rate2
                        d_gdp_pc = round(d_gdp_pc_ppp * _rate2) if d_gdp_pc_ppp else None

                    # 区县人口（仅 population 选中时）
                    d_pop = 0
                    if "population" in indicators:
                        d_pop = _district_population_impl(analysis_geom, last_year)

                    # 区县夜灯（仅 nightLight 选中时）
                    d_ntl = 0.0
                    if "nightLight" in indicators:
                        d_ntl = _district_ntl_impl(analysis_geom, last_year)

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
