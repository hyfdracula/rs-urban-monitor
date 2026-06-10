"""
GeoServer REST API 服务
====================
P1: 重试机制。
"""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import quote

import requests

from app.config import (
    GEOSERVER_URL, GEOSERVER_USER, GEOSERVER_PASS,
    GEOSERVER_WORKSPACE, GEOSERVER_RETRY_TIMES, GEOSERVER_RETRY_DELAY,
)

logger = logging.getLogger("ueea2601.geoserver")


class GeoServerService:

    def __init__(self) -> None:
        self.base_url = f"{GEOSERVER_URL}/rest"
        self.auth = (GEOSERVER_USER, GEOSERVER_PASS)
        self.headers = {"Content-Type": "application/json"}

    def _request_with_retry(self, method: str, url: str, **kwargs) -> requests.Response:
        """带重试的 HTTP 请求。"""
        kwargs.setdefault("timeout", 30)
        last_error = None

        for attempt in range(GEOSERVER_RETRY_TIMES):
            try:
                resp = getattr(requests, method)(url, auth=self.auth, **kwargs)
                if resp.status_code in (200, 201):
                    return resp
                if resp.status_code >= 500:
                    last_error = f"Server error: {resp.status_code} — {resp.text[:200]}"
                    logger.warning(f"GeoServer retry {attempt+1}/{GEOSERVER_RETRY_TIMES}: {last_error}")
                    time.sleep(GEOSERVER_RETRY_DELAY)
                    continue
                return resp  # 4xx 不重试
            except requests.RequestException as e:
                last_error = str(e)
                logger.warning(f"GeoServer retry {attempt+1}/{GEOSERVER_RETRY_TIMES}: {e}")
                time.sleep(GEOSERVER_RETRY_DELAY)

        raise ConnectionError(f"GeoServer 请求失败（重试 {GEOSERVER_RETRY_TIMES} 次）: {last_error}")

    @property
    def available(self) -> bool:
        try:
            resp = self._request_with_retry("get", f"{self.base_url}/about/version.json")
            return resp.status_code == 200
        except Exception:
            return False

    def ensure_workspace(self) -> bool:
        resp = self._request_with_retry("get", f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}.json")
        if resp.status_code == 200:
            return True

        payload = {"workspace": {"name": GEOSERVER_WORKSPACE}}
        resp = self._request_with_retry("post", f"{self.base_url}/workspaces.json",
                                        json=payload, headers=self.headers)
        if resp.status_code in (200, 201):
            logger.info(f"Workspace '{GEOSERVER_WORKSPACE}' created")
            return True
        logger.error(f"Failed to create workspace: {resp.status_code} {resp.text}")
        return False

    def publish_geotiff(
        self,
        layer_name: str,
        file_path: str,
        title: str | None = None,
        layer_type: str | None = None,
    ) -> dict[str, Any]:
        if not self.ensure_workspace():
            return {"success": False, "layer_name": layer_name, "wms_url": None, "error": "无法创建 workspace"}

        # GeoServer names the default coverage after the coverage store.
        # Keep store and layer names aligned so REST layer/style paths and WMS URLs match.
        store_name = layer_name
        upload_url = (
            f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}"
            f"/coveragestores/{store_name}/file.geotiff"
        )

        # Clean up stale store from a previous (possibly failed) run.
        # If a corrupt store exists, PUT returns 500.
        delete_url = (
            f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}"
            f"/coveragestores/{store_name}?recurse=true"
        )
        try:
            self._request_with_retry("delete", delete_url, headers=self.headers)
        except Exception:
            pass  # store didn't exist — that's fine

        try:
            with open(file_path, "rb") as f:
                resp = self._request_with_retry(
                    "put", upload_url, data=f,
                    headers={"Content-Type": "image/tiff"}, timeout=120,
                )
        except FileNotFoundError:
            return {"success": False, "layer_name": layer_name, "wms_url": None, "error": f"文件不存在: {file_path}"}
        except ConnectionError as e:
            return {"success": False, "layer_name": layer_name, "wms_url": None, "error": str(e)}

        if resp.status_code not in (200, 201):
            return {"success": False, "layer_name": layer_name, "wms_url": None,
                    "error": f"上传失败: {resp.status_code}"}

        if title:
            self._request_with_retry(
                "put",
                f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/{store_name}/coverages/{layer_name}.json",
                json={"coverage": {"title": title}}, headers=self.headers,
            )

        # 自动应用 SLD 样式
        if layer_type:
            try:
                self._apply_sld_style(layer_name, layer_type)
            except Exception as e:
                # 样式失败不应吞掉已经发布成功的 WMS 图层。
                logger.warning(f"SLD apply failed for {layer_name} ({layer_type}): {e}")

        # 设置 coverage nullValues = -9999，让 GeoServer 把 sentinel 像素识别为 NoData
        # SLD 中 <ColorMapEntry opacity="0" quantity="-9999" /> 需要 coverage 级别配合才生效
        try:
            self._request_with_retry(
                "put",
                f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/{store_name}/coverages/{layer_name}.json",
                json={"coverage": {
                    "dimensions": {"coverageDimension": [{"name": "GreyBand", "nullValues": [-9999]}]}
                }}, headers=self.headers,
            )
        except Exception as e:
            logger.warning(f"Failed to set nullValues for {layer_name}: {e}")

        wms_url = (
            f"{GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wms"
            f"?service=WMS&version=1.1.0&request=GetMap"
            f"&layers={GEOSERVER_WORKSPACE}:{layer_name}"
            f"&styles=&width=512&height=512&srs=EPSG:4326&format=image/png&transparent=true"
        )

        logger.info(f"Published: {GEOSERVER_WORKSPACE}:{layer_name}")
        return {"success": True, "layer_name": f"{GEOSERVER_WORKSPACE}:{layer_name}",
                "wms_url": wms_url, "store_name": store_name, "error": None}

    def _apply_sld_style(self, layer_name: str, layer_type: str) -> bool:
        from app.sld_templates import get_sld
        sld_xml = get_sld(layer_type, layer_name)
        if not sld_xml:
            return False

        style_name = f"style_{layer_name}"
        encoded_style_name = quote(style_name, safe="")

        # 直接用 SLD 内容创建/更新样式，避免部分 GeoServer 版本无法用 JSON 创建 SLD 样式。
        check = self._request_with_retry("get", f"{self.base_url}/styles/{encoded_style_name}.json")
        style_headers = {"Content-Type": "application/vnd.ogc.sld+xml"}
        if check.status_code == 200:
            style_resp = self._request_with_retry(
                "put", f"{self.base_url}/styles/{encoded_style_name}",
                data=sld_xml.encode("utf-8"), headers=style_headers,
            )
        else:
            style_resp = self._request_with_retry(
                "post", f"{self.base_url}/styles?name={encoded_style_name}",
                data=sld_xml.encode("utf-8"), headers=style_headers,
            )
        if style_resp.status_code not in (200, 201):
            raise ConnectionError(f"样式上传失败: {style_resp.status_code} {style_resp.text[:200]}")

        # 绑定到图层
        bind_resp = self._request_with_retry("put",
            f"{self.base_url}/layers/{GEOSERVER_WORKSPACE}:{layer_name}.json",
            json={"layer": {"defaultStyle": {"name": style_name}}},
            headers=self.headers)
        if bind_resp.status_code not in (200, 201):
            raise ConnectionError(f"样式绑定失败: {bind_resp.status_code} {bind_resp.text[:200]}")

        logger.info(f"SLD applied: {layer_name} <- {style_name}")
        return True

    def publish_geojson(self, layer_name: str, file_path: str, title: str | None = None) -> dict[str, Any]:
        if not self.ensure_workspace():
            return {"success": False, "layer_name": layer_name, "wms_url": None, "wfs_url": None, "error": "无法创建 workspace"}

        store_name = f"{layer_name}_store"
        upload_url = f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}/datastores/{store_name}/file.geojson"

        try:
            with open(file_path, "rb") as f:
                resp = self._request_with_retry("put", upload_url, data=f,
                    headers={"Content-Type": "application/json"})
        except FileNotFoundError:
            return {"success": False, "layer_name": layer_name, "wms_url": None, "wfs_url": None, "error": f"文件不存在: {file_path}"}

        if resp.status_code not in (200, 201):
            return {"success": False, "layer_name": layer_name, "wms_url": None, "wfs_url": None, "error": f"上传失败: {resp.status_code}"}

        wms_url = f"{GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wms?service=WMS&version=1.1.0&request=GetMap&layers={GEOSERVER_WORKSPACE}:{layer_name}&styles=&width=512&height=512&srs=EPSG:4326&format=image/png"
        wfs_url = f"{GEOSERVER_URL}/{GEOSERVER_WORKSPACE}/wfs?service=WFS&version=1.0.0&request=GetFeature&typeName={GEOSERVER_WORKSPACE}:{layer_name}&outputFormat=application/json"

        return {"success": True, "layer_name": f"{GEOSERVER_WORKSPACE}:{layer_name}", "wms_url": wms_url, "wfs_url": wfs_url, "error": None}

    def delete_layer(self, layer_name: str, layer_type: str = "raster") -> bool:
        store_name = f"{layer_name}_store"
        if layer_type == "raster":
            url = f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}/coveragestores/{store_name}?recurse=true"
        else:
            url = f"{self.base_url}/workspaces/{GEOSERVER_WORKSPACE}/datastores/{store_name}?recurse=true"
        try:
            resp = self._request_with_retry("delete", url, headers=self.headers)
            return resp.status_code == 200
        except ConnectionError:
            return False


geoserver = GeoServerService()
