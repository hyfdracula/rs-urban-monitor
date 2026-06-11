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

from datetime import datetime
from typing import Any

from app.report.estimators import get_data_sources as _get_data_sources
from app.report.formatting import (
    build_charts as _build_charts,
    build_indicators as _build_indicators,
    build_map_layers as _build_map_layers,
    build_table as _build_table,
)
from app.report.legacy import (
    build_legacy_report as _build_legacy_report,
    build_placeholder_report as _build_placeholder_report,
)
from app.report.panels import (
    build_coupling as _build_coupling,
    build_ecology as _build_ecology,
    build_expansion as _build_expansion,
    build_hotspot as _build_hotspot,
    build_overview as _build_overview,
    build_partition as _build_partition,
    build_socio as _build_socio,
)


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
