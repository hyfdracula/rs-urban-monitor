"""
计算相关路由
=========
自动模式：
  GET /api/compute/{task_id}/status  - 轮询进度
  GET /api/compute/{task_id}/report  - 获取分析报告

手动模式：
  GET /api/compute/{task_id}/code    - 获取 GEE 代码
"""

from __future__ import annotations

import json
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.auth import get_user_token
from app.database import get_db, SessionLocal
from app.models import UserBoundary
from app.schemas import AutoComputeStatusResponse, GEECodeResponse, GEETaskDetail, AnalysisReportResponse, BoundaryListResponse, BoundaryListItem, ComputeProgressResponse, CancelResponse
from app.gee_service import gee_online
from app.geoserver_service import geoserver
from app.report_service import generate_report
from app import tasks

logger = logging.getLogger("ueea2601.compute")

router = APIRouter(prefix="/api/compute", tags=["compute"])

# ──────────────────────────────────────────────
# 任务列表
# ──────────────────────────────────────────────


@router.get("/tasks", response_model=BoundaryListResponse)
async def list_tasks(
    authorization: str | None = Header(None),
) -> BoundaryListResponse:
    """返回所有任务列表。"""
    user_token = get_user_token(authorization)
    db: Session = SessionLocal()
    try:
        rows = db.query(UserBoundary).filter(
            UserBoundary.user_token == user_token
        ).order_by(UserBoundary.created_at.desc()).all()
        items = [
            BoundaryListItem(
                id=r.id,
                task_id=r.task_id,
                name=r.name,
                filename=r.filename,
                file_type=r.file_type,
                compute_mode=r.compute_mode,
                status=r.status,
                years=json.loads(r.years) if r.years else [],
                indicators=json.loads(r.indicators) if r.indicators else [],
                report_available=r.report_data is not None,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
            for r in rows
        ]
        return BoundaryListResponse(total=len(items), items=items)
    except Exception:
        logger.exception("Failed to list tasks from database")
        raise HTTPException(500, detail="任务列表查询失败，请检查数据库连接")
    finally:
        db.close()


# ──────────────────────────────────────────────
# 别名路由: /api/tasks/{task_id}
# ──────────────────────────────────────────────

_alias_router = APIRouter(tags=["tasks"])


@_alias_router.get("/api/tasks/{task_id}", response_model=AutoComputeStatusResponse)
async def tasks_status_alias(
    task_id: str,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> AutoComputeStatusResponse:
    """别名：/api/tasks/{taskId} 等价于 /api/compute/{task_id}/status。"""
    return await get_auto_status(task_id, authorization, db)


@router.get("/{task_id}/status", response_model=AutoComputeStatusResponse)
async def get_auto_status(
    task_id: str,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> AutoComputeStatusResponse:
    """轮询自动模式任务状态。

    GEE 完成后自动：下载结果 → 发布 GeoServer（含 SLD 样式）→ 生成报告。
    """
    task = tasks.get_task(task_id)
    if task is None:
        raise HTTPException(404, detail=f"任务 '{task_id}' 不存在")

    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.task_id == task_id,
        UserBoundary.user_token == user_token,
    ).first()
    if boundary is None:
        raise HTTPException(404, detail=f"任务 '{task_id}' 对应的边界不存在")

    if boundary.compute_mode != "online":
        raise HTTPException(400, detail="此接口仅适用于自动模式 (online)")

    # 已完成 → 直接返回缓存结果
    if boundary.status == "completed" and boundary.wms_urls:
        wms = json.loads(boundary.wms_urls) if boundary.wms_urls else {}
        return AutoComputeStatusResponse(
            task_id=task_id,
            boundary_id=boundary.id,
            status="completed",
            progress=100,
            completed_tasks=0,
            total_tasks=0,
            details=[],
            wms_urls=wms,
        )

    # 失败 → 返回失败状态
    if boundary.status == "failed":
        progress_info = json.loads(boundary.progress_info) if boundary.progress_info else {}
        return AutoComputeStatusResponse(
            task_id=task_id, boundary_id=boundary.id,
            status="failed", progress=progress_info.get("percent", 0),
            completed_tasks=0, total_tasks=0, details=[],
        )

    # 处理中 → 优先从 progress_info 读取（新流程）
    progress_info = json.loads(boundary.progress_info) if boundary.progress_info else {}

    # 兼容旧流程：如果有 gee_tasks，走旧逻辑轮询 GEE 状态
    gee_tasks = json.loads(boundary.gee_tasks) if boundary.gee_tasks else []
    if gee_tasks:
        status_result = gee_online.check_all_tasks(gee_tasks)
        completed = status_result["completed"]
        total = status_result["total"]
        progress = int((completed / total) * 80) if total > 0 else 0
        details = [GEETaskDetail(**d) for d in status_result["details"]]

        # 全部完成 → 下载 → 发布 GeoServer（带 SLD）→ 生成报告
        if status_result["all_completed"] and not boundary.wms_urls:
            logger.info(f"All GEE tasks done for {task_id}")

            # 下载
            downloaded = gee_online.download_results(boundary.id, task_id, gee_tasks)

            # 发布到 GeoServer + 应用 SLD 样式
            wms_urls = {}
            for layer_type, file_path in downloaded.items():
                result = geoserver.publish_geotiff(
                    layer_name=f"b{boundary.id}_{layer_type}",
                    file_path=file_path,
                    title=f"{boundary.name} - {layer_type}",
                    layer_type=layer_type,  # 自动应用对应 SLD 样式
                )
                if result["success"]:
                    wms_urls[layer_type] = result["wms_url"]

            # 生成分析报告
            report = generate_report(
                boundary_name=boundary.name,
                boundary_id=boundary.id,
                wms_urls=wms_urls,
            )

            # 保存到数据库
            boundary.wms_urls = json.dumps(wms_urls)
            boundary.report_data = json.dumps(report, ensure_ascii=False)
            boundary.status = "completed"
            db.commit()

            tasks.update_task(
                task_id,
                status=tasks.TaskStatus.completed,
                progress=100,
                result=json.dumps({"wms_urls": wms_urls}),
            )

            return AutoComputeStatusResponse(
                task_id=task_id, boundary_id=boundary.id,
                status="completed", progress=100,
                completed_tasks=completed, total_tasks=total,
                details=details, wms_urls=wms_urls,
            )

        return AutoComputeStatusResponse(
            task_id=task_id, boundary_id=boundary.id,
            status="processing", progress=progress,
            completed_tasks=completed, total_tasks=total,
            details=details,
        )

    # 新流程（无 gee_tasks）：从 progress_info 读取进度
    return AutoComputeStatusResponse(
        task_id=task_id, boundary_id=boundary.id,
        status=boundary.status or "processing",
        progress=progress_info.get("percent", 0),
        completed_tasks=0, total_tasks=0, details=[],
    )


@router.get("/{task_id}/report", response_model=AnalysisReportResponse)
async def get_report(
    task_id: str,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> AnalysisReportResponse:
    """获取分析报告数据。

    前端拿到这个 JSON 渲染完整的分析页面：
    - 地图区（WMS 图层）
    - 图表区（ECharts 配置）
    - 报告区（指标卡片 + 数据表格）
    """
    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.task_id == task_id,
        UserBoundary.user_token == user_token,
    ).first()
    if boundary is None:
        raise HTTPException(404, detail=f"任务 '{task_id}' 不存在")

    if not boundary.report_data:
        raise HTTPException(404, detail="报告尚未生成，请等待计算完成")

    report = json.loads(boundary.report_data)

    return AnalysisReportResponse(
        boundary_id=boundary.id,
        boundary_name=boundary.name,
        status=boundary.status,
        meta=report["meta"],
        map_layers=report["map_layers"],
        charts=report["charts"],
        indicators=report["indicators"],
        table=report["table"],
    )


@router.get("/{task_id}/code", response_model=GEECodeResponse)
async def get_gee_code(
    task_id: str,
    authorization: str | None = Header(None),
) -> GEECodeResponse:
    """获取 GEE JavaScript 代码（手动模式）。"""
    task = tasks.get_task(task_id)
    if task is None:
        raise HTTPException(404, detail=f"任务 '{task_id}' 不存在")

    db = SessionLocal()
    try:
        user_token = get_user_token(authorization)
        boundary = db.query(UserBoundary).filter(
            UserBoundary.task_id == task_id,
            UserBoundary.user_token == user_token,
        ).first()
        if boundary is None:
            raise HTTPException(404, detail=f"任务 '{task_id}' 对应的边界不存在")

        if boundary.compute_mode != "manual":
            raise HTTPException(400, detail="只有手动模式 (manual) 才能获取 GEE 代码")

        if not boundary.gee_code:
            raise HTTPException(404, detail="该任务尚未生成 GEE 代码")

        return GEECodeResponse(
            task_id=task_id,
            compute_mode="manual",
            code=boundary.gee_code,
            boundary_name=boundary.name,
        )
    finally:
        db.close()


# ──────────────────────────────────────────────
# 进度查询 + 取消
# ──────────────────────────────────────────────


@router.get("/{task_id}/progress", response_model=ComputeProgressResponse)
async def get_progress(
    task_id: str,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> ComputeProgressResponse:
    """查询后台计算进度。前端轮询此接口获取实时进度。"""
    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.task_id == task_id,
        UserBoundary.user_token == user_token,
    ).first()
    if boundary is None:
        raise HTTPException(404, detail=f"任务 '{task_id}' 不存在")

    progress_info = json.loads(boundary.progress_info) if boundary.progress_info else {}

    return ComputeProgressResponse(
        task_id=task_id,
        status=boundary.status,
        progress=progress_info.get("percent", 0),
        current_year=progress_info.get("year"),
        current_step=progress_info.get("step", ""),
        cancelled=boundary.cancelled,
    )


@router.post("/{task_id}/cancel", response_model=CancelResponse)
async def cancel_compute(
    task_id: str,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> CancelResponse:
    """取消正在进行的计算任务。"""
    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.task_id == task_id,
        UserBoundary.user_token == user_token,
    ).first()
    if boundary is None:
        raise HTTPException(404, detail=f"任务 '{task_id}' 不存在")

    ok = tasks.cancel_task(task_id)
    if ok:
        return CancelResponse(success=True, message="已发送取消请求")
    return CancelResponse(success=False, message="任务不存在或已完成，无法取消")
