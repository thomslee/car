# -*- coding: utf-8 -*-
"""AI 分析 + 大模型配置管理"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import AiProvider, User
from ..schemas import MaintenancePlanIn, PriceEstimateIn, ProviderIn, ProviderOut
from ..services import ai_service

router = APIRouter(prefix="/api/ai", tags=["ai"])


# ---------- 分析 ----------
@router.post("/maintenance-plan")
def maintenance_plan(body: MaintenancePlanIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_vehicle_or_404(db, body.vehicle_id, user)
    plan = ai_service.maintenance_plan(db, v)
    narration = ai_service.narrate(db, plan=plan)
    return {**plan, "narration": narration}


@router.post("/over-maintenance")
def over_maintenance(body: MaintenancePlanIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_vehicle_or_404(db, body.vehicle_id, user)
    over = ai_service.over_maintenance(db, v)
    narration = ai_service.narrate(db, over=over)
    return {**over, "narration": narration}


@router.post("/price-estimate")
def price_estimate(body: PriceEstimateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_vehicle_or_404(db, body.vehicle_id, user)
    price = ai_service.price_estimate(db, v, body.items)
    narration = ai_service.narrate(db, price=price)
    return {**price, "narration": narration}


@router.post("/health-report")
def health_report(body: MaintenancePlanIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_vehicle_or_404(db, body.vehicle_id, user)
    report = ai_service.health_report(db, v)
    plan = ai_service.maintenance_plan(db, v)
    over = ai_service.over_maintenance(db, v)
    narration = ai_service.narrate(db, plan=plan, over=over)
    return {**report, "narration": narration}


# ---------- 大模型配置 ----------
@router.get("/providers", response_model=list[ProviderOut])
def list_providers(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(AiProvider).order_by(AiProvider.id).all()


@router.post("/providers", response_model=ProviderOut)
def create_provider(body: ProviderIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = AiProvider(**body.model_dump())
    if p.is_default:
        _clear_default(db)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/providers/{provider_id}", response_model=ProviderOut)
def update_provider(provider_id: int, body: ProviderIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(AiProvider, provider_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "配置不存在")
    if body.is_default and not p.is_default:
        _clear_default(db)
    for k, val in body.model_dump().items():
        setattr(p, k, val)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/providers/{provider_id}")
def delete_provider(provider_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = db.get(AiProvider, provider_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "配置不存在")
    db.delete(p)
    db.commit()
    return {"ok": True}


def _clear_default(db: Session):
    for p in db.query(AiProvider).filter(AiProvider.is_default.is_(True)).all():
        p.is_default = False
