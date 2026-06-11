"""Remote-sensing index computations for GEE images."""

from __future__ import annotations


def compute_rsei(composite, boundary):
    """Compute a simplified RSEI image from NDVI, WET, NDBSI, and LST bands."""
    import ee

    def _norm(img, band):
        s = img.select(band).reduceRegion(
            ee.Reducer.minMax(), boundary, 500, maxPixels=1e12,
            bestEffort=True, tileScale=4,
        )
        return img.select(band).subtract(ee.Number(s.get(band + "_min"))).divide(
            ee.Number(s.get(band + "_max")).subtract(ee.Number(s.get(band + "_min")))
        )

    ndvi_n = _norm(composite, "NDVI").rename("NDVI_n")
    wet_n = _norm(composite, "WET").rename("WET_n")
    ndbsi_n = ee.Image(1).subtract(_norm(composite, "NDBSI")).rename("NDBSI_n")
    lst_n = ee.Image(1).subtract(_norm(composite, "LST")).rename("LST_n")

    return (
        ndvi_n.multiply(0.4)
        .add(wet_n.multiply(0.3))
        .add(ndbsi_n.multiply(0.2))
        .add(lst_n.multiply(0.1))
        .rename("RSEI")
    )
