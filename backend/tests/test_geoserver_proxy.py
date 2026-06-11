import unittest

from fastapi import HTTPException

from app.routers.geoserver_proxy import _check_path


class GeoServerProxyTests(unittest.TestCase):
    def test_allows_collection_json_endpoints_used_by_frontend(self):
        _check_path("/workspaces.json")
        _check_path("/styles.json")

    def test_rejects_non_rest_admin_paths(self):
        with self.assertRaises(HTTPException):
            _check_path("/reload")


if __name__ == "__main__":
    unittest.main()
