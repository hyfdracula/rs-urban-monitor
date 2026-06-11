import unittest

from fastapi import HTTPException

import app.routers.geoserver_proxy as geoserver_proxy
from app.routers.geoserver_proxy import _check_path
from app.routers.geoserver_proxy import _check_local


class DummyClient:
    def __init__(self, host):
        self.host = host


class DummyHeaders(dict):
    def get(self, key, default=None):
        return super().get(key.lower(), default)


class DummyRequest:
    def __init__(self, host, headers=None):
        self.client = DummyClient(host)
        self.headers = DummyHeaders({
            str(k).lower(): v for k, v in (headers or {}).items()
        })


class GeoServerProxyTests(unittest.TestCase):
    def test_allows_collection_json_endpoints_used_by_frontend(self):
        _check_path("/workspaces.json")
        _check_path("/styles.json")

    def test_rejects_non_rest_admin_paths(self):
        with self.assertRaises(HTTPException):
            _check_path("/reload")

    def test_rejects_forwarded_external_client_even_from_local_proxy(self):
        request = DummyRequest(
            "127.0.0.1",
            {"X-Forwarded-For": "203.0.113.10, 127.0.0.1"},
        )

        with self.assertRaises(HTTPException):
            _check_local(request)

    def test_requires_proxy_token_in_production(self):
        original_env = geoserver_proxy.APP_ENV
        original_token = geoserver_proxy.GEOSERVER_PROXY_TOKEN
        geoserver_proxy.APP_ENV = "production"
        geoserver_proxy.GEOSERVER_PROXY_TOKEN = "secret"
        try:
            with self.assertRaises(HTTPException):
                _check_local(DummyRequest("127.0.0.1"))

            _check_local(
                DummyRequest(
                    "127.0.0.1",
                    {"X-GeoServer-Proxy-Token": "secret"},
                )
            )
        finally:
            geoserver_proxy.APP_ENV = original_env
            geoserver_proxy.GEOSERVER_PROXY_TOKEN = original_token


if __name__ == "__main__":
    unittest.main()
