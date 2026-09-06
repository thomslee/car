# -*- coding: utf-8 -*-
"""保险单 CRUD"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import InsurancePolicy, User, Vehicle
from ..schemas import InsuranceIn, InsuranceOut

router = APIRouter(prefix="/api/insurance", tags=["insurance"])


@router.get("", response_model=list[InsuranceOut])
def list_insurance(
    vehicle_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    return (
        db.query(InsurancePolicy)
        .filter(InsurancePolicy.vehicle_id == vehicle_id)
        .order_by(InsurancePolicy.end_date.desc(), InsurancePolicy.id.desc())
        .all()
    )


@router.post("", response_model=InsuranceOut)
def create_insurance(body: InsuranceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, body.vehicle_id, user)
    p = InsurancePolicy(**body.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{policy_id}", response_model=InsuranceOut)
def update_insurance(policy_id: int, body: InsuranceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _get_owned(db, policy_id, user)
    for k, val in body.model_dump().items():
        setattr(p, k, val)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{policy_id}")
def delete_insurance(policy_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = _get_owned(db, policy_id, user)
    db.delete(p)
    db.commit()
    return {"ok": True}


def _get_owned(db: Session, policy_id: int, user: User) -> InsurancePolicy:
    p = db.get(InsurancePolicy, policy_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "保单不存在")
    v = db.get(Vehicle, p.vehicle_id)
    if v is None or v.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "保单不存在")
    return p
