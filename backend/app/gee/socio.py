"""Population, GDP, and nighttime-light helpers for GEE computations."""

from __future__ import annotations

import logging
from typing import Any

from app.gee.data_sources import get_gdp_band, get_ntl_source

logger = logging.getLogger("ueea2601.gee")


def get_population(boundary, year: int) -> int:
    """Estimate WorldPop population for a boundary."""
    import ee

    try:
        pop = (
            ee.ImageCollection("WorldPop/GP/100m/pop")
            .filterBounds(boundary)
            .filter(ee.Filter.eq("year", year))
            .first()
        )
        if pop:
            pop_result = pop.reduceRegion(
                ee.Reducer.sum(), boundary, 100, maxPixels=1e12,
                bestEffort=True, tileScale=4,
            ).getInfo()
            if pop_result:
                vals = list(pop_result.values())
                if vals and vals[0] is not None:
                    return round(float(vals[0]))
    except Exception as e:
        logger.warning(f"Population failed for {year}: {e}")
    return 0


def get_gdp_image_and_stats(boundary, year: int) -> tuple[float | None, Any]:
    """Extract mean Kummu et al. gridded GDP per capita and its clipped image."""
    import ee

    band_name = get_gdp_band(year)
    if not band_name:
        return None, None

    try:
        gdp_img = ee.Image(
            "projects/sat-io/open-datasets/GRIDDED_HDI_GDP/"
            "adm2_gdp_perCapita_1990_2022"
        )
        gdp_band = gdp_img.select(band_name).clip(boundary)

        stats = gdp_band.reduceRegion(
            ee.Reducer.mean(),
            boundary,
            1000,
            maxPixels=1e12,
            bestEffort=True,
            tileScale=4,
        ).getInfo()

        if stats and stats.get(band_name) is not None:
            value = float(stats[band_name])
            if value > 0:
                return round(value, 1), gdp_band.rename("GDP")
    except Exception as e:
        logger.warning(f"GDP per capita extraction failed for {year}: {e}")
    return None, None


def compute_gdp_total(gdp_image, boundary, year: int) -> float | None:
    """Compute total GDP as GDP per capita raster multiplied by population raster."""
    import ee

    try:
        pop = (
            ee.ImageCollection("WorldPop/GP/100m/pop")
            .filterBounds(boundary)
            .filter(ee.Filter.eq("year", year))
            .first()
        )
        gdp_total_img = gdp_image.multiply(pop)
        result = gdp_total_img.reduceRegion(
            ee.Reducer.sum(), boundary, 100,
            maxPixels=1e12, bestEffort=True, tileScale=4,
        ).getInfo()
        if result:
            vals = list(result.values())
            if vals and vals[0] is not None:
                return round(float(vals[0]))
    except Exception as e:
        logger.warning(f"GDP total (raster multiply) failed for {year}: {e}")
    return None


def get_gdp_per_capita(boundary, year: int) -> float | None:
    """Return only the GDP per-capita statistic."""
    value, _ = get_gdp_image_and_stats(boundary, year)
    return value


def get_ntl_sum(boundary, ntl_collection: str, year: int) -> float | None:
    """Sum nighttime light brightness for a boundary and year."""
    import ee

    try:
        ntl_img = (
            ee.ImageCollection(ntl_collection)
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .first()
        )
        if ntl_img is None:
            logger.warning(f"NTL: no image in {ntl_collection} for {year}")
            return None
        ntl_result = ntl_img.select([0]).reduceRegion(
            ee.Reducer.sum(), boundary, 1000, maxPixels=1e12,
            bestEffort=True, tileScale=4,
        ).getInfo()
        if ntl_result:
            vals = list(ntl_result.values())
            if vals and vals[0] is not None:
                return round(float(vals[0]), 2)
    except Exception as e:
        logger.warning(f"NTL failed for {ntl_collection} ({year}): {e}")
    return None


def district_population(district_geom, year: int) -> int:
    """Sum WorldPop population for a district geometry."""
    import ee

    if not (2000 <= year <= 2020):
        return 0
    try:
        wp = ee.ImageCollection("WorldPop/GP/100m/pop")\
            .filter(ee.Filter.eq("year", year)).first()
        result = wp.reduceRegion(
            ee.Reducer.sum(), district_geom, 100,
            maxPixels=1e12, bestEffort=True, tileScale=4,
        ).getInfo()
        if result:
            vals = list(result.values())
            if vals and vals[0] is not None:
                return round(float(vals[0]))
    except Exception as e:
        logger.warning(f"District population failed: {e}")
    return 0


def district_ntl(district_geom, year: int) -> float:
    """Sum nighttime lights for a district geometry."""
    import ee

    ntl_id, ntl_ok = get_ntl_source(year)
    if not ntl_ok or not ntl_id:
        return 0.0
    try:
        ntl_img = (
            ee.ImageCollection(ntl_id)
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .first()
        )
        result = ntl_img.select([0]).reduceRegion(
            ee.Reducer.sum(), district_geom, 500,
            maxPixels=1e12, bestEffort=True, tileScale=4,
        ).getInfo()
        if result:
            vals = list(result.values())
            if vals and vals[0] is not None:
                return round(float(vals[0]), 1)
    except Exception as e:
        logger.warning(f"District NTL failed: {e}")
    return 0.0
