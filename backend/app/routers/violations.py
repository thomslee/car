# -*- coding: utf-8 -*-
"""违章记录 CRUD"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import User, Vehicle, ViolationRecord
from ..schemas import ViolationIn, ViolationOut

router = APIRouter(prefix="/api/violations", tags=["violations"])


@router.get("", response_model=list[ViolationOut])
def list_violations(
    vehicle_id: int = Query(...),
    status_filter: str = Query("", alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    q = db.query(ViolationRecord).filter(ViolationRecord.vehicle_id == vehicle_id)
    if status_filter:
        q = q.filter(ViolationRecord.status == status_filter)
    return q.order_by(ViolationRecord.occurred_at.desc(), ViolationRecord.id.desc()).all()


@router.post("", response_model=ViolationOut)
def create_violation(body: ViolationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, body.vehicle_id, user)
    v = ViolationRecord(**body.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.put("/{violation_id}", response_model=ViolationOut)
def update_violation(violation_id: int, body: ViolationIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = _get_owned(db, violation_id, user)
    for k, val in body.model_dump().items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{violation_id}")
def delete_violation(violation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = _get_owned(db, violation_id, user)
    db.delete(v)
    db.commit()
    return {"ok": True}


def _get_owned(db: Session, violation_id: int, user: User) -> ViolationRecord:
    v = db.get(ViolationRecord, violation_id)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    ve = db.get(Vehicle, v.vehicle_id)
    if ve is None or ve.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    return v
