"""Formatting helpers for the analysis report.

These functions build map layer configs, indicator cards, chart data and
data tables used by the legacy and multi-year report paths.
"""

from __future__ import annotations

from typing import Any


def build_map_layers(wms_urls: dict[str, str]) -> list[dict[str, Any]]:
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


def build_indicators(yearly: dict, change: dict, years: list[int]) -> list[dict]:
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


def build_charts(yearly: dict, years: list[int], districts: list[dict], change: dict) -> dict:
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


def build_table(yearly: dict, years: list[int], districts: list[dict]) -> dict:
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
