"""
UEEA2601 上传功能模块 — 启动入口
=============================
直接运行此文件即可启动后端服务。

Usage:
    python main.py
"""

import logging
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import upload, boundary, compute, gee_key, health, mock_data, analysis
from app.routers.geoserver_proxy import router as geoserver_proxy_router

logger = logging.getLogger("ueea2601.main")


def _warm_geoserver() -> None:
    """后台等待 GeoServer 就绪并预建工作区，不阻塞启动。

    GeoServer 首次启动需要 2~5 分钟，backend 不应干等。
    开一个守护线程轮询，就绪后调 ensure_workspace() 把 ueea2601 工作区建好；
    即便失败，上传逻辑里也会懒加载兜底。
    """
    from app.geoserver_service import geoserver

    def _wait() -> None:
        for _ in range(90):  # 最多等 ~180 秒
            if geoserver.available:
                geoserver.ensure_workspace()
                logger.info("GeoServer ready, workspace 'ueea2601' ensured")
                return
            time.sleep(2)
        logger.warning("GeoServer not ready after 180s; will lazy-init on first upload")

    threading.Thread(target=_wait, daemon=True).start()


# ──────────────────────────────────────────────
# App
# ──────────────────────────────────────────────

app = FastAPI(
    title="UEEA2601 Upload API",
    version="1.0.0",
    description="城市扩张与生态评估 — 上传与分析后端",
)

# ──────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Startup: 初始化数据库表
# ──────────────────────────────────────────────


@app.on_event("startup")
def on_startup():
    init_db()
    _warm_geoserver()


# ──────────────────────────────────────────────
# 挂载所有路由
# ──────────────────────────────────────────────

app.include_router(upload.router)
app.include_router(boundary.router)
app.include_router(compute.router)
app.include_router(compute._alias_router)  # /api/tasks/{taskId} 别名
app.include_router(gee_key.router)
app.include_router(health.router)
app.include_router(mock_data.router)
app.include_router(analysis.router)  # GET /api/analysis/{task_id} 聚合接口
app.include_router(geoserver_proxy_router)  # GeoServer REST 代理（凭据不暴露给前端）


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
