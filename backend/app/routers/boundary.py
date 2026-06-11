"""
边界查询路由
=========
GET    /api/boundary/list   - 获取所有边界列表（必须在 /{id} 前注册，否则 "list" 被当成 id → 422）
GET    /api/boundary/{id}   - 获取边界 GeoJSON + WMS URL
DELETE /api/boundary/{id}   - 删除指定边界
"""

from __future__ import annotations

import json
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_user_token
from app.database import get_db
from app.models import UserBoundary
from app.schemas import (
    BoundaryGeometryResponse, BoundaryListResponse, BoundaryListItem,
    BoundaryUploadResponse, ComputeMode, RecomputeRequest,
)


class RenameRequest(BaseModel):
    """改名请求体。"""
    name: str

logger = logging.getLogger("ueea2601.boundary")

router = APIRouter(prefix="/api/boundary", tags=["boundary"])


# ──────────────────────────────────────────────
# /list 必须在 /{boundary_id} 前面，否则路由冲突 → 422
# ──────────────────────────────────────────────


@router.get("/list", response_model=BoundaryListResponse)
async def list_boundaries(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> BoundaryListResponse:
    user_token = get_user_token(authorization)
    boundaries = db.query(UserBoundary).filter(
        UserBoundary.user_token == user_token
    ).order_by(UserBoundary.created_at.desc()).all()

    items = [
        BoundaryListItem(
            id=b.id,
            name=b.name,
            filename=b.filename,
            file_type=b.file_type,
            compute_mode=b.compute_mode,
            status=b.status,
            indicators=json.loads(b.indicators) if b.indicators else [],
            created_at=b.created_at.isoformat() if b.created_at else "",
        )
        for b in boundaries
    ]

    return BoundaryListResponse(total=len(items), items=items)


@router.get("/{boundary_id}", response_model=BoundaryGeometryResponse)
async def get_boundary(
    boundary_id: int,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> BoundaryGeometryResponse:
    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.id == boundary_id,
        UserBoundary.user_token == user_token,
    ).first()
    if boundary is None:
        raise HTTPException(404, detail=f"边界 {boundary_id} 不存在")

    geojson = {}
    if boundary.geojson_text:
        try:
            geojson = json.loads(boundary.geojson_text)
        except json.JSONDecodeError:
            pass

    wms_urls = None
    if boundary.wms_urls:
        try:
            wms_urls = json.loads(boundary.wms_urls)
        except json.JSONDecodeError:
            pass

    return BoundaryGeometryResponse(
        id=boundary.id,
        name=boundary.name,
        filename=boundary.filename,
        file_type=boundary.file_type,
        compute_mode=boundary.compute_mode,
        status=boundary.status,
        geojson=geojson,
        wms_urls=wms_urls,
        report_available=boundary.report_data is not None,
        indicators=json.loads(boundary.indicators) if boundary.indicators else [],
        created_at=boundary.created_at.isoformat() if boundary.created_at else "",
    )


@router.put("/{boundary_id}/rename")
async def rename_boundary(
    boundary_id: int,
    body: RenameRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """修改边界名称。"""
    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.id == boundary_id,
        UserBoundary.user_token == user_token,
    ).first()
    if boundary is None:
        raise HTTPException(404, detail=f"边界 {boundary_id} 不存在")

    new_name = body.name.strip()
    if not new_name:
        raise HTTPException(400, detail="名称不能为空")

    old_name = boundary.name
    boundary.name = new_name
    db.commit()
    logger.info(f"Renamed boundary {boundary_id}: '{old_name}' → '{new_name}'")
    return {"success": True, "message": f"已更名为 '{new_name}'"}


@router.delete("/{boundary_id}")
async def delete_boundary(
    boundary_id: int,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> dict:
    """删除指定边界记录。"""
    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.id == boundary_id,
        UserBoundary.user_token == user_token,
    ).first()
    if boundary is None:
        raise HTTPException(404, detail=f"边界 {boundary_id} 不存在")

    db.delete(boundary)
    db.commit()
    logger.info(f"Deleted boundary {boundary_id}: {boundary.name}")
    return {"success": True, "message": f"边界 '{boundary.name}' 已删除"}


# ──────────────────────────────────────────────
# POST /{boundary_id}/recompute — 复用已有边界重新计算
# ──────────────────────────────────────────────


@router.post("/{boundary_id}/recompute", response_model=BoundaryUploadResponse)
async def recompute_boundary(
    boundary_id: int,
    body: RecomputeRequest,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> BoundaryUploadResponse:
    """复用已有边界的几何数据，用新参数重新计算。

    创建全新的 UserBoundary 记录（克隆几何），旧结果保留。
    """
    # 1. 查源边界
    user_token = get_user_token(authorization)
    source = db.query(UserBoundary).filter(
        UserBoundary.id == boundary_id,
        UserBoundary.user_token == user_token,
    ).first()
    if source is None:
        raise HTTPException(404, detail=f"边界 {boundary_id} 不存在")
    if not source.geojson_text:
        raise HTTPException(400, detail="源边界无几何数据，无法重新计算")

    # 2. 校验年份（与 upload.py 一致）
    year_list = sorted(set(body.years))
    if not year_list:
        raise HTTPException(400, detail="至少选择1个年份")
    if len(year_list) > 5:
        raise HTTPException(400, detail="最多选择5个年份")

    from datetime import datetime as dt
    current_year = dt.now().year
    for y in year_list:
        if not isinstance(y, int) or y < 1984 or y > current_year:
            raise HTTPException(400, detail=f"年份 {y} 不合法，范围 1984-{current_year}")

    # 3. 从 geojson_text 解析几何
    from geoalchemy2 import WKTElement
    import shapely.geometry

    try:
        geojson_dict = json.loads(source.geojson_text)
        shp = shapely.geometry.shape(geojson_dict)
        geom_wkt = WKTElement(shp.wkt, srid=4326)
    except Exception as e:
        raise HTTPException(400, detail=f"几何数据解析失败: {e}")

    # 4. 前置检查：排队容量 & GEE 密钥（在写入数据库之前，避免留下假 processing）
    from app.gee_service import gee_online
    from app.gee_key_service import gee_key_service
    from app import tasks as tasks_module

    if body.compute_mode == ComputeMode.online:
        if not tasks_module.can_submit_gee_task():
            raise HTTPException(429, detail="当前排队任务过多，请稍后重试")

        user_key = gee_key_service.get_valid_key(user_token)

        if user_key is None:
            raise HTTPException(400, detail="请先在「GEE配置」页面上传并验证您的 GEE 密钥")
    else:
        user_key = None

    # 5. 创建新任务 + 新 UserBoundary 记录
    task_id = tasks_module.new_task(source.filename)
    new_name = body.name.strip() if body.name else f"[重算] {source.name}"

    boundary = UserBoundary(
        name=new_name,
        user_token=user_token,
        area_km2=source.area_km2,
        filename=source.filename,
        file_type=source.file_type,
        compute_mode=body.compute_mode.value,
        task_id=task_id,
        geom=geom_wkt,
        geojson_text=source.geojson_text,
        status="processing",
        years=json.dumps(year_list),
        progress_info=json.dumps({"year": None, "step": "准备中...", "percent": 0}),
    )
    db.add(boundary)
    db.commit()
    db.refresh(boundary)

    # 6. 调度计算（前置检查已通过）
    if body.compute_mode == ComputeMode.online:
        # 解析 indicators（与 upload.py 一致的逻辑）
        indicators = body.indicators or []
        if not indicators:
            indicators = ["rsei", "construction", "expansion", "nightLight", "population", "gdp"]
        if "expansion" in indicators and "construction" not in indicators:
            indicators.append("construction")

        boundary.indicators = json.dumps(indicators)
        db.commit()

        tasks_module.start_background(
            task_id=task_id,
            target=gee_online.submit_task_async,
            args=(geojson_dict, boundary.id, task_id, year_list, user_key, indicators),
        )
        logger.info(f"Recompute: GEE task started, boundary={boundary.id}, years={year_list}, indicators={indicators}")

    elif body.compute_mode == ComputeMode.manual:
        from app.gee_code_service import generate_gee_code

        # indicators 与 online 路径共享同一份解析逻辑
        indicators = body.indicators or []
        if not indicators:
            indicators = ["rsei", "construction", "expansion", "nightLight", "population", "gdp"]
        if "expansion" in indicators and "construction" not in indicators:
            indicators.append("construction")

        gee_code = generate_gee_code(
            geojson=geojson_dict,
            boundary_name=new_name,
            years=year_list,
            indicators=indicators,
        )

        boundary.gee_code = gee_code
        boundary.indicators = json.dumps(indicators)
        boundary.status = "completed"
        boundary.progress_info = json.dumps(
            {"year": None, "step": "代码已生成", "percent": 100}
        )
        db.commit()
        logger.info(f"Recompute: manual mode, boundary={boundary.id}, indicators={indicators}")

    return BoundaryUploadResponse(
        boundary_id=boundary.id, task_id=task_id,
        status=boundary.status, filename=source.filename,
        compute_mode=body.compute_mode,
        url=f"/analysis/{task_id}",
    )

