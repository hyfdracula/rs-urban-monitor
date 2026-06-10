"""
用户 GEE 密钥管理
================
P0: Fernet 加密 + get_db_context 统一管理。
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from app.database import get_db_context
from app.models import UserGEEKey
from app.config import ENCRYPTION_SECRET

logger = logging.getLogger("ueea2601.gee_key")


def _get_fernet():
    """从配置密钥派生 Fernet 密钥。"""
    from cryptography.fernet import Fernet
    key = hashlib.sha256(ENCRYPTION_SECRET.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class GEEKeyService:

    def save_key(self, user_token: str, service_account: str, key_json: str) -> dict:
        try:
            parsed = json.loads(key_json)
            if "private_key" not in parsed:
                raise HTTPException(400, detail="密钥 JSON 缺少 private_key 字段")
            if "client_email" not in parsed:
                raise HTTPException(400, detail="密钥 JSON 缺少 client_email 字段")
        except json.JSONDecodeError as e:
            raise HTTPException(400, detail=f"无效的 JSON 格式: {e}")

        if parsed["client_email"] != service_account:
            raise HTTPException(400, detail="Service Account 邮箱与密钥中的 client_email 不一致")

        fernet = _get_fernet()
        encrypted = fernet.encrypt(key_json.encode("utf-8")).decode("utf-8")

        with get_db_context() as db:
            existing = db.query(UserGEEKey).filter(
                UserGEEKey.user_token == user_token
            ).first()

            if existing:
                existing.service_account = service_account
                existing.encrypted_key = encrypted
                existing.status = "unverified"
                existing.verified_at = None
            else:
                db.add(UserGEEKey(
                    user_token=user_token,
                    service_account=service_account,
                    encrypted_key=encrypted,
                    status="unverified",
                ))

            db.commit()
            logger.info(f"GEE key saved: user={user_token}")
            return {"success": True, "message": "密钥上传成功"}

    def verify_key(self, user_token: str) -> dict:
        with get_db_context() as db:
            record = db.query(UserGEEKey).filter(
                UserGEEKey.user_token == user_token
            ).first()

            if record is None:
                raise HTTPException(404, detail="未找到密钥，请先保存")

            key_json = self._decrypt(record.encrypted_key)

            key_path = None
            try:
                import ee

                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    f.write(key_json)
                    key_path = f.name

                credentials = ee.ServiceAccountCredentials(record.service_account, key_path)
                ee.Initialize(credentials)
                test = ee.Number(1).getInfo()

                if test == 1:
                    record.status = "valid"
                    record.verified_at = datetime.now()
                    db.commit()
                    return {"success": True, "status": "valid", "message": "GEE 密钥验证成功"}

            except Exception as e:
                record.status = "invalid"
                db.commit()
                return {"success": False, "status": "invalid", "message": f"密钥无效: {e}"}
            finally:
                if key_path:
                    try:
                        os.unlink(key_path)
                    except OSError:
                        pass

            return {"success": False, "status": "invalid", "message": "验证失败"}

    def get_valid_key(self, user_token: str) -> tuple[str, str] | None:
        with get_db_context() as db:
            record = db.query(UserGEEKey).filter(
                UserGEEKey.user_token == user_token
            ).first()
            if record and record.status == "valid":
                return (record.service_account, self._decrypt(record.encrypted_key))

            return None

    def get_status(self, user_token: str) -> dict:
        with get_db_context() as db:
            record = db.query(UserGEEKey).filter(
                UserGEEKey.user_token == user_token
            ).first()

            if record is None:
                return {"has_key": False, "status": None, "service_account": None}

            return {
                "has_key": True,
                "status": record.status,
                "service_account": record.service_account,
                "verified_at": record.verified_at.isoformat() if record.verified_at else None,
            }

    def delete_key(self, user_token: str) -> dict:
        with get_db_context() as db:
            record = db.query(UserGEEKey).filter(
                UserGEEKey.user_token == user_token
            ).first()

            if record is None:
                raise HTTPException(404, detail="未找到密钥")

            db.delete(record)
            db.commit()
            return {"success": True, "message": "密钥已删除"}

    def _decrypt(self, encrypted: str) -> str:
        fernet = _get_fernet()
        return fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8")


gee_key_service = GEEKeyService()
