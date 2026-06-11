import unittest

from app.gee.change import compute_change, compute_change_partial


class GeeChangeTests(unittest.TestCase):
    def test_compute_change_returns_full_multi_year_metrics(self):
        result = compute_change({
            2015: {"built_area_km2": 100, "rsei_mean": 0.4, "population": 1000, "ntl_sum": 10},
            2020: {"built_area_km2": 161.05, "rsei_mean": 0.55, "population": 1100, "ntl_sum": 15},
        }, [2015, 2020])

        self.assertEqual(result["new_built_area"], 61.05)
        self.assertEqual(result["expansion_rate"], 10.0)
        self.assertEqual(result["rsei_change"], 0.15)
        self.assertEqual(result["pop_growth_rate"], 10.0)
        self.assertEqual(result["ntl_change_rate"], 50.0)

    def test_compute_change_partial_zeros_unselected_indicators(self):
        result = compute_change_partial({
            2015: {"built_area_km2": 100, "rsei_mean": 0.4, "population": 1000, "ntl_sum": 10},
            2020: {"built_area_km2": 120, "rsei_mean": 0.5, "population": 1200, "ntl_sum": 12},
        }, [2015, 2020], ["rsei"])

        self.assertEqual(result["new_built_area"], 0)
        self.assertEqual(result["expansion_rate"], 0.0)
        self.assertEqual(result["rsei_change"], 0.1)
        self.assertIsNone(result["pop_growth_rate"])
        self.assertIsNone(result["ntl_change_rate"])


if __name__ == "__main__":
    unittest.main()
