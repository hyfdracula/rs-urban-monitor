"""
GEE 在线计算服务
================
公开 API 层：认证、任务提交、状态查询、配额管理。

核心计算逻辑已拆分到子模块：
- app.gee.computation     — 年度指标计算
- app.gee.district_analysis — 区县统计
- app.gee.export          — 栅格导出
- app.gee.orchestration   — 多年度编排
- app.gee.data_sources    — Landsat/夜灯数据源选择
- app.gee.built           — 建设用地计算
- app.gee.change          — 变化分析
- app.gee.indices         — RSEI 指数
- app.gee.socio           — 人口/GDP/夜灯
"""

from __future__ import annotations

import logging
import os
import tempfile

from typing import Any

from app import tasks
from app.database import get_db_context
from app.models import UserBoundary
from app.config import MAX_CONCURRENT_GEE_TASKS, PUBLIC_ACCOUNT_DAILY_LIMIT
from app.gee.computation import compute_year_full
from app.gee.orchestration import run_multi_year

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
        if not indicators:
            indicators = ["rsei", "construction", "expansion", "nightLight", "population", "gdp"]

        service_account, key_json = user_key
        temp_key_path = self._init_with_key_json(key_json, service_account)
        if temp_key_path is None:
            tasks.update_task(task_id, status="failed",
                              progress_info={"year": None, "step": "GEE 初始化失败", "percent": 0})
            return

        try:
            run_multi_year(geojson, boundary_id, task_id, years, cancel_event, indicators)
        finally:
            try:
                os.unlink(temp_key_path)
            except Exception:
                pass

    # ─── 单年度同步计算（兼容旧接口）───

    def _run_single_year(self, geojson: dict, boundary_id: int, year: int) -> dict:
        """兼容旧接口：单年同步计算。"""
        import ee

        try:
            boundary = ee.Geometry(geojson)
            result = compute_year_full(boundary, geojson, year)

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

    # ─── 任务状态查询（兼容旧接口）───

    def check_all_tasks(self, gee_tasks: list[dict]) -> dict:
        """同步模式下无需检查，直接返回完成。"""
        return {"all_completed": True, "completed": 0, "total": 0, "details": []}

    def download_results(self, boundary_id: int, task_id: str, gee_tasks: list) -> dict:
        """同步模式不下载。"""
        return {}

    # ─── 配额管理 ───

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
