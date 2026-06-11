"""Pure estimation and classification helpers for analysis reports."""

RSEI_GRADES = [
    (0.8, "excellent", "优"),
    (0.6, "good", "良"),
    (0.4, "moderate", "中"),
    (0.2, "poor", "较差"),
    (0.0, "bad", "差"),
]


def normalize_lst(lst_mean: float, lst_min: float = -10, lst_max: float = 50) -> float:
    """Normalize LST to 0-1, reversed so lower temperature means better ecology."""
    if lst_mean is None or lst_mean == 0:
        return 0
    normalized = (lst_mean - lst_min) / (lst_max - lst_min)
    return round(max(0, min(1, 1 - normalized)), 3)


def estimate_patches(built_area: float) -> int:
    """Estimate construction patches from built-up area and average patch size."""
    if built_area <= 0:
        return 0
    return max(1, int(built_area / 0.5))


def estimate_ecology_area(data: dict, direction: str) -> float | None:
    """Estimate improved/degraded ecology area in square kilometers."""
    built = data.get("built_area_km2", 100)
    total_area = built * 5

    if direction == "improved":
        return round(total_area * 0.15, 1)
    return round(total_area * 0.2, 1)


def estimate_grade_distribution(rsei_mean: float, built_area: float) -> list[dict]:
    """Estimate ecology grade area distribution from mean RSEI."""
    total = built_area * 5 if built_area > 0 else 1000
    rsei = max(0, min(1, rsei_mean or 0))

    excellent = 0.10 + rsei * 0.30
    good = 0.20 + rsei * 0.15
    medium = 0.30 - rsei * 0.10
    poor = 1.0 - excellent - good - medium

    return [
        {"grade": "优", "range": "0.8-1.0", "area": round(total * excellent, 1), "color": "#2B8A3E"},
        {"grade": "良", "range": "0.6-0.8", "area": round(total * good, 1), "color": "#69DB7C"},
        {"grade": "中", "range": "0.4-0.6", "area": round(total * medium, 1), "color": "#FFD43B"},
        {"grade": "差", "range": "0-0.4", "area": round(total * poor, 1), "color": "#FF6B6B"},
    ]


def estimate_change_distribution(yearly: dict, years: list[int]) -> list[dict]:
    """Estimate ecology change area distribution."""
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

    return [
        {"name": "明显改善", "area": round(total * 0.08, 1), "color": "#2B8A3E"},
        {"name": "轻微改善", "area": round(total * 0.15, 1), "color": "#69DB7C"},
        {"name": "基本不变", "area": round(total * 0.25, 1), "color": "#FFD43B"},
        {"name": "轻微退化", "area": round(total * 0.28, 1), "color": "#FF922B"},
        {"name": "明显退化", "area": round(total * 0.24, 1), "color": "#FF6B6B"},
    ]


def get_data_sources(years: list[int]) -> list[str]:
    """Infer data sources from selected years."""
    sources = set()
    for year in years:
        if year >= 2021:
            sources.add("Landsat 9 OLI-2 (USGS)")
        elif year >= 2013:
            sources.add("Landsat 8 OLI (USGS)")
        elif 1999 <= year <= 2003:
            sources.add("Landsat 7 ETM+ (USGS)")
        else:
            sources.add("Landsat 5 TM (USGS)")

        if 1975 <= year <= 2030:
            sources.add("GHSL built-up surface (JRC)")
        if year == 2020:
            sources.add("ESA WorldCover v100")
        if 2000 <= year <= 2020:
            sources.add("WorldPop Population")
        if 1992 <= year <= 2013:
            sources.add("DMSP-OLS Nighttime Light (NOAA)")
        if year >= 2012:
            sources.add("VIIRS Nighttime Light (NOAA)")
        if 1990 <= year <= 2022:
            sources.add("Gridded GDP per capita (Kummu et al. 2025, PPP)")

    return sorted(sources)


def classify_rsei_grade(rsei_mean: float) -> tuple[str, str]:
    """Return (grade_key, grade_label) from mean RSEI."""
    for threshold, key, label in RSEI_GRADES:
        if rsei_mean >= threshold:
            return key, label
    return "bad", "差"


def classify_ecology_change(rsei_change: float, multi_year: bool) -> str:
    """Return ecology change direction from RSEI delta."""
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
