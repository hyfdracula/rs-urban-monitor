"""Built-up area helpers for GEE computations."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("ueea2601.gee")

BUILT_NDBSI_MIN = -0.2
BUILT_NDVI_MAX = 0.5
BUILT_MNDWI_MAX = 0.3
BUILT_DW_PROB_MIN = 0.30
BUILT_GHSL_COLLECTION = "JRC/GHSL/P2023A/GHS_BUILT_S"
BUILT_GHSL_YEARS = (1975, 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2025, 2030)
BUILT_GHSL_MIN_SURFACE_M2 = 1.0


def sum_built_area(built_binary, boundary, scale: int = 30) -> float:
    """Sum binary built-up pixels in square kilometers."""
    import ee

    pixel_area = ee.Image.pixelArea().divide(1e6)
    result = built_binary.multiply(pixel_area).reduceRegion(
        ee.Reducer.sum(), boundary, scale,
        maxPixels=1e12, bestEffort=True, tileScale=4,
    ).getInfo()
    if result:
        val = result.get("built")
        if val is not None:
            return round(float(val), 2)
    return 0.0


def sum_built_surface_area(built_surface, boundary, scale: int = 100) -> float:
    """Sum GHSL built_surface values in square kilometers."""
    import ee

    result = built_surface.reduceRegion(
        ee.Reducer.sum(), boundary, scale,
        maxPixels=1e12, bestEffort=True, tileScale=4,
    ).getInfo()
    if result:
        val = result.get("built_surface")
        if val is not None:
            return round(float(val) / 1e6, 2)
    return 0.0


def get_ghsl_built(boundary, year: int):
    """Return GHSL built-up area, binary mask, and matched GHSL year."""
    import ee

    ghsl_year = min(BUILT_GHSL_YEARS, key=lambda item: abs(item - year))
    image = (
        ee.ImageCollection(BUILT_GHSL_COLLECTION)
        .filter(ee.Filter.eq("system:index", str(ghsl_year)))
        .first()
        .select("built_surface")
    )
    area = sum_built_surface_area(image, boundary, scale=100)
    built_binary = (
        image.gt(BUILT_GHSL_MIN_SURFACE_M2)
        .unmask(0)
        .toByte()
        .rename("built")
        .reproject("EPSG:4326", None, 100)
    )
    return area, built_binary, ghsl_year


def get_dynamic_world_built(boundary, year: int):
    """Return Dynamic World built probability binary mask, or None if unavailable."""
    import ee

    dw_col = (
        ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        .filterBounds(boundary)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .select("built")
    )
    count = dw_col.size().getInfo()
    if count == 0:
        logger.info(f"Dynamic World: no data for year={year}")
        return None
    dw_median = dw_col.median()
    return dw_median.gte(BUILT_DW_PROB_MIN).unmask(0).toByte().rename("built")


def compute_built_up(composite, band_map, boundary, year: int) -> tuple[float, Any]:
    """Calculate built-up area using GHSL, WorldCover, Dynamic World, and NDBI."""
    import ee

    candidates = []

    try:
        ghsl_area, ghsl_built, ghsl_year = get_ghsl_built(boundary, year)
        candidates.append(("GHSL", ghsl_area, ghsl_built))
        logger.info(f"GHSL built source year={ghsl_year} requested={year} area={ghsl_area}km²")
    except Exception as e:
        logger.warning(f"GHSL built-up failed for {year}: {e}")

    if year == 2020:
        try:
            wc = ee.Image("ESA/WorldCover/v100/2020")
            wc_built = wc.eq(50).unmask(0).toByte().rename("built")
            wc_area = sum_built_area(wc_built, boundary, scale=30)
            candidates.append(("WorldCover", wc_area, wc_built))
        except Exception as e:
            logger.warning(f"WorldCover failed for {year}: {e}")

    try:
        dw_built = get_dynamic_world_built(boundary, year)
        if dw_built is not None:
            dw_area = sum_built_area(dw_built, boundary, scale=30)
            candidates.append(("DynamicWorld", dw_area, dw_built))
    except Exception as e:
        logger.warning(f"Dynamic World failed for {year}: {e}")

    try:
        ndbsi = composite.select("NDBSI")
        ndvi_band = composite.select("NDVI")
        green = composite.select(band_map["green"]).multiply(0.0000275).add(-0.2)
        swir1 = composite.select(band_map["swir1"]).multiply(0.0000275).add(-0.2)
        mndwi = green.subtract(swir1).divide(green.add(swir1)).rename("MNDWI")
        ndbi_built = (
            ndbsi.gt(BUILT_NDBSI_MIN)
            .And(ndvi_band.lt(BUILT_NDVI_MAX))
            .And(mndwi.lt(BUILT_MNDWI_MAX))
        ).unmask(0).toByte().rename("built")
        ndbi_area = sum_built_area(ndbi_built, boundary, scale=30)
        candidates.append(("NDBI", ndbi_area, ndbi_built))
    except Exception as e:
        logger.warning(f"NDBI built-up failed for {year}: {e}")

    priority_order = ["GHSL", "WorldCover", "DynamicWorld", "NDBI"]
    if not candidates:
        logger.warning(f"built-up: all sources failed for year={year}")
        return 0.0, None

    ordered = sorted(candidates, key=lambda item: priority_order.index(item[0]))
    nonzero = [item for item in ordered if item[1] > 0]
    best = nonzero[0] if nonzero else ordered[0]

    if best[0] != "GHSL":
        for src_name, area, binary in (nonzero[1:] if nonzero else ordered[1:]):
            if best[1] > 0 and area > 0 and best[1] < area * 0.3:
                logger.warning(
                    f"built-up: {best[0]} area={best[1]} suspiciously low vs "
                    f"{src_name} area={area}, using {src_name}"
                )
                best = (src_name, area, binary)

    src_name, area, binary = best
    logger.info(
        f"built-up: source={src_name} year={year} area={area}km² "
        f"(candidates: {[(c[0], c[1]) for c in candidates]})"
    )
    return area, binary


def compute_new_built(first_built, last_built, boundary) -> Any:
    """Return pixels newly built in the last year compared with the first year."""
    if first_built is None or last_built is None:
        return None

    try:
        new_built = last_built.And(first_built.Not()).unmask(0).toByte().rename("built")
        return new_built.clip(boundary)
    except Exception as e:
        logger.warning(f"Compute new_built failed: {e}")
        return None
