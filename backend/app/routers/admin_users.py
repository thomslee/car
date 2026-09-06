# -*- coding: utf-8 -*-
"""管理员：用户管理（创建账号 / 重置密码 / 角色 / 启用禁用 / 删除）"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_admin
from ..models import (
    AiAnalysis,
    Attachment,
    Inspection,
    InsurancePolicy,
    MaintenanceItem,
    MaintenanceRecord,
    MileageRecord,
    OcrTask,
    RefuelRecord,
    Reminder,
    User,
    Vehicle,
    ViolationRecord,
)
from ..schemas import AdminUserCreate, AdminUserUpdate, UserOut
from ..security import hash_password

router = APIRouter(prefix="/api/admin", tags=["admin"])

# 车辆关联的子表（删除车辆时需要清理）
_VEHICLE_CHILD_MODELS = [
    MaintenanceItem,  # 先删明细（FK 到 maintenance_records）
    MaintenanceRecord,
    RefuelRecord,
    InsurancePolicy,
    Inspection,
    ViolationRecord,
    MileageRecord,
    Attachment,
    Reminder,
    OcrTask,
    AiAnalysis,
]


@router.get("/users", response_model=list[UserOut])
def list_users(admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserOut)
def create_user(body: AdminUserCreate, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if body.role not in ("admin", "user"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "角色只能是 admin 或 user")
    exists = db.query(User).filter(User.username == body.username).first()
    if exists:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "用户名已存在")
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        display_name=body.display_name or body.username,
        role=body.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: AdminUserUpdate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    # 自我保护：管理员不能降级/禁用/删除自己
    if target.id == admin.id:
        if body.role is not None and body.role != "admin":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能降低自己的管理员权限")
        if body.is_active is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能禁用自己")
    if body.display_name is not None:
        target.display_name = body.display_name
    if body.role is not None:
        if body.role not in ("admin", "user"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "角色只能是 admin 或 user")
        target.role = body.role
    if body.is_active is not None:
        target.is_active = body.is_active
    if body.password:
        target.password_hash = hash_password(body.password)
    db.commit()
    db.refresh(target)
    return target


@router.delete("/users/{user_id}")
def delete_user(user_id: int, admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能删除自己")
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    # 级联清理该用户名下全部数据（车辆及其子表、提醒、OCR、AI 分析）
    vids = [row[0] for row in db.query(Vehicle.id).filter(Vehicle.user_id == user_id).all()]
    for vid in vids:
        rec_ids = [
            row[0]
            for row in db.query(MaintenanceRecord.id).filter(MaintenanceRecord.vehicle_id == vid).all()
        ]
        if rec_ids:
            db.query(MaintenanceItem).filter(MaintenanceItem.record_id.in_(rec_ids)).delete(synchronize_session=False)
        db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vid).delete(synchronize_session=False)
        db.query(RefuelRecord).filter(RefuelRecord.vehicle_id == vid).delete(synchronize_session=False)
        db.query(InsurancePolicy).filter(InsurancePolicy.vehicle_id == vid).delete(synchronize_session=False)
        db.query(Inspection).filter(Inspection.vehicle_id == vid).delete(synchronize_session=False)
        db.query(ViolationRecord).filter(ViolationRecord.vehicle_id == vid).delete(synchronize_session=False)
        db.query(MileageRecord).filter(MileageRecord.vehicle_id == vid).delete(synchronize_session=False)
        db.query(Attachment).filter(Attachment.vehicle_id == vid).delete(synchronize_session=False)
        db.query(Reminder).filter(Reminder.vehicle_id == vid).delete(synchronize_session=False)
        db.query(OcrTask).filter(OcrTask.vehicle_id == vid).delete(synchronize_session=False)
        db.query(AiAnalysis).filter(AiAnalysis.vehicle_id == vid).delete(synchronize_session=False)
    db.query(Vehicle).filter(Vehicle.user_id == user_id).delete(synchronize_session=False)
    db.query(Reminder).filter(Reminder.user_id == user_id).delete(synchronize_session=False)
    db.query(OcrTask).filter(OcrTask.user_id == user_id).delete(synchronize_session=False)
    db.query(AiAnalysis).filter(AiAnalysis.user_id == user_id).delete(synchronize_session=False)
    db.delete(target)
    db.commit()
    return {"message": "用户及其数据已删除"}
