"""
验证模块
=======
文件解析 + GeoJSON 验证 + 坐标系检查 + 几何类型检查。
"""

from __future__ import annotations

import json
import io
from typing import Any

import shapely.geometry
import shapely.ops
from shapely.geometry import mapping, shape
from shapely.errors import GEOSException
from fastapi import HTTPException


def parse_geojson(content: bytes) -> dict[str, Any]:
    try:
        return json.loads(content.decode("utf-8"))
    except json.JSONDecodeError as e:
        raise HTTPException(400, detail=f"文件不是有效的 JSON 格式: {e}")


def parse_shapefile(zip_bytes: bytes) -> dict[str, Any]:
    try:
        import fiona
        from fiona.io import ZipMemoryFile
    except ImportError:
        raise HTTPException(500, detail="缺少 fiona 库，无法解析 Shapefile")

    try:
        with ZipMemoryFile(io.BytesIO(zip_bytes)) as zmf:
            layers = zmf.listlayers()
            if not layers:
                raise HTTPException(400, detail="ZIP 文件中未找到 Shapefile")

            with zmf.open(layers[0]) as src:
                crs = src.crs
                if crs:
                    epsg = crs.get("init", "").replace("epsg:", "")
                    if epsg and epsg != "4326":
                        raise HTTPException(400, detail=f"坐标系必须为 WGS84 (EPSG:4326)，当前使用 EPSG:{epsg}")

                features = []
                for feat in src:
                    geom = feat.geometry
                    if geom:
                        features.append({"type": "Feature", "geometry": geom, "properties": feat.properties or {}})

                return {"type": "FeatureCollection", "features": features, "crs": crs.to_dict() if crs else None}
    except Exception as e:
        raise HTTPException(400, detail=f"无法读取 Shapefile: {e}")


def parse_geotiff(tiff_bytes: bytes) -> dict[str, Any]:
    try:
        import rasterio
        from rasterio.io import MemoryFile
    except ImportError:
        raise HTTPException(500, detail="缺少 rasterio 库，无法解析 GeoTIFF")

    try:
        with MemoryFile(tiff_bytes) as memfile:
            with memfile.open() as src:
                if src.crs:
                    epsg = src.crs.to_epsg() if hasattr(src.crs, "to_epsg") else None
                    if epsg and epsg != 4326:
                        raise HTTPException(400, detail=f"坐标系必须为 WGS84 (EPSG:4326)，当前使用 EPSG:{epsg}")

                bounds = src.bounds
                polygon = {"type": "Polygon", "coordinates": [[
                    [bounds.left, bounds.bottom], [bounds.right, bounds.bottom],
                    [bounds.right, bounds.top], [bounds.left, bounds.top],
                    [bounds.left, bounds.bottom],
                ]]}
                return {"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": polygon, "properties": {}}]}
    except Exception as e:
        raise HTTPException(400, detail=f"无法读取 GeoTIFF: {e}")


def validate_geojson_structure(geojson: dict[str, Any]) -> None:
    geo_type = geojson.get("type")
    if geo_type == "FeatureCollection":
        if not geojson.get("features"):
            raise HTTPException(400, detail="GeoJSON FeatureCollection 中没有 Feature")
    elif geo_type == "Feature":
        if not geojson.get("geometry"):
            raise HTTPException(400, detail="GeoJSON Feature 缺少 geometry 字段")
    else:
        raise HTTPException(400, detail=f"GeoJSON 类型必须是 Feature 或 FeatureCollection，当前是: {geo_type}")


def validate_geometry_type(geojson: dict[str, Any]) -> None:
    features = geojson.get("features", []) if geojson.get("type") == "FeatureCollection" else [geojson]
    for feat in features:
        geom = feat.get("geometry")
        if geom and geom.get("type") not in ("Polygon", "MultiPolygon"):
            raise HTTPException(400, detail=f"几何类型必须为 Polygon 或 MultiPolygon，检测到: {geom.get('type')}")


def normalize_to_multipolygon(geojson: dict[str, Any]) -> tuple[dict[str, Any], str]:
    features = geojson.get("features", []) if geojson.get("type") == "FeatureCollection" else [geojson]
    polygons = []
    for feat in features:
        geom = feat.get("geometry")
        if not geom:
            continue
        try:
            shp = _repair_polygonal_geometry(shape(geom))
        except Exception as e:
            raise HTTPException(400, detail=f"边界几何无效，无法解析: {e}")
        polygons.extend(_extract_polygon_parts(shp))

    if not polygons:
        raise HTTPException(400, detail="没有有效的 Polygon/MultiPolygon 几何")

    try:
        merged = shapely.ops.unary_union(polygons)
    except GEOSException:
        repaired = []
        for polygon in polygons:
            repaired.extend(_extract_polygon_parts(_repair_polygonal_geometry(polygon)))
        try:
            merged = shapely.ops.unary_union(repaired)
        except GEOSException as e:
            raise HTTPException(400, detail=f"边界几何拓扑无效，无法自动修复: {e}")

    merged = _repair_polygonal_geometry(merged)
    polygon_parts = _extract_polygon_parts(merged)
    if not polygon_parts:
        raise HTTPException(400, detail="边界几何修复后没有有效面要素")

    merged = shapely.geometry.MultiPolygon(polygon_parts)

    normalized = mapping(merged)
    normalized["type"] = "MultiPolygon"
    return normalized, json.dumps(normalized, ensure_ascii=False)


def _repair_polygonal_geometry(geom):
    if geom.is_empty:
        return geom
    if geom.is_valid:
        return geom

    try:
        repaired = shapely.make_valid(geom)
    except Exception:
        repaired = geom.buffer(0)

    if not repaired.is_valid:
        repaired = repaired.buffer(0)
    return repaired


def _extract_polygon_parts(geom) -> list:
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    if geom.geom_type == "MultiPolygon":
        return list(geom.geoms)
    if geom.geom_type == "GeometryCollection":
        parts = []
        for item in geom.geoms:
            parts.extend(_extract_polygon_parts(item))
        return parts
    return []


def validate_and_parse(content: bytes, file_ext: str) -> tuple[dict[str, Any], str, str]:
    ext = file_ext.lower()
    if ext in (".geojson", ".json"):
        geojson = parse_geojson(content)
        file_type = "geojson"
    elif ext == ".zip":
        geojson = parse_shapefile(content)
        file_type = "shapefile"
    elif ext in (".tif", ".tiff"):
        geojson = parse_geotiff(content)
        file_type = "geotiff"
    else:
        raise HTTPException(400, detail=f"不支持的文件类型: {ext}")

    validate_geojson_structure(geojson)
    if file_type != "geotiff":
        validate_geometry_type(geojson)

    normalized, geojson_str = normalize_to_multipolygon(geojson)
    return normalized, geojson_str, file_type
