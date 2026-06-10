"""
补丁脚本：补充遗漏的省直管市/县级市（东莞、中山、济源等）
这些城市在 DataV 没有 _full 下级页面，但自身就是县级单位。

运行方式：python patch_missing_counties.py
"""

import json
import urllib.request
import os

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
GEOJSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "china_counties_full.json")


def fetch(adcode: str, use_full: bool = False) -> dict | None:
    suffix = "_full.json" if use_full else ".json"
    url = f"https://geo.datav.aliyun.com/areas_v3/bound/{adcode}{suffix}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  Failed: {adcode} - {e}")
        return None


def main():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing = data["features"]
    existing_adcodes = {f["properties"]["adcode"] for f in existing}
    print(f"Existing counties: {len(existing)}")

    # 从 metadata 中提取失败的市
    failed = data.get("metadata", {}).get("stats", {}).get("failed_cities", [])
    print(f"Failed cities to patch: {len(failed)}")

    added = 0
    for entry in failed:
        # entry format: "广东省/东莞市" → need to get city adcode from province data
        prov_name, city_name = entry.split("/", 1)
        print(f"\n  Patching: {entry}")

        # 查找该省的 adcode
        prov_adcode = None
        for f in existing:
            p = f["properties"]
            if p.get("province_name") == prov_name:
                prov_adcode = p["province_adcode"]
                break
        if not prov_adcode:
            print(f"    Cannot find province adcode for {prov_name}, skipping")
            continue

        # 从省级数据中找到该市的 adcode
        prov_data = fetch(str(prov_adcode), use_full=True)
        if not prov_data:
            continue

        city_adcode = None
        for feat in prov_data.get("features", []):
            if feat["properties"].get("name") == city_name:
                city_adcode = feat["properties"]["adcode"]
                break

        if not city_adcode:
            print(f"    Cannot find {city_name} in province {prov_name}")
            continue

        if city_adcode in existing_adcodes:
            print(f"    Already exists: {city_name} ({city_adcode})")
            continue

        # 获取该市自身边界（不带 _full）
        city_data = fetch(str(city_adcode))
        if not city_data:
            continue

        for feat in city_data.get("features", []):
            props = feat["properties"]
            if props.get("adcode") not in existing_adcodes:
                props["province_adcode"] = prov_adcode
                props["province_name"] = prov_name
                props["city_adcode"] = city_adcode
                props["city_name"] = city_name
                feat["properties"] = props
                existing.append(feat)
                existing_adcodes.add(props["adcode"])
                added += 1
                print(f"    Added: {city_name} ({city_adcode})")

    # 更新 metadata
    data["metadata"]["stats"]["total_counties"] = len(existing)
    data["metadata"]["stats"]["patched_counties"] = added
    data["metadata"]["stats"]["failed_cities"] = []

    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(f"\n=== Patch complete ===")
    print(f"Added: {added}")
    print(f"Total counties now: {len(existing)}")


if __name__ == "__main__":
    main()