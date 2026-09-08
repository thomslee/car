# -*- coding: utf-8 -*-
"""停车记录（长租车位）CRUD"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import ParkingRecord, User
from ..schemas import ParkingIn, ParkingOut

router = APIRouter(prefix="/api/parking", tags=["parking"])


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    days_in_month = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(y, m, min(d.day, days_in_month))


def _calc_end_date(start_date, duration_months):
    if start_date and duration_months:
        return _add_months(start_date, duration_months)
    return None


@router.get("", response_model=list[ParkingOut])
def list_parking(
    vehicle_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    rows = (
        db.query(ParkingRecord)
        .filter(ParkingRecord.vehicle_id == vehicle_id)
        .order_by(ParkingRecord.start_date.desc(), ParkingRecord.id.desc())
        .all()
    )
    return rows


@router.get("/{parking_id}", response_model=ParkingOut)
def get_parking(parking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(ParkingRecord, parking_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "停车记录不存在")
    get_vehicle_or_404(db, p.vehicle_id, user)
    return p


@router.post("", response_model=ParkingOut)
def create_parking(body: ParkingIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, body.vehicle_id, user)
    p = ParkingRecord(**body.model_dump())
    p.end_date = _calc_end_date(body.start_date, body.duration_months)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{parking_id}", response_model=ParkingOut)
def update_parking(parking_id: int, body: ParkingIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(ParkingRecord, parking_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "停车记录不存在")
    get_vehicle_or_404(db, p.vehicle_id, user)
    for k, val in body.model_dump().items():
        setattr(p, k, val)
    p.end_date = _calc_end_date(body.start_date, body.duration_months)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{parking_id}")
def delete_parking(parking_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(ParkingRecord, parking_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "停车记录不存在")
    get_vehicle_or_404(db, p.vehicle_id, user)
    db.delete(p)
    db.commit()
    return {"ok": True}
