"""
统一配置模块
===========
所有配置集中管理，不再散落在各文件里。
"""

from __future__ import annotations

import os


APP_ENV: str = os.environ.get("APP_ENV", "development").lower()
_PRODUCTION_ENVS = {"prod", "production"}


def _config(name: str, default: str, *, production_required: bool = False) -> str:
    value = os.environ.get(name, default)
    if production_required and APP_ENV in _PRODUCTION_ENVS and value == default:
        raise RuntimeError(
            f"{name} must be set explicitly when APP_ENV={APP_ENV}; "
            "refusing to start with the development default."
        )
    return value


# ──────────────────────────────────────────────
# 数据库
# ──────────────────────────────────────────────
DATABASE_URL: str = _config(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/ueea2601",
    production_required=True,
)
DB_POOL_SIZE: int = int(os.environ.get("DB_POOL_SIZE", "5"))
DB_MAX_OVERFLOW: int = int(os.environ.get("DB_MAX_OVERFLOW", "10"))

# ──────────────────────────────────────────────
# GEE
# ──────────────────────────────────────────────
GEE_KEY_PATH: str = os.environ.get("GEE_KEY_PATH", "")
GEE_SERVICE_ACCOUNT: str = os.environ.get("GEE_SERVICE_ACCOUNT", "")
GCS_BUCKET: str = os.environ.get("GCS_BUCKET", "ueea2601-results")

# ──────────────────────────────────────────────
# GeoServer
# ──────────────────────────────────────────────
GEOSERVER_URL: str = os.environ.get("GEOSERVER_URL", "http://localhost:8080/geoserver")
GEOSERVER_USER: str = _config("GEOSERVER_USER", "admin", production_required=True)
GEOSERVER_PASS: str = _config("GEOSERVER_PASS", "geoserver", production_required=True)
GEOSERVER_WORKSPACE: str = os.environ.get("GEOSERVER_WORKSPACE", "ueea2601")
GEOSERVER_RETRY_TIMES: int = int(os.environ.get("GEOSERVER_RETRY_TIMES", "3"))
GEOSERVER_RETRY_DELAY: float = float(os.environ.get("GEOSERVER_RETRY_DELAY", "2.0"))

# ──────────────────────────────────────────────
# 上传限制
# ──────────────────────────────────────────────
UPLOAD_MAX_SIZE_MB: int = int(os.environ.get("UPLOAD_MAX_SIZE_MB", "50"))  # 50MB
UPLOAD_MAX_SIZE_BYTES: int = UPLOAD_MAX_SIZE_MB * 1024 * 1024

# ──────────────────────────────────────────────
# 并发控制
# ──────────────────────────────────────────────
MAX_CONCURRENT_GEE_TASKS: int = int(os.environ.get("MAX_CONCURRENT_GEE_TASKS", "3"))

# ──────────────────────────────────────────────
# 中国县级行政区划 GEE Asset
# ──────────────────────────────────────────────
# DataV GeoAtlas 县级区划（含中文名），上传到 GEE 后的 Asset ID。
# 格式：users/{用户名}/{asset名} 或 projects/{项目名}/assets/{asset名}
# 如果未设置，回退到 FAO/GAUL/2015/level2（地级市粒度）。
COUNTY_ASSET_ID: str = os.environ.get(
    "COUNTY_ASSET_ID", "users/9mqn4hia/china_counties"
)

# ──────────────────────────────────────────────
# 密钥加密
# ──────────────────────────────────────────────
ENCRYPTION_SECRET: str = _config(
    "ENCRYPTION_SECRET",
    "ueea2601-change-me-in-production",
    production_required=True,
)

# ──────────────────────────────────────────────
# 速率限制
# ──────────────────────────────────────────────
RATE_LIMIT_PER_MINUTE: str = os.environ.get("RATE_LIMIT_PER_MINUTE", "20")
PUBLIC_ACCOUNT_DAILY_LIMIT: int = int(os.environ.get("PUBLIC_ACCOUNT_DAILY_LIMIT", "100"))

# ──────────────────────────────────────────────
# GDP 汇率换算
# ──────────────────────────────────────────────
# Kummu et al. (2025) 数据集给出的是 PPP constant 2021 USD，
# 需要乘以转换系数才能得到人民币口径。
# 世界银行 PPP conversion factor (GDP) for China ≈ 4.2 (2021 年)。
# 如需使用名义汇率，可改为 ~7.2 (2024 年市场汇率)。
# 注意：PPP 系数更接近中国统计年鉴公布的 GDP 数值。
GDP_USD_TO_RMB: float = float(os.environ.get("GDP_USD_TO_RMB", "4.2"))

# ──────────────────────────────────────────────
# 结果目录（栅格导出临时文件）
# ──────────────────────────────────────────────
import tempfile
RESULTS_DIR: str = os.environ.get(
    "RESULTS_DIR",
    os.path.join(tempfile.gettempdir(), "ueea2601_results")
)
