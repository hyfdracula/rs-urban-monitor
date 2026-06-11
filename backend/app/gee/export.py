"""
栅格导出
=========
从 gee_service.py 拆出的纯函数，负责将 ee.Image 导出为 GeoTIFF。

使用 ee.Image.getDownloadURL(format='GEO_TIFF') 同步下载。
根据预计算的边界面积自动选择合适的 scale，避免反复重试。
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Any

from app.config import RESULTS_DIR

logger = logging.getLogger("ueea2601.gee.export")

# 边界外哨兵值：unmask(-9999, False) 写入像素，但 EE 不写 GDAL NoData 标签
NODATA_VALUE = -9999


def _clip_with_nodata(img: Any, boundary: Any) -> Any:
    """裁剪影像，并把导出矩形中边界外像素填成 NoData 哨兵值。"""
    return img.clip(boundary).unmask(NODATA_VALUE, sameFootprint=False)


def _stamp_nodata(file_path: Path, nodata: int) -> None:
    """给 GeoTIFF 补打 NoData 元数据标签。

    Earth Engine 的 unmask(-9999, False) 只把边界外像素值写成 -9999，不写
    GDAL NoData 标签。GeoServer 导入时会把 -9999 当成正常像素渲染成方形色块。
    这里补打标签，让 GeoServer 自动识别哨兵值为透明像素。
    """
    import rasterio
    try:
        with rasterio.open(file_path, "r+") as ds:
            ds.nodata = nodata
    except Exception as e:
        logger.warning(f"Stamp nodata failed for {file_path}: {e}")


# 低分辨率数据源最低导出分辨率
LAYER_MIN_SCALES: dict[str, int] = {
    "built": 100,      # GHSL 100m 栅格
    "new_built": 100,  # 变化图通常由 built 二值图计算
    "gdp": 500,        # Kummu 1km 栅格
    "population": 200, # WorldPop 100m 栅格
}


def export_rasters(
    boundary,          # ee.Geometry
    boundary_id: int,
    year: int | None,  # None 表示多年份变化图（如 new_built）
    images: dict,      # {"rsei": ee.Image, "ndvi": ee.Image, "built": ee.Image}
    scale: int = 30,   # Landsat 分辨率（米）
    area_km2: float | None = None,
    progress_cb: Any = None,
    raster_idx: list[int] | None = None,
) -> dict[str, str]:
    """导出栅格为 GeoTIFF 文件。

    Args:
        boundary: ee.Geometry 边界
        boundary_id: 边界 ID（用于目录命名）
        year: 年份，None 表示变化图
        images: {layer_key: ee.Image} dict
        scale: 默认导出分辨率（米），仅小区域使用
        area_km2: 上传时预计算的边界面积（km²）
        progress_cb: 每导出一个栅格后回调
        raster_idx: mutable counter [count]，用于外部进度追踪

    Returns:
        {layer_type: file_path} dict。失败的图层不包含在返回值中。
    """
    import ee
    import requests

    # 创建输出目录
    out_dir = Path(RESULTS_DIR) / f"b{boundary_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── 根据面积计算最优 scale ──
    if area_km2 and area_km2 > 0:
        area_m2 = area_km2 * 1e6
    else:
        try:
            area_m2 = boundary.area(maxError=1).getInfo()
        except Exception:
            area_m2 = 1000 * 1e6  # fallback 1000 km²
        area_km2 = area_m2 / 1e6

    SAFE_BYTES = 35_000_000
    BYTES_PER_PIXEL = 4
    max_pixels = SAFE_BYTES // BYTES_PER_PIXEL

    band_count = max(
        img.bandNames().length().getInfo()
        for img in images.values() if img is not None
    ) if images else 1
    if band_count <= 0:
        band_count = 1
    effective_max_pixels = max_pixels // band_count
    opt_scale = max(scale, int(math.ceil(math.sqrt(area_m2 / effective_max_pixels) / 10) * 10))
    opt_scale = min(opt_scale, 2000)  # 不超过 2km

    logger.info(f"Export scale chosen: {opt_scale}m for area={area_km2:.0f}km² (bands={band_count})")

    exported: dict[str, str] = {}

    for layer_key, img in images.items():
        if img is None:
            logger.warning(f"Skip export: {layer_key} image is None")
            continue

        # 构建图层名：rsei_2020, built_2010, new_built 等
        if year is not None:
            layer_name = f"{layer_key}_{year}"
        else:
            layer_name = layer_key

        file_path = out_dir / f"{layer_name}.tif"

        # 对低分辨率数据源，提高最低导出 scale
        layer_min = LAYER_MIN_SCALES.get(layer_key, scale)
        effective_opt = max(opt_scale, layer_min)

        # clip + unmask(-9999, False): 显式填充导出矩形中边界外的像素。
        img_clipped = _clip_with_nodata(img, boundary)

        # 尝试序列：effective_opt → 2x → 4x → 1km → 2km
        scales_to_try = list(dict.fromkeys([
            effective_opt, effective_opt * 2, effective_opt * 4, 1000, 2000,
        ]))

        for try_scale in scales_to_try:
            try:
                url = img_clipped.getDownloadURL({
                    "scale": try_scale,
                    "region": boundary,
                    "format": "GEO_TIFF",
                    "name": layer_name,
                })

                logger.info(f"Exporting {layer_name} at {try_scale}m...")
                resp = requests.get(url, timeout=300)
                if resp.status_code == 200:
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                    _stamp_nodata(file_path, NODATA_VALUE)
                    exported[layer_name] = str(file_path)
                    logger.info(f"Exported: {file_path} ({len(resp.content)} bytes, {try_scale}m)")
                    if raster_idx is not None:
                        raster_idx[0] += 1
                    if progress_cb:
                        progress_cb()
                    break
                else:
                    if try_scale < scales_to_try[-1]:
                        logger.warning(f"Export {layer_name} at {try_scale}m got HTTP {resp.status_code}, retrying...")
                        continue
                    else:
                        logger.warning(f"Export {layer_name} failed: HTTP {resp.status_code}")
                        break

            except Exception as e:
                if try_scale < scales_to_try[-1]:
                    logger.warning(f"Export {layer_name} at {try_scale}m error: {e}, retrying...")
                    continue
                else:
                    logger.warning(f"Export {layer_name} failed: {e}")
                    break

        # 失败也推进进度，避免卡住
        # 注意：exported 的 key 是 layer_name（如 rsei_2020），不是 layer_key（如 rsei）
        if layer_name not in exported:
            if raster_idx is not None:
                raster_idx[0] += 1
            if progress_cb:
                progress_cb()

    return exported
