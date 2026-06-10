"""
Pydantic 请求/响应模型
==================
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class ComputeMode(str, Enum):
    online = "online"
    manual = "manual"


class FileType(str, Enum):
    geojson = "geojson"
    shapefile = "shapefile"
    geotiff = "geotiff"


# ──────────────────────────────────────────────
# 上传响应
# ──────────────────────────────────────────────

class BoundaryUploadResponse(BaseModel):
    boundary_id: int
    task_id: str
    status: str
    filename: str
    compute_mode: ComputeMode
    url: str = ""


# ──────────────────────────────────────────────
# 自动模式：任务状态轮询
# ──────────────────────────────────────────────

class GEETaskDetail(BaseModel):
    type: str
    state: str
    error: str | None = None


class AutoComputeStatusResponse(BaseModel):
    task_id: str
    boundary_id: int
    status: str
    progress: int
    completed_tasks: int
    total_tasks: int
    details: list[GEETaskDetail]
    wms_urls: dict[str, str] | None = None


# ──────────────────────────────────────────────
# 分析报告响应
# ──────────────────────────────────────────────

class AnalysisReportResponse(BaseModel):
    """完整分析报告 — 前端渲染专属页面用。"""
    boundary_id: int
    boundary_name: str
    status: str
    meta: dict[str, Any]
    map_layers: list[dict[str, Any]]
    charts: dict[str, Any]
    indicators: list[dict[str, Any]]
    table: dict[str, Any]


# ──────────────────────────────────────────────
# 手动模式：GEE 代码
# ──────────────────────────────────────────────

class GEECodeResponse(BaseModel):
    task_id: str
    compute_mode: str
    code: str
    boundary_name: str


# ──────────────────────────────────────────────
# 边界查询
# ──────────────────────────────────────────────

class BoundaryGeometryResponse(BaseModel):
    id: int
    name: str
    filename: str
    file_type: str
    compute_mode: str
    status: str
    geojson: dict[str, Any]
    wms_urls: dict[str, str] | None = None
    report_available: bool = False
    indicators: list[str] = []
    created_at: str


class BoundaryListItem(BaseModel):
    id: int
    task_id: str = ""
    name: str
    filename: str
    file_type: str
    compute_mode: str
    status: str
    years: list[int] = []
    indicators: list[str] = []
    report_available: bool = False
    created_at: str


class BoundaryListResponse(BaseModel):
    total: int
    items: list[BoundaryListItem]


# ──────────────────────────────────────────────
# 进度查询 + 取消
# ──────────────────────────────────────────────

class ComputeProgressResponse(BaseModel):
    task_id: str
    status: str
    progress: int
    current_year: int | None = None
    current_step: str = ""
    cancelled: bool = False


class RecomputeRequest(BaseModel):
    """复用已有边界重新计算。"""
    years: list[int]
    compute_mode: ComputeMode
    name: str | None = None
    indicators: list[str] = []


class CancelResponse(BaseModel):
    success: bool
    message: str
