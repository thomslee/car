# -*- coding: utf-8 -*-
"""保养/维修记录（含项目明细）"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import MaintenanceItem, MaintenanceRecord, User, Vehicle
from ..schemas import MaintenanceIn, MaintenanceOut

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


@router.get("", response_model=list[MaintenanceOut])
def list_maintenance(
    vehicle_id: int = Query(...),
    record_type: str = Query(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    q = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle_id)
    if record_type:
        q = q.filter(MaintenanceRecord.record_type == record_type)
    return q.order_by(MaintenanceRecord.occurred_at.desc(), MaintenanceRecord.id.desc()).all()


@router.post("", response_model=MaintenanceOut)
def create_maintenance(body: MaintenanceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, body.vehicle_id, user)
    rec = MaintenanceRecord(
        vehicle_id=body.vehicle_id,
        occurred_at=body.occurred_at,
        mileage=body.mileage,
        shop_name=body.shop_name,
        record_type=body.record_type,
        category=body.category,
        title=body.title,
        description=body.description,
        total_cost=body.total_cost,
        invoice_no=body.invoice_no,
        warranty=body.warranty,
        notes=body.notes,
    )
    for it in body.items:
        rec.items.append(MaintenanceItem(**it.model_dump()))
    db.add(rec)
    _sync_mileage(db, rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/{record_id}", response_model=MaintenanceOut)
def get_maintenance(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_owned(db, record_id, user)


@router.put("/{record_id}", response_model=MaintenanceOut)
def update_maintenance(record_id: int, body: MaintenanceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = _get_owned(db, record_id, user)
    for k, val in body.model_dump(exclude={"items"}).items():
        setattr(rec, k, val)
    # 重建明细
    rec.items.clear()
    db.flush()
    for it in body.items:
        rec.items.append(MaintenanceItem(**it.model_dump()))
    _sync_mileage(db, rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.delete("/{record_id}")
def delete_maintenance(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = _get_owned(db, record_id, user)
    db.delete(rec)
    db.commit()
    return {"ok": True}


def _get_owned(db: Session, record_id: int, user: User) -> MaintenanceRecord:
    rec = db.get(MaintenanceRecord, record_id)
    if rec is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    v = db.get(Vehicle, rec.vehicle_id)
    if v is None or v.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    return rec


def _sync_mileage(db: Session, rec: MaintenanceRecord):
    """保养记录里程高于当前里程时更新车辆当前里程"""
    v = db.get(Vehicle, rec.vehicle_id)
    if v and rec.mileage and rec.mileage > (v.current_mileage or 0):
        v.current_mileage = rec.mileage
