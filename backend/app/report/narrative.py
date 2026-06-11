"""Narrative text builders for analysis reports."""

from __future__ import annotations

GRADE_LABELS = {"excellent": "优", "good": "良", "moderate": "中", "poor": "较差", "bad": "差"}


def generate_conclusion(
    name: str,
    years: list[int],
    yearly: dict,
    change: dict,
    rsei_mean: float,
    rsei_grade: str,
    multi_year: bool,
) -> str:
    """Generate the overview conclusion."""
    last_year = years[-1]
    first_year = years[0]
    last = yearly.get(last_year, {})
    total_built = last.get("built_area_km2", 0)
    grade_cn = GRADE_LABELS.get(rsei_grade, "中")

    if multi_year:
        new_built = change.get("new_built_area", 0)
        exp_rate = change.get("expansion_rate", 0)
        rsei_change = change.get("rsei_change", 0)

        parts = [f"本研究对「{name}」进行了 {first_year}–{last_year} 年城市扩张与生态响应遥感监测。"]

        if new_built and new_built > 0:
            parts.append(
                f"研究区建设用地从 {first_year} 年扩张至 {last_year} 年，"
                f"新增面积 {round(new_built, 1)} km²，年均复合扩张速率 {round(exp_rate, 1)}%。"
            )
        else:
            parts.append(
                f"研究区在 {last_year} 年建设用地总面积为 {round(total_built, 1)} km²。"
            )

        change_dir = "改善" if rsei_change > 0 else "退化" if rsei_change < 0 else "稳定"
        parts.append(
            f"遥感生态指数（RSEI）均值为 {round(rsei_mean, 3)}，生态等级「{grade_cn}」，"
            f"研究期间生态质量整体呈{change_dir}趋势（ΔRSEI = {round(rsei_change, 3)}）。"
        )

        return "".join(parts)

    return (
        f"本研究对「{name}」进行了 {last_year} 年现状遥感监测。"
        f"研究区建设用地总面积为 {round(total_built, 1)} km²，"
        f"遥感生态指数（RSEI）均值为 {round(rsei_mean, 3)}，生态等级「{grade_cn}」。"
        f"由于仅分析单一年份，无法计算年际变化指标。"
    )


def generate_expansion_description(
    name: str,
    years: list[int],
    total_area: float,
    new_area: float | None,
    rate: float | None,
    multi_year: bool,
) -> str:
    """Generate expansion panel copy."""
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
    parts.append("区县排名基于各地建设用地面积从高到低排列。")
    return "".join(parts)


def generate_ecology_description(
    name: str,
    years: list[int],
    rsei_mean: float,
    rsei_grade: str,
    rsei_change: float | None,
    multi_year: bool,
) -> str:
    """Generate ecology panel copy."""
    grade_cn = GRADE_LABELS.get(rsei_grade, "中")
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
        parts.append("RSEI 四维指标（绿度/湿度/干度/热度）反映各生态因子的归一化状态。")
    else:
        parts.append("生态等级面积分布基于 RSEI 均值统计。")

    return "".join(parts)


def generate_socio_description(
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
    """Generate socioeconomic panel copy."""
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
