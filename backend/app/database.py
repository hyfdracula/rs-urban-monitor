"""
数据库连接模块
===========
P0: 连接池 + 统一 session 管理。
"""

from __future__ import annotations

import logging
import json
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.config import DATABASE_URL, DB_POOL_SIZE, DB_MAX_OVERFLOW

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖注入: 获取数据库 session。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Session:
    """上下文管理器: 用于非路由代码（service 层）。"""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """启动时自动创建所有表，并对已有表补齐缺失列。

    数据库不可用时跳过（mock 接口仍可用）。
    """
    from app.models import UserBoundary, UserGEEKey  # noqa: F401
    _log = logging.getLogger("ueea2601.database")

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        _log.warning(f"数据库连接失败，跳过建表: {e}")
        return

    # 自动迁移：补齐旧表缺失的列（create_all 不会加列）
    _migrate_user_boundaries(engine, _log)
    _mark_stale_processing_tasks(engine, _log)


def _migrate_user_boundaries(eng, _log: logging.Logger) -> None:
    """为旧版 user_boundaries 表补充 ORM 中已有但建表 SQL 中缺失的列。"""
    _ALTERS = [
        "ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS area_km2 DOUBLE PRECISION",
        "ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS years TEXT",
        "ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS user_token VARCHAR(255) NOT NULL DEFAULT 'anonymous'",
        "ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS progress_info TEXT",
        "ALTER TABLE user_boundaries ADD COLUMN IF NOT EXISTS cancelled BOOLEAN DEFAULT FALSE",
    ]
    try:
        with eng.connect() as conn:
            for sql in _ALTERS:
                conn.execute(__import__("sqlalchemy").text(sql))
            conn.commit()
        _log.info("Migration OK: user_boundaries columns up-to-date")
    except Exception as e:
        _log.warning(f"Migration skipped (may not be PostgreSQL): {e}")


def _mark_stale_processing_tasks(eng, _log: logging.Logger) -> None:
    """Fail online tasks that were left processing by a previous crashed process."""
    progress = json.dumps(
        {"year": None, "step": "服务已重启，任务已中断，请重新提交", "percent": 0},
        ensure_ascii=False,
    )
    try:
        with eng.connect() as conn:
            result = conn.execute(
                __import__("sqlalchemy").text(
                    """
                    UPDATE user_boundaries
                    SET status = 'failed',
                        progress_info = :progress,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE status = 'processing'
                      AND compute_mode = 'online'
                    """
                ),
                {"progress": progress},
            )
            conn.commit()
        if result.rowcount:
            _log.warning("Marked %s stale online task(s) as failed", result.rowcount)
    except Exception as e:
        _log.warning(f"Stale task cleanup skipped: {e}")
