import unittest

from app.gee.data_sources import get_gdp_band, get_landsat_source, get_ntl_source
from app.report.estimators import (
    classify_ecology_change,
    classify_rsei_grade,
    estimate_change_distribution,
    get_data_sources,
)
from app.report.industry import lookup_industry_structure
from app.report.narrative import generate_conclusion


class ReportHelperTests(unittest.TestCase):
    def test_classifies_rsei_grade_boundaries(self):
        self.assertEqual(classify_rsei_grade(0.8), ("excellent", "优"))
        self.assertEqual(classify_rsei_grade(0.6), ("good", "良"))
        self.assertEqual(classify_rsei_grade(0.1), ("bad", "差"))

    def test_classifies_ecology_change_for_single_and_multi_year(self):
        self.assertEqual(classify_ecology_change(0.2, True), "明显改善")
        self.assertEqual(classify_ecology_change(-0.05, True), "轻微退化")
        self.assertEqual(classify_ecology_change(0, False), "单年份，无法判断变化方向")

    def test_estimates_change_distribution_only_for_multi_year(self):
        self.assertEqual(estimate_change_distribution({}, [2020]), [])

        result = estimate_change_distribution({
            2015: {"rsei_mean": 0.4},
            2020: {"rsei_mean": 0.5, "built_area_km2": 10},
        }, [2015, 2020])

        self.assertEqual(result[0]["name"], "明显改善")
        self.assertEqual(sum(item["area"] for item in result), 50)

    def test_infers_report_data_sources_by_year(self):
        sources = get_data_sources([2010, 2022])

        self.assertIn("Landsat 5 TM (USGS)", sources)
        self.assertIn("Landsat 9 OLI-2 (USGS)", sources)
        self.assertIn("Gridded GDP per capita (Kummu et al. 2025, PPP)", sources)

    def test_industry_lookup_falls_back_for_unknown_boundary(self):
        structure, is_mock = lookup_industry_structure("不存在测试区")

        self.assertTrue(is_mock)
        self.assertEqual([item["name"] for item in structure], ["第一产业", "第二产业", "第三产业"])

    def test_generates_single_year_conclusion(self):
        text = generate_conclusion(
            "测试区",
            [2020],
            {2020: {"built_area_km2": 12.34}},
            {},
            0.61,
            "good",
            False,
        )

        self.assertIn("2020 年现状遥感监测", text)
        self.assertIn("生态等级「良」", text)


class GeeDataSourceTests(unittest.TestCase):
    def test_selects_landsat_source_by_year(self):
        self.assertEqual(get_landsat_source(2022)[2], "OLI")
        self.assertIn("LC09", get_landsat_source(2022)[0])
        self.assertIn("LE07", get_landsat_source(2001)[0])
        self.assertIn("LT05", get_landsat_source(1995)[0])

    def test_selects_nightlight_source_availability(self):
        self.assertEqual(get_ntl_source(1990), (None, False))
        self.assertEqual(get_ntl_source(2000), ("NOAA/DMSP-OLS/NIGHTTIME_LIGHTS", True))
        self.assertEqual(get_ntl_source(2020), ("NOAA/VIIRS/DNB/ANNUAL_V21", True))

    def test_selects_gdp_band_range(self):
        self.assertEqual(get_gdp_band(1990), "PPP_1990")
        self.assertEqual(get_gdp_band(2022), "PPP_2022")
        self.assertIsNone(get_gdp_band(2023))


if __name__ == "__main__":
    unittest.main()
