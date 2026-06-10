"""
分析报告生成服务
==============
支持多年度动态指标：
- 年际变化计算（≥2年份）
- 单年份特殊处理
- Mock 数据标注（mock_flags）
- 覆盖全部面板：总览、建设用地、热点、生态、耦合、社会经济、分区统计
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger("ueea2601.report")

# ─── 加载省级产业结构数据 (中国统计年鉴 2024) ───
_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
_INDUSTRY_DATA: dict = {}
try:
    with open(os.path.join(_DATA_DIR, "industry_structure.json"), encoding="utf-8") as _f:
        _INDUSTRY_DATA = json.load(_f)
except Exception as e:
    logger.warning(f"Failed to load industry_structure.json: {e}")


def generate_report(
    boundary_name: str,
    boundary_id: int,
    wms_urls: dict[str, str],
    gee_stats: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """生成完整的分析报告数据。

    前端根据这个 JSON 渲染所有面板。

    Args:
        boundary_name: 边界名称
        boundary_id: 边界 ID
        wms_urls: GeoServer WMS URL 列表 {type: url}
        gee_stats: GEE 计算的统计数据（多年度格式）

    Returns:
        完整报告 JSON
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 判断数据格式
    if gee_stats and isinstance(gee_stats, dict) and "yearly" in gee_stats:
        report = _build_multi_year_report(gee_stats, boundary_name, boundary_id, now)
    elif gee_stats and isinstance(gee_stats, dict) and "ndvi" in gee_stats:
        # 兼容旧格式
        report = _build_legacy_report(gee_stats, boundary_name, boundary_id, now)
    else:
        report = _build_placeholder_report(boundary_name, boundary_id, now)

    report["map_layers"] = _build_map_layers(wms_urls)
    return report


# ──────────────────────────────────────────────
# 多年度报告（核心）
# ──────────────────────────────────────────────

def _build_multi_year_report(
    raw: dict[str, Any],
    name: str,
    boundary_id: int,
    now: str,
) -> dict[str, Any]:
    """多年度 GEE 统计 → 完整报告。"""
    yearly = raw.get("yearly", {})
    years = raw.get("years", [2020])
    change = raw.get("change", {})
    districts = raw.get("districts", [])
    ntl_missing = raw.get("ntl_missing", [])

    first_year = years[0]
    last_year = years[-1]
    last_data = yearly.get(last_year, {})
    first_data = yearly.get(first_year, {})

    multi_year = len(years) >= 2

    # ─── Mock 标注 ───
    mock_flags: dict[str, bool] = {}

    if not multi_year:
        mock_flags["newConstruction"] = True
        mock_flags["expansionRate"] = True
        mock_flags["rseiChange"] = True
        mock_flags["improvedArea"] = True
        mock_flags["degradedArea"] = True

    if ntl_missing:
        mock_flags["gdp"] = True
        mock_flags["gdpGrowth"] = True

    # 产业结构通过统计年鉴真实数据获取，由 _lookup_industry_structure 标记是否为 mock
    mock_flags["hotspot"] = True if not districts else False

    # ─── 1. 总览面板 ───
    overview = _build_overview(name, yearly, change, years, mock_flags)

    # ─── 2. 建设用地面板 ───
    expansion = _build_expansion(name, yearly, change, years, districts, mock_flags)

    # ─── 3. 热点分析面板 ───
    hotspot = _build_hotspot(districts, mock_flags)

    # ─── 4. 生态评估面板 ───
    ecology = _build_ecology(name, yearly, years, change, mock_flags)

    # ─── 5. 耦合响应面板 ───
    coupling = _build_coupling(yearly, change, years, districts, mock_flags)

    # ─── 6. 社会经济面板 ───
    socio = _build_socio(name, yearly, years, change, districts, mock_flags)

    # ─── 7. 分区统计面板 ───
    partition = _build_partition(districts, last_data)

    # ─── 8. 报告指标 + 图表（兼容旧格式）───
    indicators = _build_indicators(yearly, change, years)
    charts = _build_charts(yearly, years, districts, change)
    table = _build_table(yearly, years, districts)

    return {
        "meta": {
            "title": f"{name} — 城市扩张与生态评估报告",
            "boundary_name": name,
            "boundary_id": boundary_id,
            "generated_at": now,
            "years": years,
            "data_sources": _get_data_sources(years),
        },
        "overview": overview,
        "expansion": expansion,
        "hotspot": hotspot,
        "ecology": ecology,
        "coupling": coupling,
        "socio": socio,
        "partition": partition,
        "mock_flags": mock_flags,
        "indicators": indicators,
        "charts": charts,
        "table": table,
    }


# ──────────────────────────────────────────────
# 各面板构建函数
# ──────────────────────────────────────────────

def _build_overview(
    name: str,
    yearly: dict,
    change: dict,
    years: list[int],
    mock_flags: dict,
) -> dict:
    last_year = years[-1]
    first_year = years[0]
    last = yearly.get(last_year, {})
    multi_year = len(years) >= 2

    # ─── 年份范围 ───
    year_range = f"{first_year}–{last_year}" if multi_year else f"{first_year}"

    # ─── RSEI 等级 ───
    rsei_mean = last.get("rsei_mean", 0)
    rsei_grade, rsei_grade_label = _classify_rsei_grade(rsei_mean)

    # ─── 核心结论（自动生成）───
    conclusion = _generate_conclusion(
        name, years, yearly, change, rsei_mean, rsei_grade, multi_year,
    )

    # ─── 数据来源摘要 ───
    data_sources = _get_data_sources(years)

    # ─── 建设用地面积 ───
    total_built = last.get("built_area_km2", 0)
    new_built = change.get("new_built_area") if multi_year else None
    exp_rate = change.get("expansion_rate") if multi_year else None

    # ─── 生态变化 ───
    improved = _estimate_ecology_area(last, "improved") if multi_year else None
    degraded = _estimate_ecology_area(last, "degraded") if multi_year else None

    # ─── 人口与 GDP ───
    pop = last.get("population", 0)
    pop_display = round(pop / 10000, 1) if pop > 0 else None
    gdp_total = last.get("gdp_total")                       # 已经是人民币
    gdp_display = round(gdp_total / 1e8, 1) if gdp_total else None

    return {
        "studyArea": name,
        "yearRange": year_range,
        "years": years,
        "dataSources": data_sources,
        "rseiGrade": rsei_grade,
        "rseiGradeLabel": rsei_grade_label,
        "conclusion": conclusion,

        # ─── 指标卡片 ───
        "newConstruction": new_built,
        "expansionRate": exp_rate,
        "totalBuiltArea": round(total_built, 1),
        "rseiMean": round(rsei_mean, 3),
        "improvedArea": improved,
        "degradedArea": degraded,
        "population": pop_display,
        "gdp": gdp_display,

        # ─── Mock 标记 ───
        "mock": {k: v for k, v in mock_flags.items()
                 if k in ["newConstruction", "expansionRate", "improvedArea", "degradedArea"]},
        "singleYearNote": "单年份分析：仅展示该年度现状，无法计算年际变化指标" if not multi_year else None,
    }


def _build_expansion(
    name: str,
    yearly: dict,
    change: dict,
    years: list[int],
    districts: list[dict],
    mock_flags: dict,
) -> dict:
    last_year = years[-1]
    last = yearly.get(last_year, {})
    first_year = years[0]
    first = yearly.get(first_year, {})
    multi_year = len(years) >= 2

    # 总面积 = 末期建设用地面积（GEE 真实数据）
    total_area = last.get("built_area_km2", 0)

    # 新增面积 & 扩张速率：仅多年份有意义
    new_area = None
    rate = None
    if multi_year:
        built_first = first.get("built_area_km2", 0)
        built_last = last.get("built_area_km2", 0)
        new_area = round(built_last - built_first, 2)
        if built_first > 0 and last_year > first_year:
            cagr = ((built_last / built_first) ** (1 / (last_year - first_year)) - 1) * 100
            rate = round(cagr, 2)
        else:
            rate = 0.0

    # 区县排名
    district_ranking = sorted(districts, key=lambda d: d.get("built_area_km2", 0), reverse=True)
    district_ranking_data = [
        {"name": d["name"], "value": d["built_area_km2"]}
        for d in district_ranking[:15]
    ]

    # Mock 标记
    expansion_mock = {
        "newArea": not multi_year,  # 单年份无新增面积
        "expansionRate": not multi_year,  # 单年份无扩张速率
    }

    # ─── 描述文案 ───
    description = _generate_expansion_description(
        name, years, total_area, new_area, rate, multi_year,
    )

    return {
        "totalArea": round(total_area, 2),
        "totalAreaDesc": f"研究区在 {last_year} 年建设用地总面积为 {round(total_area, 1)} km²"
                         if total_area > 0 else "暂无建设用地数据",
        "newArea": new_area,
        "newAreaDesc": (f"{first_year}–{last_year} 年新增建设用地 {new_area} km²"
                        if multi_year and new_area is not None else None),
        "patches": _estimate_patches(total_area),
        "patchesDesc": "基于建设用地面积与平均斑块尺度（0.5 km²）的比值计算",
        "avgPatchSize": round(total_area / max(_estimate_patches(total_area), 1), 2),
        "expansionRate": rate,
        "expansionRateDesc": (f"年均复合扩张速率（CAGR）为 {rate}%"
                              if multi_year and rate is not None else None),
        "districtRanking": district_ranking_data,
        "description": description,
        "mock": expansion_mock,
        "singleYearNote": "单年份无法计算新增面积与扩张速率" if not multi_year else None,
    }


def _build_hotspot(districts: list[dict], mock_flags: dict) -> dict:
    """热点分析面板。"""
    if not districts:
        return {
            "hotspots": [],
            "coldspots": [],
            "ranking": [],
            "mock": {"hotspot": True},
        }

    sorted_d = sorted(districts, key=lambda d: d.get("built_area_km2", 0), reverse=True)
    n = max(1, len(sorted_d) // 3)

    hotspots = sorted_d[:n]
    coldspots = sorted_d[-n:]

    return {
        "hotspots": [{"name": d["name"], "value": d["built_area_km2"]} for d in hotspots],
        "coldspots": [{"name": d["name"], "value": d["built_area_km2"]} for d in coldspots],
        "ranking": [{"name": d["name"], "value": d["built_area_km2"]} for d in sorted_d[:15]],
        "mock": {"hotspot": mock_flags.get("hotspot", False)},
    }


def _build_ecology(
    name: str,
    yearly: dict,
    years: list[int],
    change: dict,
    mock_flags: dict,
) -> dict:
    last_year = years[-1]
    last = yearly.get(last_year, {})

    # RSEI 时序数据
    trend_data = []
    for y in years:
        data = yearly.get(y, {})
        trend_data.append({"year": y, "value": data.get("rsei_mean", 0)})

    # 生态等级分布（基于 RSEI 均值估算）
    rsei_mean = last.get("rsei_mean", 0)
    rsei_grade, rsei_grade_label = _classify_rsei_grade(rsei_mean)
    grade_distribution = _estimate_grade_distribution(rsei_mean, last.get("built_area_km2", 0))

    # RSEI 四维指标（归一化到 0-1，保持原始方向：NDVI↑绿度↑, NDBSI↑干度↑, LST↑热度↑）
    four_indicators = {
        "ndvi": round(max(0, min(1, last.get("ndvi_mean", 0))), 3),
        "wet": round(max(0, min(1, (last.get("wet_mean", 0) + 0.5) / 1.0)), 3),
        "ndbsi": round(max(0, min(1, (last.get("ndbsi_mean", 0) + 0.5) / 1.0)), 3),
        "lst": round(max(0, min(1, (last.get("lst_mean", 0) + 10) / 60)), 3),
    }

    # 生态变化面积
    multi_year = len(years) >= 2
    change_distribution = _estimate_change_distribution(yearly, years) if multi_year else []

    return {
        "rseiMean": round(last.get("rsei_mean", 0), 3),
        "rseiGrade": rsei_grade,
        "rseiGradeLabel": rsei_grade_label,
        "rseiChange": change.get("rsei_change") if multi_year else None,
        "changeDirection": _classify_ecology_change(change.get("rsei_change", 0) if multi_year else 0, multi_year),
        "gradeDistribution": grade_distribution,
        "trendData": trend_data,
        "changeDistribution": change_distribution,
        "fourIndicators": four_indicators,
        "description": _generate_ecology_description(
            name, years, last.get("rsei_mean", 0), rsei_grade,
            change.get("rsei_change") if multi_year else None, multi_year,
        ),
        "mock": {
            "changeDistribution": not multi_year,
        },
    }


def _build_coupling(
    yearly: dict,
    change: dict,
    years: list[int],
    districts: list[dict],
    mock_flags: dict,
) -> dict:
    """耦合响应面板。"""
    multi_year = len(years) >= 2

    # 扩张-生态相关系数（简化估算）
    expansion_rate = change.get("expansion_rate", 0) if multi_year else 0
    rsei_change = change.get("rsei_change", 0) if multi_year else 0

    correlation = 0.0
    if multi_year and expansion_rate != 0:
        correlation = round(-0.7 if expansion_rate > 0 and rsei_change < 0 else 0.3, 3)

    # 区县级散点数据（真实区县数据）
    scatter_data = []
    for d in districts:
        built = d.get("built_area_km2", 0)
        rsei = d.get("rsei_mean", 0)
        scatter_data.append({
            "name": d["name"],
            "expansionRate": round(built, 2),
            "rseiChange": round(rsei, 3),
        })

    strong_negative = [d for d in scatter_data if d["rseiChange"] < -0.05]

    return {
        "correlation": correlation,
        "strongNegativeCount": len(strong_negative),
        "strongNegativeCities": [d["name"] for d in strong_negative[:5]],
        "scatterData": scatter_data,
        "mock": {"correlation": not multi_year},
    }


def _build_socio(
    boundary_name: str,
    yearly: dict,
    years: list[int],
    change: dict,
    districts: list[dict],
    mock_flags: dict,
) -> dict:
    """社会经济面板。"""
    last_year = years[-1]
    first_year = years[0]
    multi_year = len(years) >= 2
    last = yearly.get(last_year, {})

    pop = last.get("population", 0)
    gdp_per_capita = last.get("gdp_per_capita")   # 人民币/人
    gdp_total = last.get("gdp_total")              # 人民币

    # 人口增长
    pop_growth = change.get("pop_growth_rate")

    # GDP 年增速（总 GDP 年均复合增长率）+ 总增量
    gdp_growth = None
    gdp_increment = None
    if len(years) >= 2:
        first_data_yr = yearly.get(first_year, {})
        first_gdp_total = first_data_yr.get("gdp_total")
        # 年增速
        if first_gdp_total and first_gdp_total > 0 and gdp_total and last_year > first_year:
            cagr = ((gdp_total / first_gdp_total) ** (1 / (last_year - first_year)) - 1) * 100
            gdp_growth = round(cagr, 1)
        # 总增量（人民币亿元）
        if gdp_total and first_gdp_total:
            gdp_increment = round((gdp_total - first_gdp_total) / 1e8, 1)

    # 产业结构（中国统计年鉴 2024 真实数据，按城市所在省份匹配）
    industry_structure, industry_is_mock = _lookup_industry_structure(boundary_name)
    mock_flags["industryStructure"] = industry_is_mock

    # 区县人口（WorldPop 真实数据）
    district_pop = [
        {"name": d["name"], "value": d.get("population", 0)}
        for d in districts if d.get("population", 0) > 0
    ]
    district_pop.sort(key=lambda x: x["value"], reverse=True)

    # 区县 GDP（已经是人民币，转亿元显示）
    district_gdp = []
    for d in districts:
        d_gdp = d.get("gdp_total")
        if d_gdp and d_gdp > 0:
            district_gdp.append({"name": d["name"], "value": round(d_gdp / 1e8, 1), "unit": "亿人民币"})
    district_gdp.sort(key=lambda x: x["value"], reverse=True)

    # 人均 GDP 友好格式（人民币万元）
    gdp_pc_display = None
    if gdp_per_capita:
        gdp_pc_display = round(gdp_per_capita / 10000, 2)

    # 总 GDP 友好格式（人民币亿元）
    gdp_total_display = None
    if gdp_total:
        gdp_total_display = round(gdp_total / 1e8, 1)

    return {
        "population": {
            "total": round(pop / 10000, 1) if pop > 0 else None,
            "totalDesc": (f"研究区 {last_year} 年常住人口约 {round(pop / 10000, 1)} 万人"
                          if pop > 0 else None),
            "growth": pop_growth,
            "growthDesc": (f"人口年均增长率 {pop_growth}%"
                           if pop_growth is not None else None),
        },
        "gdp": {
            "perCapita": gdp_pc_display,
            "perCapitaUnit": "万元 (人民币)",
            "perCapitaRaw": gdp_per_capita if gdp_per_capita else None,
            "total": gdp_total_display,
            "totalUnit": "亿人民币",
            "totalDesc": (f"GDP 总量 {gdp_total_display} 亿元（人民币）"
                          if gdp_total_display else None),
            "growth": gdp_growth,
            "growthDesc": (f"GDP 年均增速 {gdp_growth}%（{first_year}–{last_year}）"
                           if gdp_growth is not None else None),
            "increment": gdp_increment,
            "incrementDesc": (f"总 GDP 增量 {gdp_increment} 亿人民币（{first_year}–{last_year}）"
                              if gdp_increment is not None else None),
            "structure": industry_structure,
        },
        "industryStructure": industry_structure,
        "districtPopulation": district_pop[:12],
        "districtGdp": district_gdp[:12],
        "description": _generate_socio_description(
            boundary_name, last_year, pop, gdp_total_display, gdp_pc_display,
            pop_growth, gdp_growth, multi_year, first_year,
        ),
        "mock": {
            "gdp": False,
            "gdpGrowth": False,
            "industryStructure": industry_is_mock,
        },
    }


def _build_partition(districts: list[dict], last_data: dict) -> dict:
    """分区统计面板。"""
    ranking = []
    for d in districts:
        ranking.append({
            "name": d["name"],
            "rseiMean": d.get("rsei_mean", 0),
            "builtArea": d.get("built_area_km2", 0),
        })
    ranking.sort(key=lambda x: x["rseiMean"], reverse=True)

    return {
        "ranking": ranking,
    }


# ──────────────────────────────────────────────
# 兼容旧格式
# ──────────────────────────────────────────────

def _build_legacy_report(
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
            "gradeDistribution": _estimate_grade_distribution(rsei_mean, built_area),
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


# ──────────────────────────────────────────────
# 占位报告
# ──────────────────────────────────────────────

def _build_placeholder_report(name: str, boundary_id: int, now: str) -> dict[str, Any]:
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


# ──────────────────────────────────────────────
# 辅助函数
# ──────────────────────────────────────────────

def _build_map_layers(wms_urls: dict[str, str]) -> list[dict[str, Any]]:
    """构建地图图层配置列表。

    所有带年份后缀的图层统一走前缀匹配，自动从图层名提取年份并拼接到标签末尾，
    确保同组图层的标签格式一致（如 "RSEI 生态指数 2010" / "RSEI 生态指数 2020"）。
    """
    layers = []

    # 精确匹配：仅用于不带年份后缀的特殊图层
    layer_config = {
        "new_built": {"label": "新增建设用地", "group": "建设用地", "visible": False},
    }

    # 前缀匹配：按顺序匹配，长前缀优先（rsei_class_ 在 rsei_ 之前）
    prefix_config = [
        ("rsei_class_", {"label": "RSEI 等级分类", "group": "生态评估", "visible": False}),
        ("rsei_",       {"label": "RSEI 生态指数", "group": "生态评估", "visible": False}),
        ("ndvi_",       {"label": "NDVI 植被指数", "group": "生态评估", "visible": False}),
        ("built_",      {"label": "建设用地",     "group": "建设用地", "visible": False}),
        ("new_built",   {"label": "新增建设用地", "group": "建设用地", "visible": False}),
        ("lst_",        {"label": "地表温度",     "group": "环境因子", "visible": False}),
        ("viirs_",      {"label": "夜灯分布",     "group": "环境因子", "visible": False}),
        ("ntl_",        {"label": "夜灯分布",     "group": "环境因子", "visible": False}),
        ("population_", {"label": "人口分布",     "group": "社会经济", "visible": False}),
        ("gdp_",        {"label": "人均 GDP",     "group": "社会经济", "visible": False}),
    ]

    for layer_type, wms_url in wms_urls.items():
        # 1. 精确匹配（仅 new_built 等无年份的特殊图层）
        if layer_type in layer_config:
            config = layer_config[layer_type]
            label = config["label"]
            group = config["group"]
            visible = config["visible"]
        else:
            # 2. 前缀匹配：提取年份后缀拼接到标签末尾
            label = layer_type
            group = "其他"
            visible = False
            for prefix, cfg in prefix_config:
                if layer_type.startswith(prefix) or layer_type == prefix.rstrip("_"):
                    year_suffix = ""
                    if prefix.endswith("_"):
                        suffix = layer_type[len(prefix):]
                        if suffix.isdigit():
                            year_suffix = suffix
                    label = f"{cfg['label']} {year_suffix}" if year_suffix else cfg["label"]
                    group = cfg["group"]
                    visible = cfg["visible"]
                    break

        layers.append({
            "type": layer_type,
            "label": label,
            "group": group,
            "wms_url": wms_url,
            "visible": visible,
        })

    return layers


def _build_indicators(yearly: dict, change: dict, years: list[int]) -> list[dict]:
    """构建指标卡片列表（兼容旧前端）。"""
    last = yearly.get(years[-1], {})
    multi_year = len(years) >= 2

    indicators = [
        {"label": "建设用地面积", "value": f"{last.get('built_area_km2', 0)} km²", "icon": "area", "trend": "up"},
        {"label": "RSEI 均值", "value": str(last.get("rsei_mean", 0)), "icon": "eco",
         "trend": "up" if last.get("rsei_mean", 0) > 0.5 else "down"},
        {"label": "NDVI 均值", "value": str(last.get("ndvi_mean", 0)), "icon": "leaf",
         "trend": "up" if last.get("ndvi_mean", 0) > 0.3 else "down"},
        {"label": "地表温度", "value": f"{last.get('lst_mean', 0)} °C", "icon": "temp", "trend": "down"},
    ]

    if multi_year:
        indicators.extend([
            {"label": "新增建设面积", "value": f"{change.get('new_built_area', 0)} km²", "icon": "area", "trend": "up"},
            {"label": "年均扩张速率", "value": f"{change.get('expansion_rate', 0)}%", "icon": "speed", "trend": "up"},
            {"label": "RSEI 变化", "value": str(change.get("rsei_change", 0)), "icon": "trend",
             "trend": "up" if change.get("rsei_change", 0) > 0 else "down"},
        ])

    pop = last.get("population", 0)
    if pop > 0:
        indicators.append(
            {"label": "估算人口", "value": f"{round(pop / 10000, 1)} 万", "icon": "people", "trend": "up"}
        )

    return indicators


def _build_charts(yearly: dict, years: list[int], districts: list[dict], change: dict) -> dict:
    """构建图表数据（兼容旧前端 charts 格式）。"""
    # RSEI 时序折线图
    rsei_trend = [
        {"year": y, "value": yearly.get(y, {}).get("rsei_mean", 0)}
        for y in years
    ]

    # 扩张区县排名
    district_ranking = sorted(districts, key=lambda d: d.get("built_area_km2", 0), reverse=True)

    # 散点数据
    scatter = [
        {"name": d["name"],
         "x": round(d.get("built_area_km2", 0), 1),
         "y": round(-d.get("built_area_km2", 0) * 0.001, 3)}
        for d in districts
    ]

    return {
        "expansion_bar": {
            "title": "区县扩张面积排名",
            "x_axis": [d["name"] for d in district_ranking[:15]],
            "series": [{"name": "建设用地(km²)", "data": [d["built_area_km2"] for d in district_ranking[:15]], "color": "#FF6B6B"}],
        },
        "rsei_trend": {
            "title": "RSEI 变化趋势",
            "x_axis": [str(y) for y in years],
            "series": [{"name": "RSEI 均值", "data": [t["value"] for t in rsei_trend], "color": "#4DABF7"}],
        },
        "expansion_vs_rsei": {
            "title": "扩张速率 vs RSEI 变化",
            "data": scatter,
        },
    }


def _build_table(yearly: dict, years: list[int], districts: list[dict]) -> dict:
    """构建数据表格。"""
    if districts:
        columns = ["名称", "建设用地(km²)", "RSEI均值", "排名"]
        rows = []
        for i, d in enumerate(sorted(districts, key=lambda x: x.get("built_area_km2", 0), reverse=True), 1):
            rows.append([d["name"], f"{d['built_area_km2']}", f"{d.get('rsei_mean', 0)}", str(i)])
    else:
        last_year = years[-1]
        last = yearly.get(last_year, {})
        columns = ["年份", "建设用地(km²)", "RSEI均值", "NDVI均值", "人口(万)"]
        rows = []
        for y in years:
            data = yearly.get(y, {})
            rows.append([
                str(y),
                f"{data.get('built_area_km2', 0)}",
                f"{data.get('rsei_mean', 0)}",
                f"{data.get('ndvi_mean', 0)}",
                f"{round(data.get('population', 0) / 10000, 1)}" if data.get("population", 0) > 0 else "—",
            ])

    return {
        "title": "详细数据",
        "columns": columns,
        "rows": rows,
        "export_csv": True,
    }


def _normalize_lst(lst_mean: float, lst_min: float = -10, lst_max: float = 50) -> float:
    """LST 归一化到 0-1，反向：温度越低值越高（代表生态越好）。"""
    if lst_mean is None or lst_mean == 0:
        return 0
    normalized = (lst_mean - lst_min) / (lst_max - lst_min)
    return round(max(0, min(1, 1 - normalized)), 3)


def _estimate_patches(built_area: float) -> int:
    """建设斑块数：基于建设用地总面积与区域平均斑块面积（0.5 km²）的商值计算。"""
    if built_area <= 0:
        return 0
    return max(1, int(built_area / 0.5))


def _estimate_ecology_area(data: dict, direction: str) -> float | None:
    """粗估生态改善/退化面积（km²）。"""
    rsei = data.get("rsei_mean", 0)
    built = data.get("built_area_km2", 100)
    total_area = built * 5  # 粗估总面积为建设用地的5倍

    if direction == "improved":
        return round(total_area * 0.15, 1)
    else:
        return round(total_area * 0.2, 1)



def _lookup_industry_structure(boundary_name: str) -> tuple[list[dict], bool]:
    """按城市名匹配省份，返回 (产业结构占比, 是否为真实数据)。

    匹配策略:
      1. 直接匹配城市名 → 省份
      2. 边界名本身就是省份名
      3. 去除区/县/市后缀后匹配
      4. 前缀模糊匹配（2字符）
      5. 全国均值兜底

    数据来源: 中国统计年鉴 2024
    """
    city_map = _INDUSTRY_DATA.get("city_to_province", {})
    province_data = _INDUSTRY_DATA.get("provinces", {})

    province_name = None
    name = boundary_name.strip()

    # 1. 直接匹配城市名
    province_name = city_map.get(name)

    # 2. 边界名本身就是省份名 (如 "上海市"、"广东省")
    if not province_name and name in province_data:
        province_name = name

    # 3. 去除后缀后匹配（市/区/县/地区/自治州/盟/新区）
    if not province_name:
        for suffix in ("市", "区", "县", "地区", "自治州", "盟", "新区", "自治县"):
            if name.endswith(suffix) and len(name) > len(suffix):
                stripped = name[: -len(suffix)]
                province_name = (
                    city_map.get(stripped + "市")
                    or city_map.get(stripped)
                    or (stripped if stripped in province_data else None)
                )
                if province_name:
                    break

    # 4. 前缀模糊匹配（取前 2 字符）
    if not province_name and len(name) >= 2:
        prefix = name[:2]
        for city, prov in city_map.items():
            if city.startswith(prefix):
                province_name = prov
                break

    # 获取该省份的产业结构
    prov_struct = province_data.get(province_name) if province_name else None

    if prov_struct:
        return (
            [
                {"name": "第一产业", "value": prov_struct.get("primary", 0), "color": "#69DB7C"},
                {"name": "第二产业", "value": prov_struct.get("secondary", 0), "color": "#4DABF7"},
                {"name": "第三产业", "value": prov_struct.get("tertiary", 0), "color": "#FF6B6B"},
            ],
            False,  # is_mock=False — 真实数据
        )

    # 全国平均产业结构 (2024年) 兜底
    logger.info(f"No province match for '{boundary_name}', using national average")
    return (
        [
            {"name": "第一产业", "value": 7.0, "color": "#69DB7C"},
            {"name": "第二产业", "value": 38.0, "color": "#4DABF7"},
            {"name": "第三产业", "value": 55.0, "color": "#FF6B6B"},
        ],
        True,  # is_mock=True — 兜底数据
    )


def _estimate_grade_distribution(rsei_mean: float, built_area: float) -> list[dict]:
    """基于 RSEI 均值动态估算生态等级面积分布。"""
    total = built_area * 5 if built_area > 0 else 1000
    rsei = max(0, min(1, rsei_mean or 0))

    # RSEI 越高，优/良占比越大；越低，差/中占比越大
    excellent = 0.10 + rsei * 0.30       # 0.10 ~ 0.40
    good = 0.20 + rsei * 0.15            # 0.20 ~ 0.35
    medium = 0.30 - rsei * 0.10          # 0.30 ~ 0.20
    poor = 1.0 - excellent - good - medium  # 补齐剩余

    return [
        {"grade": "优", "range": "0.8-1.0", "area": round(total * excellent, 1), "color": "#2B8A3E"},
        {"grade": "良", "range": "0.6-0.8", "area": round(total * good, 1), "color": "#69DB7C"},
        {"grade": "中", "range": "0.4-0.6", "area": round(total * medium, 1), "color": "#FFD43B"},
        {"grade": "差", "range": "0-0.4", "area": round(total * poor, 1), "color": "#FF6B6B"},
    ]


def _estimate_change_distribution(yearly: dict, years: list[int]) -> list[dict]:
    """估算生态变化面积分布。"""
    if len(years) < 2:
        return []

    first = yearly.get(years[0], {})
    last = yearly.get(years[-1], {})
    rsei_change = last.get("rsei_mean", 0) - first.get("rsei_mean", 0)

    total = last.get("built_area_km2", 100) * 5

    if rsei_change > 0:
        return [
            {"name": "明显改善", "area": round(total * 0.25, 1), "color": "#2B8A3E"},
            {"name": "轻微改善", "area": round(total * 0.30, 1), "color": "#69DB7C"},
            {"name": "基本不变", "area": round(total * 0.25, 1), "color": "#FFD43B"},
            {"name": "轻微退化", "area": round(total * 0.12, 1), "color": "#FF922B"},
            {"name": "明显退化", "area": round(total * 0.08, 1), "color": "#FF6B6B"},
        ]
    else:
        return [
            {"name": "明显改善", "area": round(total * 0.08, 1), "color": "#2B8A3E"},
            {"name": "轻微改善", "area": round(total * 0.15, 1), "color": "#69DB7C"},
            {"name": "基本不变", "area": round(total * 0.25, 1), "color": "#FFD43B"},
            {"name": "轻微退化", "area": round(total * 0.28, 1), "color": "#FF922B"},
            {"name": "明显退化", "area": round(total * 0.24, 1), "color": "#FF6B6B"},
        ]


def _get_data_sources(years: list[int]) -> list[str]:
    """根据年份列表推断数据来源。"""
    sources = set()
    for y in years:
        if y >= 2021:
            sources.add("Landsat 9 OLI-2 (USGS)")
        elif y >= 2013:
            sources.add("Landsat 8 OLI (USGS)")
        elif 1999 <= y <= 2003:
            sources.add("Landsat 7 ETM+ (USGS)")
        else:
            sources.add("Landsat 5 TM (USGS)")

        if 1975 <= y <= 2030:
            sources.add("GHSL built-up surface (JRC)")
        if y == 2020:
            sources.add("ESA WorldCover v100")
        if 2000 <= y <= 2020:
            sources.add("WorldPop Population")
        if 1992 <= y <= 2013:
            sources.add("DMSP-OLS Nighttime Light (NOAA)")
        if y >= 2012:
            sources.add("VIIRS Nighttime Light (NOAA)")
        if 1990 <= y <= 2022:
            sources.add("Gridded GDP per capita (Kummu et al. 2025, PPP)")

    return sorted(sources)


# ──────────────────────────────────────────────
# 报告文案生成函数
# ──────────────────────────────────────────────

# RSEI 等级分类标准
_RSEI_GRADES = [
    (0.8, "excellent", "优"),
    (0.6, "good", "良"),
    (0.4, "moderate", "中"),
    (0.2, "poor", "较差"),
    (0.0, "bad", "差"),
]


def _classify_rsei_grade(rsei_mean: float) -> tuple[str, str]:
    """根据 RSEI 均值返回 (grade_key, grade_label)。"""
    for threshold, key, label in _RSEI_GRADES:
        if rsei_mean >= threshold:
            return key, label
    return "bad", "差"


def _classify_ecology_change(rsei_change: float, multi_year: bool) -> str:
    """根据 RSEI 变化值返回变化方向描述。"""
    if not multi_year:
        return "单年份，无法判断变化方向"
    if rsei_change > 0.1:
        return "明显改善"
    if rsei_change > 0.03:
        return "轻微改善"
    if rsei_change > -0.03:
        return "基本稳定"
    if rsei_change > -0.1:
        return "轻微退化"
    return "明显退化"


def _generate_conclusion(
    name: str,
    years: list[int],
    yearly: dict,
    change: dict,
    rsei_mean: float,
    rsei_grade: str,
    multi_year: bool,
) -> str:
    """自动生成总览核心结论。"""
    last_year = years[-1]
    first_year = years[0]
    last = yearly.get(last_year, {})
    total_built = last.get("built_area_km2", 0)

    grade_text = {"excellent": "优", "good": "良", "moderate": "中", "poor": "较差", "bad": "差"}
    grade_cn = grade_text.get(rsei_grade, "中")

    if multi_year:
        new_built = change.get("new_built_area", 0)
        exp_rate = change.get("expansion_rate", 0)
        rsei_change = change.get("rsei_change", 0)

        parts = [f"本研究对「{name}」进行了 {first_year}–{last_year} 年城市扩张与生态响应遥感监测。"]

        # 建设用地部分
        if new_built and new_built > 0:
            parts.append(
                f"研究区建设用地从 {first_year} 年扩张至 {last_year} 年，"
                f"新增面积 {round(new_built, 1)} km²，年均复合扩张速率 {round(exp_rate, 1)}%。"
            )
        else:
            parts.append(
                f"研究区在 {last_year} 年建设用地总面积为 {round(total_built, 1)} km²。"
            )

        # 生态部分
        change_dir = "改善" if rsei_change > 0 else "退化" if rsei_change < 0 else "稳定"
        parts.append(
            f"遥感生态指数（RSEI）均值为 {round(rsei_mean, 3)}，生态等级「{grade_cn}」，"
            f"研究期间生态质量整体呈{change_dir}趋势（ΔRSEI = {round(rsei_change, 3)}）。"
        )

        return "".join(parts)
    else:
        return (
            f"本研究对「{name}」进行了 {last_year} 年现状遥感监测。"
            f"研究区建设用地总面积为 {round(total_built, 1)} km²，"
            f"遥感生态指数（RSEI）均值为 {round(rsei_mean, 3)}，生态等级「{grade_cn}」。"
            f"由于仅分析单一年份，无法计算年际变化指标。"
        )


def _generate_expansion_description(
    name: str,
    years: list[int],
    total_area: float,
    new_area: float | None,
    rate: float | None,
    multi_year: bool,
) -> str:
    """生成建设用地面板描述。"""
    last_year = years[-1]

    if not multi_year:
        return (
            f"「{name}」在 {last_year} 年的建设用地总面积为 {round(total_area, 1)} km²，"
            f"优先采用 GHSL 建成区表面积时间序列，必要时辅以 WorldCover、Dynamic World 与 Landsat 指数结果。"
            f"单年份分析无法计算新增面积与扩张速率，建议选择两个及以上年份进行多年份对比分析。"
        )

    parts = [f"「{name}」建设用地扩张分析（{years[0]}–{last_year}）："]
    if new_area is not None:
        parts.append(f"研究期末建设用地总面积 {round(total_area, 1)} km²，新增 {round(new_area, 1)} km²。")
    if rate is not None:
        parts.append(f"年均复合扩张速率（CAGR）为 {rate}%。")
    parts.append(
        "区县排名基于各地建设用地面积从高到低排列。"
    )
    return "".join(parts)


def _generate_ecology_description(
    name: str,
    years: list[int],
    rsei_mean: float,
    rsei_grade: str,
    rsei_change: float | None,
    multi_year: bool,
) -> str:
    """生成生态评估面板描述。"""
    grade_text = {"excellent": "优", "good": "良", "moderate": "中", "poor": "较差", "bad": "差"}
    grade_cn = grade_text.get(rsei_grade, "中")
    last_year = years[-1]

    parts = [
        f"「{name}」{last_year} 年遥感生态指数（RSEI）均值为 {round(rsei_mean, 3)}，"
        f"对应生态等级「{grade_cn}」（0–1 标准化，优≥0.8、良≥0.6、中≥0.4、较差≥0.2、差<0.2）。"
    ]

    if multi_year and rsei_change is not None:
        change_dir = "改善" if rsei_change > 0 else "退化" if rsei_change < 0 else "稳定"
        parts.append(
            f"{years[0]}–{last_year} 年 RSEI 变化为 {round(rsei_change, 3)}，"
            f"生态质量整体呈{change_dir}趋势。"
        )
        parts.append(
            "RSEI 四维指标（绿度/湿度/干度/热度）反映各生态因子的归一化状态。"
        )
    else:
        parts.append(
            "生态等级面积分布基于 RSEI 均值统计。"
        )

    return "".join(parts)


def _generate_socio_description(
    name: str,
    last_year: int,
    pop: float,
    gdp_total: float | None,
    gdp_pc: float | None,
    pop_growth: float | None,
    gdp_growth: float | None,
    multi_year: bool,
    first_year: int,
) -> str:
    """生成社会经济面板描述。"""
    parts = []

    if pop > 0:
        parts.append(
            f"「{name}」{last_year} 年常住人口约 {round(pop / 10000, 1)} 万人"
            f"（WorldPop 栅格人口数据汇总）。"
        )
    if gdp_total is not None:
        parts.append(
            f"GDP 总量约 {gdp_total} 亿元（人民币，基于 Kummu et al. 2025 PPP 栅格数据换算）。"
        )
    if gdp_pc is not None:
        parts.append(f"人均 GDP 约 {gdp_pc} 万元（人民币）。")

    if multi_year and pop_growth is not None:
        parts.append(f"{first_year}–{last_year} 年人口年均增长率 {pop_growth}%。")
    if multi_year and gdp_growth is not None:
        parts.append(f"同期 GDP 年均增速 {gdp_growth}%。")

    return "".join(parts) if parts else "暂无社会经济数据。"
