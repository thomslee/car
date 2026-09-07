# -*- coding: utf-8 -*-
"""车辆档案 + 里程 + 车辆主页汇总"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import MaintenanceRecord, MileageRecord, Reminder, User, Vehicle
from ..schemas import MileageIn, VehicleIn, VehicleOut
from ..services import ai_service, fuel_service, remind_service

router = APIRouter(prefix="/api/vehicles", tags=["vehicles"])


def _add_months(d: date, months: int) -> date:
    """给 date 加 N 个月，处理月末溢出。"""
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    days_in_month = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(y, m, min(d.day, days_in_month))


def _calc_next_inspection_info(db: Session, v: Vehicle, today: date) -> dict | None:
    """计算下次年检：优先用手动录入的最新有效记录，否则根据注册登记日期按现行政策推算。"""
    from ..models import Inspection
    latest = (
        db.query(Inspection)
        .filter(Inspection.vehicle_id == v.id, Inspection.expire_at.isnot(None))
        .order_by(Inspection.expire_at.desc())
        .first()
    )
    if latest and latest.expire_at and latest.expire_at > today:
        days_left = (latest.expire_at - today).days
        return {
            "next_date": str(latest.expire_at),
            "inspection_type": "年检",
            "days_left": days_left,
            "source": "手动录入",
        }
    if v.registration_date:
        result = remind_service._calc_next_inspection(v.registration_date, today)
        if result:
            days_left = (result["next_date"] - today).days
            return {
                "next_date": str(result["next_date"]),
                "inspection_type": result["inspection_type"],
                "days_left": days_left,
                "source": "政策推算",
                "registration_date": str(v.registration_date),
            }
    return None


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
    # AI 保养预测（项目级，用于AI计划页）
    plan = ai_service.maintenance_plan(db, v)
    fuel = fuel_service.calc_fuel_stats(db, vehicle_id)

    # 车辆级下次保养（基于车辆保养周期，或的关系）
    interval_months = v.maint_interval_months or 12
    interval_km = v.maint_interval_km or 10000
    if last_maint:
        base_date = last_maint.occurred_at if isinstance(last_maint.occurred_at, date) else last_maint.occurred_at.date()
        base_km = last_maint.mileage or 0
    else:
        base_date = v.purchase_date if isinstance(v.purchase_date, date) else (v.purchase_date.date() if v.purchase_date else today)
        base_km = v.current_mileage or 0
    next_maint_date = _add_months(base_date, interval_months)
    next_maint_km = base_km + interval_km
    days_left = (next_maint_date - today).days
    km_left = next_maint_km - (v.current_mileage or 0)
    if days_left <= 0 or km_left <= 0:
        mt_status = "已到期"
    elif days_left <= 30 or km_left <= 1000:
        mt_status = "临期"
    else:
        mt_status = "未到期"

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
            "next_date": plan["next_maintenance"]["next_date"],
            "next_mileage": plan["next_maintenance"]["next_mileage"],
            "due_items": [i["item_name"] for i in plan["due_items"][:5]],
            "monthly_km": plan["monthly_km_estimate"],
        },
        "next_maintenance": {
            "next_date": str(next_maint_date),
            "next_mileage": next_maint_km,
            "status": mt_status,
            "days_left": days_left,
            "km_left": km_left,
            "interval_months": interval_months,
            "interval_km": interval_km,
            "last_maintenance_date": str(last_maint.occurred_at) if last_maint else None,
            "last_maintenance_mileage": last_maint.mileage if last_maint else None,
        },
        "next_inspection": _calc_next_inspection_info(db, v, today),
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
