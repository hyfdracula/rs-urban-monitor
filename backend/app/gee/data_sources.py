"""Data-source selectors and coefficients for GEE computations."""

from __future__ import annotations

LANDSAT_SOURCES: dict[str, dict] = {
    "LT05": {
        "collection": "LANDSAT/LT05/C02/T1_L2",
        "bands": {
            "blue": "SR_B1", "green": "SR_B2", "red": "SR_B3",
            "nir": "SR_B4", "swir1": "SR_B5", "swir2": "SR_B7",
            "thermal": "ST_B6",
        },
        "sensor": "TM",
    },
    "LE07": {
        "collection": "LANDSAT/LE07/C02/T1_L2",
        "bands": {
            "blue": "SR_B1", "green": "SR_B2", "red": "SR_B3",
            "nir": "SR_B4", "swir1": "SR_B5", "swir2": "SR_B7",
            "thermal": "ST_B6",
        },
        "sensor": "ETM",
    },
    "LC08": {
        "collection": "LANDSAT/LC08/C02/T1_L2",
        "bands": {
            "blue": "SR_B2", "green": "SR_B3", "red": "SR_B4",
            "nir": "SR_B5", "swir1": "SR_B6", "swir2": "SR_B7",
            "thermal": "ST_B10",
        },
        "sensor": "OLI",
    },
    "LC09": {
        "collection": "LANDSAT/LC09/C02/T1_L2",
        "bands": {
            "blue": "SR_B2", "green": "SR_B3", "red": "SR_B4",
            "nir": "SR_B5", "swir1": "SR_B6", "swir2": "SR_B7",
            "thermal": "ST_B10",
        },
        "sensor": "OLI",
    },
}

WET_COEFFICIENTS: dict[str, dict[str, float]] = {
    "TM": {
        "blue": 0.1509, "green": 0.1973, "red": 0.3279,
        "nir": 0.3406, "swir1": -0.7112, "swir2": -0.4572,
    },
    "ETM": {
        "blue": 0.1509, "green": 0.1973, "red": 0.3279,
        "nir": 0.3406, "swir1": -0.7112, "swir2": -0.4572,
    },
    "OLI": {
        "blue": 0.3029, "green": 0.2786, "red": 0.4733,
        "nir": 0.5599, "swir1": 0.5080, "swir2": -0.1872,
    },
}


def get_landsat_source(year: int) -> tuple[str, dict, str]:
    """Select Landsat collection, band mapping, and sensor by year."""
    if year >= 2021:
        src = LANDSAT_SOURCES["LC09"]
    elif year >= 2013:
        src = LANDSAT_SOURCES["LC08"]
    elif 1999 <= year <= 2003:
        src = LANDSAT_SOURCES["LE07"]
    else:
        src = LANDSAT_SOURCES["LT05"]
    return src["collection"], src["bands"], src["sensor"]


def get_ntl_source(year: int) -> tuple[str | None, bool]:
    """Select nighttime light ImageCollection for a year."""
    if 1984 <= year <= 1991:
        return None, False
    if 1992 <= year <= 2013:
        return "NOAA/DMSP-OLS/NIGHTTIME_LIGHTS", True
    if year >= 2012:
        return "NOAA/VIIRS/DNB/ANNUAL_V21", True
    return None, False


def get_gdp_band(year: int) -> str | None:
    """Return Kummu et al. gridded GDP per-capita band name for a year."""
    if 1990 <= year <= 2022:
        return f"PPP_{year}"
    return None
