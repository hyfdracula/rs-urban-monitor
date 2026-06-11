"""Legacy / placeholder report builders.

``build_legacy_report`` adapts the old single-year GEE format.
``build_placeholder_report`` is used when no GEE stats are available at all.
"""

from __future__ import annotations

from typing import Any

from app.report.estimators import estimate_grade_distribution


def build_legacy_report(
    raw: dict[str, Any], name: str, boundary_id: int, now: str
) -> dict[str, Any]:
    """兼容旧的单年度格式。"""
    ndvi = raw.get("ndvi", {})
    rsei = raw.get("rsei", {})
    lst = raw.get("lst", {})
    built_area = raw.get("built_area_km2", 0)
    population = raw.get("population", 0)

    ndvi_mean = round(ndvi.get("NDVI_mean", 0), 3) if ndvi else 0
    rsei_mean = round(rsei.get("RSEI_mean", 0), 3) if rsei else 0
    lst_mean = round(lst.get("LST_mean", 0), 1) if lst else 0

    year = 2020
    return {
        "meta": {
            "title": f"{name} — 城市扩张与生态评估报告",
            "boundary_name": name,
            "boundary_id": boundary_id,
            "generated_at": now,
            "years": [year],
            "data_sources": ["Landsat 8 (USGS)", "ESA WorldCover v100", "WorldPop"],
        },
        "overview": {
            "studyArea": name,
            "newConstruction": None,
            "expansionRate": None,
            "rseiMean": rsei_mean,
            "improvedArea": None,
            "degradedArea": None,
            "population": round(population / 10000, 1) if population > 0 else None,
            "mock": {"newConstruction": True, "expansionRate": True, "improvedArea": True, "degradedArea": True},
            "singleYearNote": "单年份无法计算变化指标",
        },
        "expansion": {"totalArea": built_area, "newArea": None, "mock": {}},
        "hotspot": {"hotspots": [], "coldspots": [], "ranking": [], "mock": {}},
        "ecology": {
            "rseiMean": rsei_mean,
            "rseiChange": None,
            "trendData": [{"year": year, "value": rsei_mean}],
            "fourIndicators": {
                "ndvi": round(max(0, min(1, ndvi_mean)), 3),
                "wet": 0,
                "ndbsi": 0,
                "lst": round(max(0, min(1, (lst_mean + 10) / 60)), 3),
            },
            "gradeDistribution": estimate_grade_distribution(rsei_mean, built_area),
            "changeDistribution": [],
            "mock": {},
        },
        "coupling": {"correlation": 0, "scatterData": [], "mock": {}},
        "socio": {
            "population": {"total": round(population / 10000, 1) if population > 0 else None, "growth": None},
            "gdp": {"total": None, "growth": None},
            "mock": {"industryStructure": True},
        },
        "partition": {"ranking": []},
        "mock_flags": {"newConstruction": True, "expansionRate": True, "industryStructure": True},
        "indicators": [
            {"label": "建设用地面积", "value": f"{built_area} km²", "icon": "area", "trend": "up"},
            {"label": "NDVI 均值", "value": str(ndvi_mean), "icon": "leaf", "trend": "up" if ndvi_mean > 0.3 else "down"},
            {"label": "RSEI 均值", "value": str(rsei_mean), "icon": "eco", "trend": "up" if rsei_mean > 0.5 else "down"},
            {"label": "地表温度", "value": f"{lst_mean} °C", "icon": "temp", "trend": "down"},
            {"label": "估算人口", "value": f"{population // 10000} 万", "icon": "people", "trend": "up"},
        ],
        "charts": {},
        "table": {
            "title": "研究区数据",
            "columns": ["名称", "建设用地(km²)", "RSEI均值", "人口(万)"],
            "rows": [[name, f"{built_area}", str(rsei_mean), f"{population // 10000}"]],
        },
    }


def build_placeholder_report(name: str, boundary_id: int, now: str) -> dict[str, Any]:
    """完全占位报告（无 GEE 数据）。"""
    return {
        "meta": {
            "title": f"{name} — 城市扩张与生态评估报告",
            "boundary_name": name,
            "boundary_id": boundary_id,
            "generated_at": now,
            "years": [],
            "data_sources": [],
        },
        "overview": {"studyArea": name, "mock": {}},
        "expansion": {"mock": {}},
        "hotspot": {"mock": {}},
        "ecology": {
            "rseiMean": 0,
            "trendData": [],
            "fourIndicators": {"ndvi": 0, "wet": 0, "ndbsi": 0, "lst": 0},
            "gradeDistribution": [],
            "changeDistribution": [],
            "mock": {},
        },
        "coupling": {"mock": {}},
        "socio": {"mock": {}},
        "partition": {"ranking": []},
        "mock_flags": {},
        "indicators": [],
        "charts": {},
        "table": {"title": "", "columns": [], "rows": []},
    }
