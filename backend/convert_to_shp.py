"""GeoJSON → Shapefile 转换（用 fiona）"""
import json
import fiona
from fiona.crs import from_epsg

GEOJSON_PATH = r"C:\Users\19161\Desktop\UEEA2601_upload\china_counties_full.json"
SHP_DIR = r"C:\Users\19161\Desktop\UEEA2601_upload\china_counties_shp"

import os
os.makedirs(SHP_DIR, exist_ok=True)

with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# 获取 schema
first_feat = data["features"][0]
props = first_feat.get("properties", {})
geom_type = first_feat.get("geometry", {}).get("type", "MultiPolygon")

schema = {
    "geometry": "MultiPolygon",
    "properties": {
        "adcode": "int",
        "name": "str",
        "level": "str",
        "province": "str",
        "city": "str",
        "prov_adcode": "int",
        "city_adcode": "int",
    },
}

shp_path = os.path.join(SHP_DIR, "china_counties.shp")
print(f"Converting {len(data['features'])} features to Shapefile...")

with fiona.open(
    shp_path, "w",
    driver="ESRI Shapefile",
    crs=from_epsg(4326),
    schema=schema,
    encoding="utf-8",
) as dst:
    for i, feat in enumerate(data["features"]):
        p = feat.get("properties", {})
        out_props = {
            "adcode": p.get("adcode", 0),
            "name": p.get("name", ""),
            "level": p.get("level", ""),
            "province": p.get("province_name", ""),
            "city": p.get("city_name", ""),
            "prov_adcode": p.get("province_adcode", 0),
            "city_adcode": p.get("city_adcode", 0),
        }
        # 统一为 MultiPolygon
        geom = feat.get("geometry")
        if geom and geom.get("type") == "Polygon":
            geom = {"type": "MultiPolygon", "coordinates": [geom["coordinates"]]}
        dst.write({
            "geometry": geom,
            "properties": out_props,
        })
        if (i + 1) % 500 == 0:
            print(f"  {i + 1}/{len(data['features'])}")

print(f"Done! Shapefile at: {SHP_DIR}")
for fn in os.listdir(SHP_DIR):
    fp = os.path.join(SHP_DIR, fn)
    print(f"  {fn}: {os.path.getsize(fp) // 1024} KB")
