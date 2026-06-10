import unittest

from shapely.geometry import shape

from app.validation import normalize_to_multipolygon


class ValidationTests(unittest.TestCase):
    def test_normalize_repairs_invalid_polygon(self):
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [0, 0], [1, 1], [1, 0], [0, 1], [0, 0],
                        ]],
                    },
                }
            ],
        }

        normalized, _ = normalize_to_multipolygon(geojson)
        geom = shape(normalized)

        self.assertEqual(normalized["type"], "MultiPolygon")
        self.assertTrue(geom.is_valid)
        self.assertGreater(geom.area, 0)


if __name__ == "__main__":
    unittest.main()
