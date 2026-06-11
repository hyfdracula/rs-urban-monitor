"""Industry structure lookup helpers for report generation."""

from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger("ueea2601.report")

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_INDUSTRY_DATA: dict = {}

try:
    with open(os.path.join(_DATA_DIR, "industry_structure.json"), encoding="utf-8") as _f:
        _INDUSTRY_DATA = json.load(_f)
except Exception as e:
    logger.warning(f"Failed to load industry_structure.json: {e}")


def lookup_industry_structure(boundary_name: str) -> tuple[list[dict], bool]:
    """Return industry structure percentages and whether fallback data was used."""
    city_map = _INDUSTRY_DATA.get("city_to_province", {})
    province_data = _INDUSTRY_DATA.get("provinces", {})

    province_name = None
    name = boundary_name.strip()

    province_name = city_map.get(name)

    if not province_name and name in province_data:
        province_name = name

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

    if not province_name and len(name) >= 2:
        prefix = name[:2]
        for city, prov in city_map.items():
            if city.startswith(prefix):
                province_name = prov
                break

    prov_struct = province_data.get(province_name) if province_name else None

    if prov_struct:
        return (
            [
                {"name": "第一产业", "value": prov_struct.get("primary", 0), "color": "#69DB7C"},
                {"name": "第二产业", "value": prov_struct.get("secondary", 0), "color": "#4DABF7"},
                {"name": "第三产业", "value": prov_struct.get("tertiary", 0), "color": "#FF6B6B"},
            ],
            False,
        )

    logger.info(f"No province match for '{boundary_name}', using national average")
    return (
        [
            {"name": "第一产业", "value": 7.0, "color": "#69DB7C"},
            {"name": "第二产业", "value": 38.0, "color": "#4DABF7"},
            {"name": "第三产业", "value": 55.0, "color": "#FF6B6B"},
        ],
        True,
    )
