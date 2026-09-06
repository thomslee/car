# -*- coding: utf-8 -*-
"""年检记录 CRUD"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import Inspection, User, Vehicle
from ..schemas import InspectionIn, InspectionOut

router = APIRouter(prefix="/api/inspections", tags=["inspections"])


@router.get("", response_model=list[InspectionOut])
def list_inspections(
    vehicle_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    return (
        db.query(Inspection)
        .filter(Inspection.vehicle_id == vehicle_id)
        .order_by(Inspection.inspected_at.desc(), Inspection.id.desc())
        .all()
    )


@router.post("", response_model=InspectionOut)
def create_inspection(body: InspectionIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, body.vehicle_id, user)
    p = Inspection(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{inspection_id}", response_model=InspectionOut)
def update_inspection(inspection_id: int, body: InspectionIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _get_owned(db, inspection_id, user)
    for k, val in body.model_dump().items():
        setattr(p, k, val)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{inspection_id}")
def delete_inspection(inspection_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _get_owned(db, inspection_id, user)
    db.delete(p)
    db.commit()
    return {"ok": True}


def _get_owned(db: Session, inspection_id: int, user: User) -> Inspection:
    p = db.get(Inspection, inspection_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    v = db.get(Vehicle, p.vehicle_id)
    if v is None or v.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "记录不存在")
    return p
