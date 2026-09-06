# -*- coding: utf-8 -*-
"""加油记录 + 油耗统计"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import RefuelRecord, User, Vehicle
from ..schemas import RefuelIn, RefuelOut
from ..services import fuel_service

router = APIRouter(prefix="/api/refuels", tags=["refuels"])


@router.get("", response_model=list[RefuelOut])
def list_refuels(
    vehicle_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    return (
        db.query(RefuelRecord)
        .filter(RefuelRecord.vehicle_id == vehicle_id)
        .order_by(RefuelRecord.refueled_at.desc(), RefuelRecord.id.desc())
        .all()
    )


@router.post("", response_model=RefuelOut)
def create_refuel(body: RefuelIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, body.vehicle_id, user)
    r = RefuelRecord(**body.model_dump())
    db.add(r)
    v = db.get(Vehicle, body.vehicle_id)
    if body.mileage and body.mileage > (v.current_mileage or 0):
        v.current_mileage = body.mileage
    db.commit()
    db.refresh(r)
    return r


@router.put("/{record_id}", response_model=RefuelOut)
def update_refuel(record_id: int, body: RefuelIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = _get_owned(db, record_id, user)
    for k, val in body.model_dump().items():
        setattr(r, k, val)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{record_id}")
def delete_refuel(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = _get_owned(db, record_id, user)
    db.delete(r)
    db.commit()
    return {"ok": True}


@router.get("/{vehicle_id}/stats")
def fuel_stats(vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, vehicle_id, user)
    return fuel_service.calc_fuel_stats(db, vehicle_id)


def _get_owned(db: Session, record_id: int, user: User) -> RefuelRecord:
    r = db.get(RefuelRecord, record_id)
    if r is None:
        from fastapi import HTTPException
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    v = db.get(Vehicle, r.vehicle_id)
    if v is None or v.user_id != user.id:
        from fastapi import HTTPException
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    return r
