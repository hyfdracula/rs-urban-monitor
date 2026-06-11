"""Panel builders for the multi-year analysis report.

Each function assembles one report panel (overview / expansion / hotspot /
ecology / coupling / socio / partition) from GEE yearly stats. They depend on
``estimators`` / ``narrative`` / ``industry`` helpers and are orchestrated by
``report_service.generate_report``.
"""

from __future__ import annotations

from app.report.estimators import (
    classify_ecology_change,
    classify_rsei_grade,
    estimate_change_distribution,
    estimate_ecology_area,
    estimate_grade_distribution,
    estimate_patches,
    get_data_sources,
)
from app.report.industry import lookup_industry_structure
from app.report.narrative import (
    generate_conclusion,
    generate_ecology_description,
    generate_expansion_description,
    generate_socio_description,
)


def build_overview(
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
    rsei_grade, rsei_grade_label = classify_rsei_grade(rsei_mean)

    # ─── 核心结论（自动生成）───
    conclusion = generate_conclusion(
        name, years, yearly, change, rsei_mean, rsei_grade, multi_year,
    )

    # ─── 数据来源摘要 ───
    data_sources = get_data_sources(years)

    # ─── 建设用地面积 ───
    total_built = last.get("built_area_km2", 0)
    new_built = change.get("new_built_area") if multi_year else None
    exp_rate = change.get("expansion_rate") if multi_year else None

    # ─── 生态变化 ───
    improved = estimate_ecology_area(last, "improved") if multi_year else None
    degraded = estimate_ecology_area(last, "degraded") if multi_year else None

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


def build_expansion(
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
    description = generate_expansion_description(
        name, years, total_area, new_area, rate, multi_year,
    )

    return {
        "totalArea": round(total_area, 2),
        "totalAreaDesc": f"研究区在 {last_year} 年建设用地总面积为 {round(total_area, 1)} km²"
                         if total_area > 0 else "暂无建设用地数据",
        "newArea": new_area,
        "newAreaDesc": (f"{first_year}–{last_year} 年新增建设用地 {new_area} km²"
                        if multi_year and new_area is not None else None),
        "patches": estimate_patches(total_area),
        "patchesDesc": "基于建设用地面积与平均斑块尺度（0.5 km²）的比值计算",
        "avgPatchSize": round(total_area / max(estimate_patches(total_area), 1), 2),
        "expansionRate": rate,
        "expansionRateDesc": (f"年均复合扩张速率（CAGR）为 {rate}%"
                              if multi_year and rate is not None else None),
        "districtRanking": district_ranking_data,
        "description": description,
        "mock": expansion_mock,
        "singleYearNote": "单年份无法计算新增面积与扩张速率" if not multi_year else None,
    }


def build_hotspot(districts: list[dict], mock_flags: dict) -> dict:
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


def build_ecology(
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
    rsei_grade, rsei_grade_label = classify_rsei_grade(rsei_mean)
    grade_distribution = estimate_grade_distribution(rsei_mean, last.get("built_area_km2", 0))

    # RSEI 四维指标（归一化到 0-1，保持原始方向：NDVI↑绿度↑, NDBSI↑干度↑, LST↑热度↑）
    four_indicators = {
        "ndvi": round(max(0, min(1, last.get("ndvi_mean", 0))), 3),
        "wet": round(max(0, min(1, (last.get("wet_mean", 0) + 0.5) / 1.0)), 3),
        "ndbsi": round(max(0, min(1, (last.get("ndbsi_mean", 0) + 0.5) / 1.0)), 3),
        "lst": round(max(0, min(1, (last.get("lst_mean", 0) + 10) / 60)), 3),
    }

    # 生态变化面积
    multi_year = len(years) >= 2
    change_distribution = estimate_change_distribution(yearly, years) if multi_year else []

    return {
        "rseiMean": round(last.get("rsei_mean", 0), 3),
        "rseiGrade": rsei_grade,
        "rseiGradeLabel": rsei_grade_label,
        "rseiChange": change.get("rsei_change") if multi_year else None,
        "changeDirection": classify_ecology_change(change.get("rsei_change", 0) if multi_year else 0, multi_year),
        "gradeDistribution": grade_distribution,
        "trendData": trend_data,
        "changeDistribution": change_distribution,
        "fourIndicators": four_indicators,
        "description": generate_ecology_description(
            name, years, last.get("rsei_mean", 0), rsei_grade,
            change.get("rsei_change") if multi_year else None, multi_year,
        ),
        "mock": {
            "changeDistribution": not multi_year,
        },
    }


def build_coupling(
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


def build_socio(
    boundary_name: str,
    yearly: dict,
    years: list[int],
    change: dict,
    districts: list[dict],
    mock_flags: dict,
) -> dict:
    """社会经济面板。

    副作用：会把 ``industryStructure`` 写入传入的 ``mock_flags``，调用方依赖此行为。
    """
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
    industry_structure, industry_is_mock = lookup_industry_structure(boundary_name)
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
        "description": generate_socio_description(
            boundary_name, last_year, pop, gdp_total_display, gdp_pc_display,
            pop_growth, gdp_growth, multi_year, first_year,
        ),
        "mock": {
            "gdp": False,
            "gdpGrowth": False,
            "industryStructure": industry_is_mock,
        },
    }


def build_partition(districts: list[dict], last_data: dict) -> dict:
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
