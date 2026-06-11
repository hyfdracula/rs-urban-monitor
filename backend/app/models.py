"""
SQLAlchemy ORM 模型
================
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func
from geoalchemy2 import Geometry

from app.database import Base


class UserBoundary(Base):
    __tablename__ = "user_boundaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    user_token = Column(String(255), nullable=False, default="anonymous", index=True)
    area_km2 = Column(Float, nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)
    compute_mode = Column(String(20), nullable=False)
    task_id = Column(String(12), nullable=False, unique=True)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    geojson_text = Column(Text, nullable=True)
    gee_code = Column(Text, nullable=True)
    gee_tasks = Column(Text, nullable=True)
    wms_urls = Column(Text, nullable=True)
    report_data = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="processing")
    years = Column(Text, nullable=True)              # JSON: [1990, 2000, 2010, 2020]
    indicators = Column(Text, nullable=True)          # JSON: ["rsei", "construction", ...]
    progress_info = Column(Text, nullable=True)      # JSON: {"year": 2010, "step": "...", "percent": 40}
    cancelled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserGEEKey(Base):
    """用户 GEE 密钥表（方案A）。"""
    __tablename__ = "user_gee_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_token = Column(String(255), nullable=False, unique=True)
    service_account = Column(String(255), nullable=False)
    encrypted_key = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="unverified")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
