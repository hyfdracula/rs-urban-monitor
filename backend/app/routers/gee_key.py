"""
用户 GEE 密钥管理路由
==================
POST   /api/gee-key/save    - 保存密钥
POST   /api/gee-key/verify  - 验证密钥
GET    /api/gee-key/status  - 查询密钥状态
DELETE /api/gee-key         - 删除密钥
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Header

from app.gee_key_service import gee_key_service
from pydantic import BaseModel

router = APIRouter(prefix="/api/gee-key", tags=["gee-key"])


class SaveKeyRequest(BaseModel):
    service_account: str
    key_json: str


class SaveKeyResponse(BaseModel):
    success: bool
    message: str


class VerifyKeyResponse(BaseModel):
    success: bool
    status: str
    message: str


class KeyStatusResponse(BaseModel):
    has_key: bool
    status: str | None = None
    service_account: str | None = None
    verified_at: str | None = None


class DeleteKeyResponse(BaseModel):
    success: bool
    message: str


def _get_user_token(authorization: str | None) -> str:
    """从请求头获取用户 token。

    简单实现：直接用 Authorization header 的值。
    未登录时使用默认匿名用户，方便单机使用。
    """
    if not authorization:
        return "anonymous"
    return authorization.replace("Bearer ", "").strip() or "anonymous"


@router.post("/save", response_model=SaveKeyResponse)
async def save_key(
    req: SaveKeyRequest,
    authorization: str | None = Header(None),
) -> SaveKeyResponse:
    """保存用户 GEE 密钥。

    前端传 Service Account 邮箱 + 密钥 JSON 内容。
    密钥会加密存储，验证前不会使用。
    """
    user_token = _get_user_token(authorization)
    result = gee_key_service.save_key(user_token, req.service_account, req.key_json)
    return SaveKeyResponse(**result)


@router.post("/verify", response_model=VerifyKeyResponse)
async def verify_key(
    authorization: str | None = Header(None),
) -> VerifyKeyResponse:
    """验证用户 GEE 密钥是否有效。

    后端尝试用该密钥初始化 GEE，成功则标记为 valid。
    验证可能需要几秒钟。
    """
    user_token = _get_user_token(authorization)
    result = gee_key_service.verify_key(user_token)
    return VerifyKeyResponse(**result)


@router.get("/status", response_model=KeyStatusResponse)
async def get_key_status(
    authorization: str | None = Header(None),
) -> KeyStatusResponse:
    """查询用户 GEE 密钥状态。"""
    user_token = _get_user_token(authorization)
    result = gee_key_service.get_status(user_token)
    return KeyStatusResponse(**result)


@router.delete("", response_model=DeleteKeyResponse)
async def delete_key(
    authorization: str | None = Header(None),
) -> DeleteKeyResponse:
    """删除用户 GEE 密钥。"""
    user_token = _get_user_token(authorization)
    result = gee_key_service.delete_key(user_token)
    return DeleteKeyResponse(**result)
