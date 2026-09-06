# -*- coding: utf-8 -*-
"""依赖注入：当前登录用户"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, Vehicle
from .security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "未登录")
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "登录已失效，请重新登录")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户不存在")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "账号已被禁用，请联系管理员")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    """仅管理员可访问"""
    if user.role != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "需要管理员权限")
    return user


def get_vehicle_or_404(db: Session, vehicle_id: int, user: User) -> Vehicle:
    """获取当前用户名下车辆，不存在或非本人则 404"""
    v = db.get(Vehicle, vehicle_id)
    if v is None or v.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "车辆不存在")
    return v
