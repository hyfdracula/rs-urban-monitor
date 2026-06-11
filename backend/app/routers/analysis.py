"""
分析页聚合路由
=============
GET /api/analysis/{task_id}
  - 任务完成 → 返回 { overview, expansion, ecology, socio, cities, report }
  - 任务计算中 → 返回 { status, progress }
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.auth import get_user_token
from app.database import get_db
from app.models import UserBoundary
from app.routers.mock_data import CITIES

router = APIRouter(tags=["analysis"])


# ──────────────────────────────────────────────
# GET /api/analysis/{task_id}
# ──────────────────────────────────────────────

@router.get("/api/analysis/{task_id}")
async def get_analysis(
    task_id: str,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """根据 taskId 返回全部分析模块数据，或计算进度。"""

    # 查数据库
    user_token = get_user_token(authorization)
    boundary = db.query(UserBoundary).filter(
        UserBoundary.task_id == task_id,
        UserBoundary.user_token == user_token,
    ).first()

    # 任务不存在
    if boundary is None:
        raise HTTPException(404, detail=f"任务 '{task_id}' 不存在")

    # 计算中
    if boundary.status in ("processing", "pending"):
        return {
            "status": boundary.status,
            "progress": _calc_progress(boundary),
        }

    # 失败
    if boundary.status == "failed":
        return {
            "status": "failed",
            "progress": 0,
            "error": "计算失败，请重新提交",
        }

    # 完成 → 聚合返回（优先用数据库里存的 report_data）
    if boundary.report_data:
        report = json.loads(boundary.report_data)
        result = {
            "status": "completed",
            **_build_from_report(report, boundary),
        }
        # 附带边界 GeoJSON 供前端绘制
        if boundary.geojson_text:
            result["boundary_geojson"] = json.loads(boundary.geojson_text)
        return result

    # 兜底：用 mock 数据
    result = {
        "status": "completed",
        "overview": _mock_overview(),
        "expansion": _mock_expansion(),
        "ecology": _mock_ecology(),
        "socio": _mock_socio(),
        "cities": CITIES,
        "report": _mock_report(),
    }
    if boundary.geojson_text:
        result["boundary_geojson"] = json.loads(boundary.geojson_text)
    return result


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def _calc_progress(boundary: UserBoundary) -> int:
    """从 progress_info 获取进度。"""
    if boundary.progress_info:
        try:
            info = json.loads(boundary.progress_info)
            return info.get("percent", 0)
        except (json.JSONDecodeError, TypeError):
            pass
    # 回退到旧的 gee_tasks 估算
    if not boundary.gee_tasks:
        return 0
    try:
        tasks_list = json.loads(boundary.gee_tasks)
        total = len(tasks_list)
        done = sum(1 for t in tasks_list if t.get("state") == "COMPLETED")
        return int((done / total) * 80) if total > 0 else 0
    except (json.JSONDecodeError, TypeError):
        return 0


def _build_from_report(report: dict, boundary: UserBoundary) -> dict:
    """从数据库 report_data 构建聚合响应。支持新旧格式。"""
    result = {
        "report": report,
    }

    # 新格式：报告已包含各面板字段
    if "overview" in report:
        result["overview"] = report["overview"]
        result["expansion"] = report.get("expansion", {})
        result["ecology"] = report.get("ecology", {})
        result["socio"] = report.get("socio", {})
        result["coupling"] = report.get("coupling", {})
        result["hotspot"] = report.get("hotspot", {})
        result["partition"] = report.get("partition", {})
        result["mock_flags"] = report.get("mock_flags", {})
    else:
        # 旧格式兼容
        charts = report.get("charts", {})
        indicators = report.get("indicators", [])
        result["overview"] = _indicators_to_overview(indicators)
        result["expansion"] = charts.get("expansion_bar", {})
        result["ecology"] = {
            "rseiMean": next(
                (i["value"] for i in indicators if "RSEI" in i.get("label", "")),
                0.55,
            ),
            "rseiChange": next(
                (i.get("trend") for i in indicators if "RSEI" in i.get("label", "")),
                -0.08,
            ),
            **charts.get("rsei_grade_stack", {}),
        }
        result["socio"] = {}
        result["mock_flags"] = {}

    result["cities"] = CITIES

    # WMS 图层：优先从 report_data 中取（report_service._build_map_layers 生成丰富格式），
    # 兜底从 boundary.wms_urls 直接转换
    if "map_layers" in report:
        result["map_layers"] = report["map_layers"]
    elif boundary.wms_urls:
        try:
            wms = json.loads(boundary.wms_urls)
            result["map_layers"] = [
                {"type": k, "wms_url": v, "visible": False}
                for k, v in wms.items()
            ]
        except (json.JSONDecodeError, TypeError):
            pass

    return result


def _indicators_to_overview(indicators: list) -> dict:
    """从 indicator 列表提取 overview 字段。"""
    lookup = {i.get("label", ""): i for i in indicators}
    return {
        "totalCities": 27,
        "totalConstruction": lookup.get("建设用地总面积", {}).get("value", 1285.6),
        "avgExpansionRate": lookup.get("平均扩张速率", {}).get("value", 3.42),
        "avgRSEI": lookup.get("RSEI均值", {}).get("value", 0.55),
        "hotspotCount": 8,
        "coldspotCount": 6,
        "improvedArea": 630,
        "degradedArea": 1040,
    }


# ──────────────────────────────────────────────
# Mock 数据生成器
# ──────────────────────────────────────────────

def _mock_overview() -> dict:
    total_area = round(sum(c["newArea"] for c in CITIES), 1)
    return {
        "totalCities": 27,
        "totalConstruction": total_area,
        "avgExpansionRate": round(
            sum(c["rate"] for c in CITIES) / len(CITIES), 2
        ),
        "avgRSEI": round(sum(c["rsei"] for c in CITIES) / len(CITIES), 2),
        "hotspotCount": 8,
        "coldspotCount": 6,
        "improvedArea": 630,
        "degradedArea": 1040,
    }


def _mock_expansion() -> dict:
    total = round(sum(c["newArea"] for c in CITIES), 1)
    ranking = sorted(CITIES, key=lambda c: c["newArea"], reverse=True)[:15]
    return {
        "totalArea": total,
        "patches": 2340,
        "avgPatchSize": round(total / 2340, 2),
        "expansionRate": 3.42,
        "modeDistribution": [
            {"name": "边缘扩张", "value": 44.8, "color": "#FF6B6B"},
            {"name": "填充式扩张", "value": 32.5, "color": "#FFD43B"},
            {"name": "飞地式扩张", "value": 22.7, "color": "#4DABF7"},
        ],
        "districtRanking": [
            {"name": c["name"], "value": c["newArea"], "center": c["center"]}
            for c in ranking
        ],
    }


def _mock_ecology() -> dict:
    return {
        "rseiMean": 0.55,
        "rseiChange": -0.08,
        "gradeDistribution": [
            {"grade": "优", "area": 820, "color": "#2B8A3E"},
            {"grade": "良", "area": 650, "color": "#69DB7C"},
            {"grade": "中", "area": 480, "color": "#FFD43B"},
            {"grade": "差", "area": 210, "color": "#FF6B6B"},
        ],
        "trendData": [
            {"year": 2000, "value": 0.66},
            {"year": 2005, "value": 0.62},
            {"year": 2010, "value": 0.58},
            {"year": 2015, "value": 0.55},
            {"year": 2020, "value": 0.52},
        ],
        "changeDistribution": [
            {"name": "明显改善", "area": 180, "color": "#2B8A3E"},
            {"name": "轻微改善", "area": 320, "color": "#69DB7C"},
            {"name": "基本不变", "area": 510, "color": "#FFD43B"},
            {"name": "轻微退化", "area": 280, "color": "#FF922B"},
            {"name": "明显退化", "area": 160, "color": "#FF6B6B"},
        ],
    }


def _mock_socio() -> dict:
    return {
        "population": {
            "total": 29860,
            "growth": 18.5,
            "density": 482,
            "urbanRate": 68.3,
        },
        "gdp": {
            "total": 458200,
            "growth": 7.2,
            "perCapita": 15.3,
            "structure": [
                {"name": "第一产业", "value": 5.8, "color": "#69DB7C"},
                {"name": "第二产业", "value": 38.4, "color": "#4DABF7"},
                {"name": "第三产业", "value": 55.8, "color": "#FF6B6B"},
            ],
        },
        "districtPopulation": [
            {"name": c["name"], "value": c["pop"], "center": c["center"]}
            for c in sorted(CITIES, key=lambda x: x["pop"], reverse=True)[:12]
        ],
        "districtGdp": [
            {"name": c["name"], "value": c["gdp"], "center": c["center"]}
            for c in sorted(CITIES, key=lambda x: x["gdp"], reverse=True)[:12]
        ],
        "correlationData": [
            {
                "expansionRate": c["rate"],
                "gdpGrowth": round(c["gdp"] / 1000 * 0.8 + 2.1, 1),
                "populationGrowth": round(c["pop"] / 1000 * 1.5 + 0.5, 1),
                "name": c["name"],
                "center": c["center"],
            }
            for c in CITIES
        ],
    }


def _mock_report() -> dict:
    top15 = sorted(CITIES, key=lambda c: c["newArea"], reverse=True)[:15]
    return {
        "studyArea": "长三角、珠三角、京津冀等27个重点城市",
        "timeRange": "2000-2020",
        "expansionTable": [
            {
                "district": c["name"],
                "newArea": c["newArea"],
                "rate": c["rate"],
                "intensity": c["intensity"],
                "mode": c["mode"],
            }
            for c in top15
        ],
        "ecologyTable": [
            {"grade": "优", "area": 820, "percent": 34.2, "change": -5.3},
            {"grade": "良", "area": 650, "percent": 27.1, "change": -3.8},
            {"grade": "中", "area": 480, "percent": 20.0, "change": 2.1},
            {"grade": "差", "area": 210, "percent": 8.8, "change": 4.2},
            {"grade": "极差", "area": 240, "percent": 10.0, "change": 2.8},
        ],
        "modeDistribution": [
            {"name": "边缘扩张", "value": 44.8, "color": "#FF6B6B"},
            {"name": "填充式扩张", "value": 32.5, "color": "#FFD43B"},
            {"name": "飞地式扩张", "value": 22.7, "color": "#4DABF7"},
        ],
        "districtRanking": [
            {"name": c["name"], "value": c["newArea"], "center": c["center"]}
            for c in top15
        ],
        "rseiTrend": [
            {"year": 2000, "value": 0.66},
            {"year": 2005, "value": 0.62},
            {"year": 2010, "value": 0.58},
            {"year": 2015, "value": 0.55},
            {"year": 2020, "value": 0.52},
        ],
        "ecologyGradeDistribution": [
            {"grade": "优", "area": 820, "color": "#2B8A3E"},
            {"grade": "良", "area": 650, "color": "#69DB7C"},
            {"grade": "中", "area": 480, "color": "#FFD43B"},
            {"grade": "差", "area": 210, "color": "#FF6B6B"},
        ],
        "scatterData": [
            [c["rate"], c["rseiChange"], c["name"]]
            for c in CITIES
        ],
    }
