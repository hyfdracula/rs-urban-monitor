# RS Urban Monitor 后端镜像
# 基于 GDAL 官方镜像 —— rasterio / fiona 需要 GDAL 系统库
#
# 备选（若 GDAL 镜像过大）：
#   FROM python:3.11-slim
#   RUN apt-get update && apt-get install -y --no-install-recommends \
#       gdal-bin libgdal-dev gcc && rm -rf /var/lib/apt/lists/*
#   （rasterio/fiona 的 wheel 自带 GDAL，多数情况不需要系统库）
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.8.5

# 不写 .pyc + 实时输出日志
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    GDAL_VERSION=3.8.5

WORKDIR /app

# GDAL 镜像自带 python3，补 pip / venv
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖（利用 Docker layer 缓存）
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 再复制业务代码
COPY . .

# 非 root 用户运行（GDAL 镜像默认 root，降权提升安全）
RUN id appuser 2>/dev/null || useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

# uvicorn 直接跑 main:app，监听所有网卡
CMD ["python3", "main.py"]
