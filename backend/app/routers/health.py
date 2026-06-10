"""
系统状态路由
===========
P1: 健康检查 + GEE 配额查询。
"""

from __future__ import annotations

from fastapi import APIRouter, Header

from app.geoserver_service import geoserver
from app.gee_service import gee_online
from app.gee_key_service import gee_key_service
from app.database import engine
from app.config import UPLOAD_MAX_SIZE_MB, MAX_CONCURRENT_GEE_TASKS, PUBLIC_ACCOUNT_DAILY_LIMIT

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
async def system_status() -> dict:
    """系统健康检查：检查所有依赖是否在线。"""
    # PostGIS
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    # GeoServer
    gs_ok = geoserver.available

    # GEE
    gee_ok = gee_online.available

    all_ok = db_ok and gs_ok and gee_ok

    return {
        "status": "ok" if all_ok else "degraded",
        "services": {
            "database": "online" if db_ok else "offline",
            "geoserver": "online" if gs_ok else "offline",
            "gee": "online" if gee_ok else "offline",
        },
        "config": {
            "upload_max_size_mb": UPLOAD_MAX_SIZE_MB,
            "max_concurrent_gee_tasks": MAX_CONCURRENT_GEE_TASKS,
            "public_daily_limit": PUBLIC_ACCOUNT_DAILY_LIMIT,
        },
    }


@router.get("/quota")
async def get_quota(authorization: str | None = Header(None)) -> dict:
    """查询 GEE 配额。

    如果用户配置了自己的密钥，返回用户额度信息。
    否则返回公共账号额度。
    """
    user_token = None
    if authorization:
        user_token = authorization.replace("Bearer ", "").strip() or None

    # 用户自有密钥的配额
    if user_token:
        user_quota = gee_online.get_user_quota(user_token)
        if user_quota:
            return {
                "mode": "user_key",
                **user_quota,
            }

    # 公共账号配额
    public_quota = gee_online.get_public_quota()
    return {
        "mode": "public",
        **public_quota,
        "hint": "配置自己的 GEE 密钥可获取无限额度",
    }
