"""
上传路由
=======
P0: 文件大小限制 + 并发控制。
方案A: 优先用用户自己的 GEE 密钥。
支持用户选择分析年份（1984-至今，最多5年）。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserBoundary
from app.schemas import BoundaryUploadResponse, ComputeMode
from app.validation import validate_and_parse
from app.gee_service import gee_online
from app.gee_key_service import gee_key_service
from app.geoserver_service import geoserver
from app import tasks
from app.config import UPLOAD_MAX_SIZE_BYTES

logger = logging.getLogger("ueea2601.upload")

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".geojson", ".json", ".zip", ".tif", ".tiff"}


@router.post("/upload/boundary", response_model=BoundaryUploadResponse)
async def upload_boundary(
    file: UploadFile = File(...),
    name: str = Form(...),
    years: str = Form(default="[2020]"),
    compute_mode: ComputeMode = Form(...),
    config: str = Form(default="{}"),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> BoundaryUploadResponse:
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, detail=f"不支持的文件类型 '{ext}'，仅允许: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    # ─── 解析并验证年份 ───
    try:
        year_list = json.loads(years)
    except json.JSONDecodeError:
        raise HTTPException(400, detail="年份格式错误，需要 JSON 数组如 [2000, 2010, 2020]")

    if not isinstance(year_list, list) or len(year_list) == 0:
        raise HTTPException(400, detail="至少选择1个年份")
    if len(year_list) > 5:
        raise HTTPException(400, detail="最多选择5个年份")

    current_year = datetime.now().year
    for y in year_list:
        if not isinstance(y, int) or y < 1984 or y > current_year:
            raise HTTPException(400, detail=f"年份 {y} 不合法，范围 1984-{current_year}")
    year_list = sorted(set(year_list))

    # P0: 文件大小限制
    content = await file.read()
    if len(content) > UPLOAD_MAX_SIZE_BYTES:
        raise HTTPException(413, detail=f"文件过大 ({len(content) // 1024 // 1024}MB)，最大允许 {UPLOAD_MAX_SIZE_BYTES // 1024 // 1024}MB")

    # 验证 + 解析
    normalized_geojson, geojson_str, file_type = validate_and_parse(content, ext)

    # 创建任务
    task_id = tasks.new_task(filename)

    # 存入 PostGIS
    from geoalchemy2 import WKTElement
    import shapely.geometry
    import math
    shp = shapely.geometry.shape(normalized_geojson)
    geom_wkt = WKTElement(shp.wkt, srid=4326)

    # 计算面积（km²）— 用 centroid 纬度做等距近似
    try:
        centroid = shp.centroid
        lat_rad = math.radians(centroid.y)
        # 1°经度 ≈ 111.32 * cos(lat) km, 1°纬度 ≈ 111.32 km
        km2_per_deg2 = 111.32 * 111.32 * math.cos(lat_rad)
        area_km2 = round(shp.area * km2_per_deg2, 1)
    except Exception as e:
        logger.warning(f"Area calc failed: {e}")
        area_km2 = None

    if compute_mode == ComputeMode.online and not tasks.can_submit_gee_task():
        raise HTTPException(429, detail="当前排队任务过多，请稍后重试")

    boundary = UserBoundary(
        name=name, area_km2=area_km2, filename=filename, file_type=file_type,
        compute_mode=compute_mode.value, task_id=task_id,
        geom=geom_wkt, geojson_text=geojson_str, status="processing",
        years=json.dumps(year_list),
        progress_info=json.dumps({"year": None, "step": "准备中...", "percent": 0}),
    )
    db.add(boundary)
    db.commit()
    db.refresh(boundary)

    # 自动模式
    if compute_mode == ComputeMode.online:
        # 方案A: 优先用用户自己的 GEE 密钥
        user_token = _extract_token(authorization) or "anonymous"
        user_key = gee_key_service.get_valid_key(user_token)

        if user_key is None:
            boundary.status = "failed"
            db.commit()
            raise HTTPException(400, detail="请先在「GEE配置」页面上传并验证您的 GEE 密钥")

        # 解析 indicators 配置
        try:
            config_dict = json.loads(config) if config else {}
        except json.JSONDecodeError:
            config_dict = {}

        indicators = config_dict.get("indicators", [])

        # 向后兼容：无 indicators 时默认全选
        if not indicators:
            indicators = ["rsei", "construction", "expansion", "nightLight", "population", "gdp"]

        # expansion 依赖 construction
        if "expansion" in indicators and "construction" not in indicators:
            indicators.append("construction")

        # 持久化 indicators 到 boundary 记录
        boundary.indicators = json.dumps(indicators)
        db.commit()

        # 启动后台线程
        tasks.start_background(
            task_id=task_id,
            target=gee_online.submit_task_async,
            args=(normalized_geojson, boundary.id, task_id, year_list, user_key, indicators),
        )
        logger.info(f"GEE background task started: boundary={boundary.id}, years={year_list}, indicators={indicators}")

    # 手动模式：生成 GEE 代码并存入数据库
    elif compute_mode == ComputeMode.manual:
        try:
            config_dict = json.loads(config) if config else {}
        except json.JSONDecodeError:
            config_dict = {}

        from app.gee_code_service import generate_gee_code

        manual_indicators = config_dict.get("indicators", ["rsei"])

        gee_code = generate_gee_code(
            geojson=normalized_geojson,
            boundary_name=name,
            years=year_list,
            indicators=manual_indicators,
            satellite=config_dict.get("satellite", "landsat-auto"),
            export_format=config_dict.get("exportFormat", "drive"),
            export_prefix=config_dict.get("exportPrefix", "rs_urban"),
        )

        boundary.gee_code = gee_code
        boundary.indicators = json.dumps(manual_indicators)
        boundary.status = "completed"
        boundary.progress_info = json.dumps(
            {"year": None, "step": "代码已生成", "percent": 100}
        )
        db.commit()
        logger.info(f"Manual mode: GEE code generated for boundary={boundary.id}, "
                     f"years={year_list}, indicators={config_dict.get('indicators', [])}")

    # 返回结果
    return BoundaryUploadResponse(
        boundary_id=boundary.id, task_id=task_id,
        status=boundary.status, filename=filename,
        compute_mode=compute_mode,
        url=f"/analysis/{task_id}",
    )


def _extract_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    return authorization.replace("Bearer ", "").strip() or None


# ──────────────────────────────────────────────
# 别名路由: /api/upload/geofile → 同 upload_boundary
# ──────────────────────────────────────────────


@router.post("/upload/geofile", response_model=BoundaryUploadResponse)
async def upload_geofile(
    file: UploadFile = File(...),
    name: str = Form(...),
    years: str = Form(default="[2020]"),
    compute_mode: ComputeMode = Form(...),
    config: str = Form(default="{}"),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> BoundaryUploadResponse:
    """别名：/api/upload/geofile 和 /api/upload/boundary 功能完全一致。"""
    return await upload_boundary(file, name, years, compute_mode, config, authorization, db)
