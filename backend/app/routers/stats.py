# -*- coding: utf-8 -*-
"""统计报表：年度费用 / 油耗趋势 / 全局概览"""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import (
    Inspection,
    InsurancePolicy,
    MaintenanceRecord,
    RefuelRecord,
    User,
    Vehicle,
    ViolationRecord,
)
from ..services import fuel_service

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/annual-cost")
def annual_cost(
    vehicle_id: int = Query(...),
    year: int = Query(0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    y = year or date.today().year

    def in_year(d, y):
        return d is not None and d.year == y

    maintenance_total = 0.0
    repair_total = 0.0
    maintenance_monthly = {f"{m:02d}": 0.0 for m in range(1, 13)}
    for r in (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle_id)
        .all()
    ):
        if in_year(r.occurred_at, y):
            cost = float(r.total_cost or 0)
            if r.record_type == "维修":
                repair_total += cost
            else:
                maintenance_total += cost
            maintenance_monthly[f"{r.occurred_at.month:02d}"] += cost

    fuel_total = sum(
        float(r.total_cost or 0)
        for r in db.query(RefuelRecord).filter(RefuelRecord.vehicle_id == vehicle_id).all()
        if in_year(r.refueled_at, y)
    )
    insurance_total = sum(
        float(r.premium or 0)
        for r in db.query(InsurancePolicy).filter(InsurancePolicy.vehicle_id == vehicle_id).all()
        if in_year(r.start_date, y)
    )
    inspection_total = sum(
        float(r.cost or 0)
        for r in db.query(Inspection).filter(Inspection.vehicle_id == vehicle_id).all()
        if in_year(r.inspected_at, y)
    )
    violation_total = sum(
        float(r.fine or 0)
        for r in db.query(ViolationRecord).filter(ViolationRecord.vehicle_id == vehicle_id).all()
        if in_year(r.occurred_at, y)
    )

    categories = [
        {"name": "保养", "amount": round(maintenance_total, 2)},
        {"name": "维修", "amount": round(repair_total, 2)},
        {"name": "加油", "amount": round(fuel_total, 2)},
        {"name": "保险", "amount": round(insurance_total, 2)},
        {"name": "年检", "amount": round(inspection_total, 2)},
        {"name": "违章罚款", "amount": round(violation_total, 2)},
    ]
    total = round(sum(c["amount"] for c in categories), 2)
    return {
        "year": y,
        "total": total,
        "categories": categories,
        "maintenance_monthly": [
            {"month": m, "amount": round(maintenance_monthly[m], 2)} for m in sorted(maintenance_monthly)
        ],
    }


@router.get("/fuel-trend")
def fuel_trend(
    vehicle_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_vehicle_or_404(db, vehicle_id, user)
    return fuel_service.calc_fuel_stats(db, vehicle_id)


@router.get("/summary")
def global_summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).filter(Vehicle.user_id == user.id, Vehicle.is_active.is_(True)).all()
    vids = [v.id for v in vehicles]
    total_cost = 0.0
    for vid in vids:
        total_cost += sum(
            float(r.total_cost or 0)
            for r in db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vid).all()
        )
        total_cost += sum(
            float(r.total_cost or 0)
            for r in db.query(RefuelRecord).filter(RefuelRecord.vehicle_id == vid).all()
        )
    return {
        "vehicle_count": len(vehicles),
        "total_cost": round(total_cost, 2),
        "vehicles": [
            {"id": v.id, "name": v.name or v.brand, "current_mileage": v.current_mileage}
            for v in vehicles
        ],
    }
