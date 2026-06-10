"""
一次性脚本：从阿里 DataV GeoAtlas 下载全国县级行政区划 GeoJSON
================================================================

数据源：https://geo.datav.aliyun.com/areas_v3/bound/{adcode}_full.json
输出：china_counties_full.json（约 2850 条区县，含中文名 + 边界）

层级逻辑：
  - 直辖市（北京/上海/天津/重庆）：省级 features 直接是 district 级
  - 普通省份：省级 → city 级 → 再查 city_full 得到 district 级

运行方式：
    python download_county_geojson.py
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATAV_BASE_URL = "https://geo.datav.aliyun.com/areas_v3/bound"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "china_counties_full.json")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
REQUEST_DELAY = 0.3
MAX_RETRIES = 3


def fetch_datav(adcode: str, retry_count: int = 0) -> dict | None:
    """请求 DataV API，返回 JSON。失败返回 None。"""
    url = f"{DATAV_BASE_URL}/{adcode}_full.json"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # 404 说明该 adcode 没有 _full 数据（可能已经是最底层）
            return None
        if retry_count < MAX_RETRIES:
            logger.warning(f"Retry {retry_count + 1}/{MAX_RETRIES} for {adcode}: {e}")
            time.sleep(REQUEST_DELAY * 2)
            return fetch_datav(adcode, retry_count + 1)
        logger.error(f"Failed to fetch {adcode}: {e}")
        return None
    except Exception as e:
        if retry_count < MAX_RETRIES:
            logger.warning(f"Retry {retry_count + 1}/{MAX_RETRIES} for {adcode}: {e}")
            time.sleep(REQUEST_DELAY * 2)
            return fetch_datav(adcode, retry_count + 1)
        logger.error(f"Failed to fetch {adcode}: {e}")
        return None


def _add_county(
    county_feat: dict, prov_name: str, prov_adcode,
    all_counties: list, stats: dict,
    city_name: str = "", city_adcode=None,
) -> None:
    """收集一个县级要素，补充上级信息。"""
    props = county_feat.get("properties", {})
    props["province_adcode"] = prov_adcode
    props["province_name"] = prov_name
    props["city_adcode"] = city_adcode
    props["city_name"] = city_name
    county_feat["properties"] = props
    all_counties.append(county_feat)
    stats["counties"] += 1


def download_all_counties():
    """下载全国所有县级行政区划。"""
    all_counties: list[dict] = []
    stats = {"provinces": 0, "cities": 0, "counties": 0, "direct_districts": 0, "failed_cities": []}

    # 1. 获取省级列表
    logger.info("Fetching province list...")
    china_data = fetch_datav("100000")
    if not china_data:
        logger.error("Failed to fetch province list, aborting.")
        return

    provinces = china_data.get("features", [])
    stats["provinces"] = len(provinces)
    logger.info(f"Found {len(provinces)} provinces")

    # 2. 逐省处理
    for prov in provinces:
        prov_props = prov.get("properties", {})
        prov_adcode = prov_props.get("adcode")
        prov_name = prov_props.get("name", "unknown")

        logger.info(f"Processing {prov_name} ({prov_adcode})...")
        prov_data = fetch_datav(str(prov_adcode))
        if not prov_data:
            logger.warning(f"Failed to fetch {prov_name}, skipping")
            continue

        sub_features = prov_data.get("features", [])
        if not sub_features:
            logger.warning(f"  {prov_name}: no sub-features")
            continue

        # 3. 判断子要素层级
        first_level = sub_features[0].get("properties", {}).get("level", "")

        if first_level == "district":
            # ── 直辖市 / 省直管：省级直接就是区县级 ──
            for feat in sub_features:
                _add_county(
                    feat, prov_name, prov_adcode,
                    city_name=prov_name, city_adcode=prov_adcode,
                    all_counties=all_counties, stats=stats,
                )
            stats["direct_districts"] += len(sub_features)
            logger.info(f"  Direct districts: {len(sub_features)}")

        else:
            # ── 普通省份：子要素是 city 级，需要再查 ──
            stats["cities"] += len(sub_features)

            for city_feat in sub_features:
                city_props = city_feat.get("properties", {})
                city_adcode = city_props.get("adcode")
                city_name = city_props.get("name", "unknown")

                city_data = fetch_datav(str(city_adcode))
                if not city_data:
                    stats["failed_cities"].append(f"{prov_name}/{city_name}")
                    continue

                counties = city_data.get("features", [])
                for county_feat in counties:
                    _add_county(
                        county_feat, prov_name, prov_adcode,
                        city_name=city_name, city_adcode=city_adcode,
                        all_counties=all_counties, stats=stats,
                    )

                logger.info(f"  {city_name}: {len(counties)} counties")
                time.sleep(REQUEST_DELAY)

        time.sleep(REQUEST_DELAY)

    # 4. 输出
    output_geojson = {
        "type": "FeatureCollection",
        "features": all_counties,
        "metadata": {
            "source": "DataV GeoAtlas (Alibaba)",
            "download_date": datetime.now().isoformat(),
            "total_counties": len(all_counties),
            "stats": {
                "provinces": stats["provinces"],
                "cities_queried": stats["cities"],
                "direct_districts": stats["direct_districts"],
                "total_counties": stats["counties"],
                "failed_cities": stats["failed_cities"],
            },
        },
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_geojson, f, ensure_ascii=False)

    file_mb = os.path.getsize(OUTPUT_FILE) // 1024 // 1024
    logger.info(f"\n{'='*50}")
    logger.info(f"Provinces: {stats['provinces']}")
    logger.info(f"Cities queried: {stats['cities']}")
    logger.info(f"Direct districts (municipalities): {stats['direct_districts']}")
    logger.info(f"Total counties collected: {stats['counties']}")
    logger.info(f"Failed cities: {len(stats['failed_cities'])}")
    if stats["failed_cities"]:
        for fc in stats["failed_cities"][:10]:
            logger.warning(f"  - {fc}")
    logger.info(f"Output: {OUTPUT_FILE}")
    logger.info(f"File size: ~{file_mb} MB")

    return all_counties


if __name__ == "__main__":
    start_time = time.time()
    download_all_counties()
    elapsed = time.time() - start_time
    logger.info(f"Total time: {elapsed:.1f} seconds")