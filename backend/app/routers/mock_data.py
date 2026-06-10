"""
27城市 Mock 数据路由
=================
原项目的固定数据接口，供前端展示地图1使用。
等真实数据入库后替换为数据库查询。
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api", tags=["mock-data"])

# ──────────────────────────────────────────────
# 27城市原始数据
# ──────────────────────────────────────────────

CITIES: list[dict[str, Any]] = [
    {"name": "上海市", "province": "上海", "newArea": 85.3, "rate": 4.5, "intensity": 0.94, "mode": "边缘扩张", "rsei": 0.48, "rseiChange": -0.10, "pop": 2487, "gdp": 47200, "center": [121.47, 31.23]},
    {"name": "南京市", "province": "江苏", "newArea": 72.1, "rate": 3.8, "intensity": 0.88, "mode": "边缘扩张", "rsei": 0.62, "rseiChange": 0.03, "pop": 942, "gdp": 16300, "center": [118.80, 32.06]},
    {"name": "杭州市", "province": "浙江", "newArea": 68.5, "rate": 4.2, "intensity": 0.91, "mode": "填充式扩张", "rsei": 0.65, "rseiChange": -0.05, "pop": 1252, "gdp": 20060, "center": [120.15, 30.28]},
    {"name": "苏州市", "province": "江苏", "newArea": 65.2, "rate": 3.6, "intensity": 0.86, "mode": "边缘扩张", "rsei": 0.52, "rseiChange": -0.08, "pop": 1291, "gdp": 24650, "center": [120.59, 31.30]},
    {"name": "无锡市", "province": "江苏", "newArea": 58.3, "rate": 3.3, "intensity": 0.82, "mode": "边缘扩张", "rsei": 0.56, "rseiChange": -0.04, "pop": 749, "gdp": 15460, "center": [120.31, 31.49]},
    {"name": "宁波市", "province": "浙江", "newArea": 55.7, "rate": 3.9, "intensity": 0.84, "mode": "填充式扩张", "rsei": 0.60, "rseiChange": -0.06, "pop": 962, "gdp": 16450, "center": [121.55, 29.87]},
    {"name": "合肥市", "province": "安徽", "newArea": 52.4, "rate": 5.1, "intensity": 0.93, "mode": "飞地式扩张", "rsei": 0.55, "rseiChange": -0.12, "pop": 963, "gdp": 12680, "center": [117.23, 31.82]},
    {"name": "北京市", "province": "北京", "newArea": 48.6, "rate": 2.1, "intensity": 0.72, "mode": "填充式扩张", "rsei": 0.35, "rseiChange": -0.15, "pop": 2189, "gdp": 43760, "center": [116.41, 39.90]},
    {"name": "天津市", "province": "天津", "newArea": 45.8, "rate": 2.8, "intensity": 0.76, "mode": "边缘扩张", "rsei": 0.38, "rseiChange": -0.11, "pop": 1373, "gdp": 16740, "center": [117.20, 39.13]},
    {"name": "广州市", "province": "广东", "newArea": 62.1, "rate": 2.0, "intensity": 0.78, "mode": "边缘扩张", "rsei": 0.40, "rseiChange": -0.09, "pop": 1881, "gdp": 30360, "center": [113.26, 23.13]},
    {"name": "深圳市", "province": "广东", "newArea": 56.9, "rate": 1.8, "intensity": 0.80, "mode": "填充式扩张", "rsei": 0.36, "rseiChange": -0.14, "pop": 1779, "gdp": 34610, "center": [114.06, 22.54]},
    {"name": "武汉市", "province": "湖北", "newArea": 53.7, "rate": 3.1, "intensity": 0.85, "mode": "边缘扩张", "rsei": 0.54, "rseiChange": -0.07, "pop": 1374, "gdp": 20010, "center": [114.30, 30.59]},
    {"name": "成都市", "province": "四川", "newArea": 59.4, "rate": 4.8, "intensity": 0.90, "mode": "飞地式扩张", "rsei": 0.58, "rseiChange": -0.08, "pop": 2140, "gdp": 22070, "center": [104.07, 30.57]},
    {"name": "重庆市", "province": "重庆", "newArea": 71.2, "rate": 4.0, "intensity": 0.87, "mode": "飞地式扩张", "rsei": 0.63, "rseiChange": -0.03, "pop": 3213, "gdp": 30150, "center": [106.55, 29.56]},
    {"name": "长沙市", "province": "湖南", "newArea": 47.3, "rate": 4.3, "intensity": 0.89, "mode": "边缘扩张", "rsei": 0.60, "rseiChange": -0.06, "pop": 1051, "gdp": 14330, "center": [112.97, 28.23]},
    {"name": "郑州市", "province": "河南", "newArea": 54.8, "rate": 5.8, "intensity": 0.95, "mode": "飞地式扩张", "rsei": 0.50, "rseiChange": -0.13, "pop": 1283, "gdp": 13620, "center": [113.63, 34.75]},
    {"name": "济南市", "province": "山东", "newArea": 44.6, "rate": 3.7, "intensity": 0.81, "mode": "边缘扩张", "rsei": 0.53, "rseiChange": -0.07, "pop": 941, "gdp": 12440, "center": [117.00, 36.67]},
    {"name": "青岛市", "province": "山东", "newArea": 49.5, "rate": 3.4, "intensity": 0.83, "mode": "边缘扩张", "rsei": 0.57, "rseiChange": -0.05, "pop": 1034, "gdp": 15760, "center": [120.38, 36.07]},
    {"name": "沈阳市", "province": "辽宁", "newArea": 38.2, "rate": 2.5, "intensity": 0.73, "mode": "填充式扩张", "rsei": 0.56, "rseiChange": -0.04, "pop": 915, "gdp": 7250, "center": [123.43, 41.80]},
    {"name": "大连市", "province": "辽宁", "newArea": 35.7, "rate": 3.0, "intensity": 0.79, "mode": "边缘扩张", "rsei": 0.61, "rseiChange": -0.02, "pop": 753, "gdp": 7830, "center": [121.61, 38.91]},
    {"name": "石家庄", "province": "河北", "newArea": 42.3, "rate": 4.1, "intensity": 0.86, "mode": "边缘扩张", "rsei": 0.55, "rseiChange": -0.09, "pop": 1121, "gdp": 7100, "center": [114.51, 38.04]},
    {"name": "太原市", "province": "山西", "newArea": 32.5, "rate": 2.2, "intensity": 0.70, "mode": "填充式扩张", "rsei": 0.44, "rseiChange": -0.10, "pop": 539, "gdp": 5130, "center": [112.55, 37.87]},
    {"name": "福州市", "province": "福建", "newArea": 40.8, "rate": 3.5, "intensity": 0.82, "mode": "边缘扩张", "rsei": 0.70, "rseiChange": -0.01, "pop": 845, "gdp": 12310, "center": [119.30, 26.07]},
    {"name": "厦门市", "province": "福建", "newArea": 36.4, "rate": 2.3, "intensity": 0.74, "mode": "填充式扩张", "rsei": 0.62, "rseiChange": -0.03, "pop": 533, "gdp": 8070, "center": [118.09, 24.48]},
    {"name": "徐州市", "province": "江苏", "newArea": 46.1, "rate": 4.5, "intensity": 0.88, "mode": "飞地式扩张", "rsei": 0.58, "rseiChange": -0.08, "pop": 902, "gdp": 8450, "center": [117.18, 34.27]},
    {"name": "唐山市", "province": "河北", "newArea": 41.7, "rate": 3.6, "intensity": 0.80, "mode": "边缘扩张", "rsei": 0.49, "rseiChange": -0.11, "pop": 772, "gdp": 8230, "center": [118.18, 39.63]},
    {"name": "芜湖市", "province": "安徽", "newArea": 33.9, "rate": 4.8, "intensity": 0.91, "mode": "飞地式扩张", "rsei": 0.59, "rseiChange": -0.09, "pop": 373, "gdp": 4560, "center": [118.43, 31.35]},
]


# ──────────────────────────────────────────────
# 1. GET /api/overview
# ──────────────────────────────────────────────

@router.get("/overview")
async def overview() -> dict:
    return {
        "totalCities": 27,
        "totalConstruction": round(sum(c["newArea"] for c in CITIES), 1),
        "avgExpansionRate": round(
            sum(c["rate"] for c in CITIES) / len(CITIES), 2
        ),
        "avgRSEI": round(
            sum(c["rsei"] for c in CITIES) / len(CITIES), 2
        ),
        "hotspotCount": 8,
        "coldspotCount": 6,
        "improvedArea": 630,
        "degradedArea": 1040,
    }


# ──────────────────────────────────────────────
# 2. GET /api/expansion
# ──────────────────────────────────────────────

@router.get("/expansion")
async def expansion() -> dict:
    total = round(sum(c["newArea"] for c in CITIES), 1)
    patches = 2340
    ranking = sorted(CITIES, key=lambda c: c["newArea"], reverse=True)[:15]
    return {
        "totalArea": total,
        "patches": patches,
        "avgPatchSize": round(total / patches, 2),
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


# ──────────────────────────────────────────────
# 3. GET /api/expansion/hotspots
# ──────────────────────────────────────────────

@router.get("/expansion/hotspots")
async def expansion_hotspots() -> list:
    return [
        {"name": "松江区", "city": "上海市", "center": [121.23, 31.03], "value": 4.2, "type": "hot"},
        {"name": "余杭区", "city": "杭州市", "center": [120.30, 30.42], "value": 3.8, "type": "hot"},
        {"name": "江宁区", "city": "南京市", "center": [118.84, 31.95], "value": 3.5, "type": "hot"},
        {"name": "蜀山区", "city": "合肥市", "center": [117.26, 31.85], "value": 3.3, "type": "hot"},
        {"name": "吴中区", "city": "苏州市", "center": [120.63, 31.26], "value": 3.1, "type": "hot"},
        {"name": "浦东新区", "city": "上海市", "center": [121.54, 31.22], "value": 2.9, "type": "hot"},
        {"name": "萧山区", "city": "杭州市", "center": [120.26, 30.18], "value": 2.7, "type": "hot"},
        {"name": "九龙坡区", "city": "重庆市", "center": [106.51, 29.50], "value": 2.5, "type": "hot"},
        {"name": "崇明区", "city": "上海市", "center": [121.40, 31.62], "value": -2.8, "type": "cold"},
        {"name": "高淳区", "city": "南京市", "center": [118.88, 31.33], "value": -2.5, "type": "cold"},
        {"name": "平山县", "city": "石家庄", "center": [114.20, 38.25], "value": -2.2, "type": "cold"},
        {"name": "阳原县", "city": "太原市", "center": [113.97, 39.85], "value": -1.9, "type": "cold"},
        {"name": "蓟州区", "city": "天津市", "center": [117.41, 40.05], "value": -1.7, "type": "cold"},
        {"name": "浏阳市", "city": "长沙市", "center": [113.64, 28.16], "value": -1.5, "type": "cold"},
    ]


# ──────────────────────────────────────────────
# 4. GET /api/ecology  (?type=ranking | ?type=radar | default)
# ──────────────────────────────────────────────

@router.get("/ecology")
async def ecology(type: str | None = Query(None)) -> Any:
    # ?type=ranking → 乡镇排名
    if type == "ranking":
        ranked = sorted(CITIES, key=lambda c: c["rsei"], reverse=True)
        return [
            {
                "rank": i + 1,
                "name": c["name"],
                "city": c["province"],
                "rsei": c["rsei"],
                "change": c["rseiChange"],
                "trend": "up" if c["rseiChange"] > 0 else "down",
            }
            for i, c in enumerate(ranked)
        ]

    # ?type=radar → 雷达图指标
    if type == "radar":
        radar_cities = CITIES[:8]
        return [
            {
                "city": c["name"],
                "ndvi": round(0.3 + c["rsei"] * 0.6, 2),
                "wet": round(0.2 + c["rsei"] * 0.5, 2),
                "ndbsi": round(0.8 - c["rsei"] * 0.5, 2),
                "lst": round(0.6 - c["rsei"] * 0.3, 2),
            }
            for c in radar_cities
        ]

    # default → 综合生态数据
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


# ──────────────────────────────────────────────
# 5. GET /api/ecology/rsei
# ──────────────────────────────────────────────

@router.get("/ecology/rsei")
async def ecology_rsei() -> dict:
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
    }


# ──────────────────────────────────────────────
# 6. GET /api/ecology/rsei-change
# ──────────────────────────────────────────────

@router.get("/ecology/rsei-change")
async def ecology_rsei_change() -> dict:
    return {
        "changeDistribution": [
            {"name": "明显改善", "area": 180, "color": "#2B8A3E"},
            {"name": "轻微改善", "area": 320, "color": "#69DB7C"},
            {"name": "基本不变", "area": 510, "color": "#FFD43B"},
            {"name": "轻微退化", "area": 280, "color": "#FF922B"},
            {"name": "明显退化", "area": 160, "color": "#FF6B6B"},
        ],
        "scatterData": [
            [c["rate"], c["rseiChange"], c["name"]]
            for c in CITIES
        ],
    }


# ──────────────────────────────────────────────
# 7. GET /api/socio
# ──────────────────────────────────────────────

@router.get("/socio")
async def socio() -> dict:
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


# ──────────────────────────────────────────────
# 8. GET /api/cities
# ──────────────────────────────────────────────

@router.get("/cities")
async def cities() -> list:
    return CITIES


# ──────────────────────────────────────────────
# 9. GET /api/report
# ──────────────────────────────────────────────

@router.get("/report")
async def report() -> dict:
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
