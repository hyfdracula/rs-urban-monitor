"""
多年编排
=========
从 gee_service.py 拆出的纯函数，负责多年 GEE 计算的完整编排流程。

流程：逐年计算 → 变化分析 → 区县分析 → 栅格导出 → GeoServer 发布 → 报告生成
"""

from __future__ import annotations

import logging
from typing import Any

from app import tasks
from app.database import get_db_context
from app.models import UserBoundary
from app.gee.built import compute_new_built
from app.gee.change import compute_change, compute_change_partial
from app.gee.computation import compute_year_optimal
from app.gee.district_analysis import compute_district_stats
from app.gee.export import export_rasters

logger = logging.getLogger("ueea2601.gee.orchestration")


def run_multi_year(
    geojson: dict,
    boundary_id: int,
    task_id: str,
    years: list[int],
    cancel_event: Any,
    indicators: list[str],
) -> None:
    """多年度 GEE 计算，逐年遍历。按 indicators 选择性计算。

    Args:
        geojson: 边界 GeoJSON
        boundary_id: 边界 ID
        task_id: 任务 ID（用于进度更新）
        years: 年份列表
        cancel_event: 取消事件
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
            result = compute_year_optimal(
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
        change_stats = compute_change(yearly_results, years)
    elif len(years) >= 2:
        # 非 construction 模式，仍然计算非建设用地的变化指标
        change_stats = compute_change_partial(yearly_results, years, indicators)
    else:
        change_stats = {"single_year": True}

    # 区县分析（按指标选择性调用）
    tasks.update_progress(task_id, None, "子区域分析...", 77)
    last_year = years[-1]
    built_image = yearly_results.get(last_year, {}).get("_images", {}).get("built") if "construction" in indicators else None
    district_stats = compute_district_stats(
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
    wms_urls: dict[str, str] = {}
    try:
        # 收集每年的 ee.Image 引用（在 pop 掉之前）
        yearly_images: dict[int | str, dict] = {}
        for y in years:
            yr_data = yearly_results.get(y, {})
            yearly_images[y] = yr_data.get("_images", {})

        # 多年份：计算并导出 new_built
        if len(years) >= 2:
            first_imgs = yearly_images.get(years[0], {})
            last_imgs = yearly_images.get(years[-1], {})
            new_built_img = compute_new_built(
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
                exported = export_rasters(
                    boundary, boundary_id, y, imgs,
                    area_km2=boundary_area_km2,
                    progress_cb=_export_progress,
                    raster_idx=raster_idx,
                )
                all_exported.update(exported)

        # 导出变化图
        if change_imgs_dict:
            exported = export_rasters(
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
