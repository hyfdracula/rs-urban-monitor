"""
任务追踪模块
===========
P0: 持久化到数据库，重启不丢失。
P1: 并发控制，限制同时跑的 GEE 任务数。
P2: 后台线程管理 + 取消机制。
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.database import get_db_context
from app.models import UserBoundary
from app.config import MAX_CONCURRENT_GEE_TASKS

logger = logging.getLogger("ueea2601.tasks")

# ─── 全局线程注册表 ───
_active_threads: dict[str, threading.Thread] = {}
_cancel_events: dict[str, threading.Event] = {}


class TaskStatus(str, Enum):
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


def new_task(filename: str, boundary_id: int | None = None) -> str:
    """创建新任务，返回 task_id。"""
    tid = uuid.uuid4().hex[:12]
    logger.info(f"Task created: {tid} (file={filename}, boundary={boundary_id})")
    return tid


def get_task(task_id: str) -> dict[str, Any] | None:
    """从数据库读取任务状态。"""
    with get_db_context() as db:
        boundary = db.query(UserBoundary).filter(UserBoundary.task_id == task_id).first()
        if boundary is None:
            return None

        years = json.loads(boundary.years) if boundary.years else []
        progress_info = json.loads(boundary.progress_info) if boundary.progress_info else {}

        return {
            "task_id": task_id,
            "filename": boundary.filename,
            "boundary_id": boundary.id,
            "name": boundary.name,
            "status": boundary.status,
            "compute_mode": boundary.compute_mode,
            "years": years,
            "progress": progress_info,
            "cancelled": boundary.cancelled,
            "gee_tasks": json.loads(boundary.gee_tasks) if boundary.gee_tasks else [],
            "wms_urls": json.loads(boundary.wms_urls) if boundary.wms_urls else None,
            "report_available": boundary.report_data is not None,
            "created_at": boundary.created_at.isoformat() if boundary.created_at else "",
            "updated_at": boundary.updated_at.isoformat() if boundary.updated_at else "",
        }


def update_task(task_id: str, **kwargs: Any) -> None:
    """更新任务字段到数据库。"""
    with get_db_context() as db:
        boundary = db.query(UserBoundary).filter(UserBoundary.task_id == task_id).first()
        if boundary is None:
            return

        if "status" in kwargs:
            boundary.status = kwargs["status"]
        if "gee_tasks" in kwargs:
            boundary.gee_tasks = json.dumps(kwargs["gee_tasks"]) if isinstance(kwargs["gee_tasks"], list) else kwargs["gee_tasks"]
        if "wms_urls" in kwargs:
            boundary.wms_urls = json.dumps(kwargs["wms_urls"]) if isinstance(kwargs["wms_urls"], dict) else kwargs["wms_urls"]
        if "report_data" in kwargs:
            boundary.report_data = json.dumps(kwargs["report_data"], ensure_ascii=False) if isinstance(kwargs["report_data"], dict) else kwargs["report_data"]
        if "gee_code" in kwargs:
            boundary.gee_code = kwargs["gee_code"]
        if "progress_info" in kwargs:
            boundary.progress_info = json.dumps(kwargs["progress_info"], ensure_ascii=False) if isinstance(kwargs["progress_info"], dict) else kwargs["progress_info"]
        if "cancelled" in kwargs:
            boundary.cancelled = kwargs["cancelled"]

        db.commit()


def update_progress(task_id: str, year: int | None, step: str, percent: int) -> None:
    """更新计算进度到数据库。"""
    progress_info = {"year": year, "step": step, "percent": percent}
    update_task(task_id, progress_info=progress_info)


def can_submit_gee_task() -> bool:
    """检查当前是否有空闲的 GEE 任务槽位。"""
    with get_db_context() as db:
        processing_count = db.query(UserBoundary).filter(
            UserBoundary.status == "processing",
            UserBoundary.compute_mode == "online",
        ).count()
        return processing_count < MAX_CONCURRENT_GEE_TASKS


def get_queue_position(task_id: str) -> int | None:
    """获取任务在队列中的位置（如果正在排队）。"""
    with get_db_context() as db:
        boundary = db.query(UserBoundary).filter(UserBoundary.task_id == task_id).first()
        if boundary is None or boundary.status != "processing":
            return None

        ahead = db.query(UserBoundary).filter(
            UserBoundary.status == "processing",
            UserBoundary.compute_mode == "online",
            UserBoundary.created_at < boundary.created_at,
        ).count()
        return ahead


# ─── 后台线程管理 ───


def start_background(
    task_id: str,
    target: callable,
    args: tuple = (),
) -> None:
    """启动后台线程执行 GEE 计算。"""
    cancel_event = threading.Event()
    _cancel_events[task_id] = cancel_event

    def _worker():
        try:
            target(*args, cancel_event=cancel_event)
        except Exception as e:
            logger.error(f"Background task {task_id} failed: {e}", exc_info=True)
            update_task(task_id, status="failed",
                        progress_info={"year": None, "step": f"失败: {e}", "percent": 0})
        finally:
            _active_threads.pop(task_id, None)
            _cancel_events.pop(task_id, None)

    thread = threading.Thread(target=_worker, name=f"gee-{task_id}", daemon=True)
    _active_threads[task_id] = thread
    thread.start()
    logger.info(f"Background thread started for task {task_id}")


def cancel_task(task_id: str) -> bool:
    """请求取消任务。"""
    event = _cancel_events.get(task_id)
    if event is None:
        return False
    event.set()
    update_task(task_id, cancelled=True, status="cancelled",
                progress_info={"year": None, "step": "已取消", "percent": 0})
    logger.info(f"Task {task_id} cancellation requested")
    return True


def is_cancelled(task_id: str) -> bool:
    """检查任务是否被请求取消。"""
    event = _cancel_events.get(task_id)
    return event is not None and event.is_set()
