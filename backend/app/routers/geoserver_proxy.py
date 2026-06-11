"""
GeoServer REST 代理路由
===================
前端不再直接调用 GeoServer REST API（避免凭据暴露），
改为通过后端代理转发请求。

安全：
  - 凭据只存在后端 config，前端无感知
  - 仅接受来自 localhost 的请求（Vite proxy / nginx 都在同一机器）
  - 路径白名单防止 SSRF
"""

from __future__ import annotations

import logging
import hmac
from typing import Any

import requests
from fastapi import APIRouter, Request, Response, HTTPException

from app.config import APP_ENV, GEOSERVER_URL, GEOSERVER_USER, GEOSERVER_PASS, GEOSERVER_PROXY_TOKEN

logger = logging.getLogger("ueea2601.routers.geoserver_proxy")

router = APIRouter(prefix="/api/geoserver/rest", tags=["geoserver-proxy"])

# 允许代理的 REST 路径前缀白名单
ALLOWED_PREFIXES = (
    "/workspaces/",
    "/layers/",
    "/styles/",
    "/namespaces/",
)

ALLOWED_PATHS = frozenset({
    "/workspaces.json",
    "/layers.json",
    "/styles.json",
    "/namespaces.json",
})

# 仅允许本地请求（Vite 代理或受控 nginx 反向代理都在同一机器上）
LOCALHOST_IPS = frozenset({"127.0.0.1", "::1", "0:0:0:0:0:0:0:1"})
PRODUCTION_ENVS = frozenset({"prod", "production"})
PROXY_TOKEN_HEADER = "x-geoserver-proxy-token"


def _check_path(path: str) -> None:
    """只允许白名单路径，防止 SSRF。"""
    if path not in ALLOWED_PATHS and not any(path.startswith(p) for p in ALLOWED_PREFIXES):
        raise HTTPException(status_code=403, detail=f"Path not allowed: {path}")


def _is_localhost(host: str | None) -> bool:
    return bool(host) and host in LOCALHOST_IPS


def _first_forwarded_host(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if not forwarded_for:
        return None
    return forwarded_for.split(",", 1)[0].strip()


def _has_valid_proxy_token(request: Request) -> bool:
    token = request.headers.get(PROXY_TOKEN_HEADER, "")
    return bool(GEOSERVER_PROXY_TOKEN) and hmac.compare_digest(token, GEOSERVER_PROXY_TOKEN)


def _check_local(request: Request) -> None:
    """只接受可信本机请求，防止反向代理把公网请求伪装成本机。"""
    client_host = request.client.host if request.client else None
    forwarded_host = _first_forwarded_host(request)

    if forwarded_host and not _is_localhost(forwarded_host):
        logger.warning(f"GeoServer proxy denied forwarded client {forwarded_host}")
        raise HTTPException(status_code=403, detail="Access denied: localhost only")

    if client_host and not _is_localhost(client_host):
        logger.warning(f"GeoServer proxy denied from {client_host}")
        raise HTTPException(status_code=403, detail="Access denied: localhost only")

    if APP_ENV in PRODUCTION_ENVS and not _has_valid_proxy_token(request):
        raise HTTPException(status_code=403, detail="Access denied: invalid proxy token")


@router.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"],
)
async def proxy_geoserver_rest(path: str, request: Request) -> Response:
    """代理前端 → GeoServer REST API 请求。"""
    _check_path("/" + path)
    _check_local(request)

    rest_url = f"{GEOSERVER_URL}/rest/{path}"
    auth = (GEOSERVER_USER, GEOSERVER_PASS)

    # 透传 query params
    params = dict(request.query_params)

    # 透传 headers（保留 Content-Type）
    headers = {}
    ct = request.headers.get("content-type")
    if ct:
        headers["Content-Type"] = ct
    accept = request.headers.get("accept")
    if accept:
        headers["Accept"] = accept

    body = await request.body()

    method = request.method.upper()
    logger.debug(f"GeoServer proxy: {method} /{path}")

    try:
        resp = requests.request(
            method=method,
            url=rest_url,
            auth=auth,
            headers=headers,
            params=params,
            data=body,
            timeout=120,
        )
    except requests.RequestException as e:
        logger.error(f"GeoServer proxy error: {e}")
        raise HTTPException(status_code=502, detail=f"GeoServer unreachable: {e}")

    # 透传响应
    resp_content_type = resp.headers.get("Content-Type", "application/json")
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp_content_type,
    )
