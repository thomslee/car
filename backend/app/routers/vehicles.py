# -*- coding: utf-8 -*-
"""车辆档案 + 里程 + 车辆主页汇总"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import MaintenanceRecord, MileageRecord, Reminder, User, Vehicle
from ..schemas import MileageIn, VehicleIn, VehicleOut
from ..services import ai_service, fuel_service

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
def list_vehicles(
    include_inactive: bool = Query(False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Vehicle).filter(Vehicle.user_id == user.id)
    if not include_inactive:
        q = q.filter(Vehicle.is_active.is_(True))
    return q.order_by(Vehicle.id).all()


@router.post("", response_model=VehicleOut)
def create_vehicle(body: VehicleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = Vehicle(user_id=user.id, **body.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    if body.initial_mileage:
        db.add(
            MileageRecord(
                vehicle_id=v.id,
                recorded_at=v.purchase_date or date.today(),
                mileage=body.initial_mileage,
                source="建档",
                note="购车建档里程",
            )
        )
        db.commit()
    return v


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_vehicle_or_404(db, vehicle_id, user)


@router.put("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(vehicle_id: int, body: VehicleIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_vehicle_or_404(db, vehicle_id, user)
    for k, val in body.model_dump().items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/{vehicle_id}")
def archive_vehicle(vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """归档（保留全部历史数据）"""
    v = get_vehicle_or_404(db, vehicle_id, user)
    v.is_active = False
    db.commit()
    return {"ok": True}


@router.get("/{vehicle_id}/summary")
def vehicle_summary(vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_vehicle_or_404(db, vehicle_id, user)
    today = date.today()
    # 最近保养
    last_maint = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(MaintenanceRecord.occurred_at.desc(), MaintenanceRecord.id.desc())
        .first()
    )
    # 待处理提醒
    reminders = (
        db.query(Reminder)
        .filter(Reminder.user_id == user.id, Reminder.vehicle_id == vehicle_id, Reminder.status == "待处理")
        .order_by(Reminder.target_date, Reminder.id)
        .all()
    )
    # 本年费用
    year_cost = 0.0
    for r in (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle_id)
        .all()
    ):
        if r.occurred_at and r.occurred_at.year == today.year:
            year_cost += float(r.total_cost or 0)
    # AI 保养预测
    plan = ai_service.maintenance_plan(db, v)
    fuel = fuel_service.calc_fuel_stats(db, vehicle_id)
    return {
        "vehicle": VehicleOut.model_validate(v).model_dump(),
        "current_mileage": v.current_mileage,
        "last_maintenance": {
            "date": str(last_maint.occurred_at) if last_maint else None,
            "mileage": last_maint.mileage if last_maint else None,
            "title": last_maint.title or last_maint.record_type if last_maint else None,
            "shop_name": last_maint.shop_name if last_maint else "",
        },
        "pending_reminders": [
            {
                "id": r.id,
                "remind_type": r.remind_type,
                "title": r.title,
                "target_date": str(r.target_date) if r.target_date else None,
                "message": r.message,
            }
            for r in reminders[:5]
        ],
        "year_cost": round(year_cost, 2),
        "maintenance_plan": {
            "next_date": plan["next_maintenance_date"],
            "next_mileage": plan["next_maintenance_mileage"],
            "due_items": [i["item_name"] for i in plan["due_items"][:5]],
            "monthly_km": plan["monthly_km_estimate"],
        },
        "fuel": {
            "overall_l100": fuel["overall_l100"],
            "total_cost": fuel["total_cost"],
            "record_count": fuel["record_count"],
        },
    }


# ---------- 里程打点 ----------
@router.get("/{vehicle_id}/mileage")
def list_mileage(vehicle_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_vehicle_or_404(db, vehicle_id, user)
    rows = (
        db.query(MileageRecord)
        .filter(MileageRecord.vehicle_id == vehicle_id)
        .order_by(MileageRecord.recorded_at, MileageRecord.id)
        .all()
    )
    return [
        {
            "id": r.id,
            "recorded_at": str(r.recorded_at),
            "mileage": r.mileage,
            "source": r.source,
            "note": r.note,
        }
        for r in rows
    ]


@router.post("/{vehicle_id}/mileage")
def create_mileage(vehicle_id: int, body: MileageIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    v = get_vehicle_or_404(db, vehicle_id, user)
    r = MileageRecord(vehicle_id=vehicle_id, **body.model_dump())
    db.add(r)
    if body.mileage > (v.current_mileage or 0):
        v.current_mileage = body.mileage
    db.commit()
    db.refresh(r)
    return {"ok": True, "id": r.id}
