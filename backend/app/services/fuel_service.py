# -*- coding: utf-8 -*-
"""油耗统计"""
from sqlalchemy.orm import Session

from ..models import RefuelRecord


def calc_fuel_stats(db: Session, vehicle_id: int):
    """基于'加满'记录计算每次百公里油耗，并按月汇总"""
    rows = (
        db.query(RefuelRecord)
        .filter(RefuelRecord.vehicle_id == vehicle_id, RefuelRecord.is_full.is_(True))
        .order_by(RefuelRecord.refueled_at, RefuelRecord.id)
        .all()
    )
    points = []  # 每次加油的油耗点
    for prev, cur in zip(rows, rows[1:]):
        if prev.mileage and cur.mileage and cur.mileage > prev.mileage and cur.fuel_amount_l:
            distance = cur.mileage - prev.mileage
            liters = float(cur.fuel_amount_l)
            l100 = liters / distance * 100
            points.append(
                {
                    "date": str(cur.refueled_at),
                    "mileage": cur.mileage,
                    "distance": distance,
                    "fuel_l": round(liters, 2),
                    "l100": round(l100, 2),
                }
            )
    # 按月平均
    monthly = {}
    for p in points:
        m = p["date"][:7]
        monthly.setdefault(m, []).append(p["l100"])
    monthly_avg = [
        {"month": m, "avg_l100": round(sum(v) / len(v), 2), "count": len(v)}
        for m, v in sorted(monthly.items())
    ]
    overall = (
        round(sum(p["l100"] for p in points) / len(points), 2) if points else None
    )
    total_cost = (
        db.query(RefuelRecord)
        .filter(RefuelRecord.vehicle_id == vehicle_id)
        .all()
    )
    cost_sum = round(sum(float(r.total_cost or 0) for r in total_cost), 2)
    total_liters = round(
        sum(float(r.fuel_amount_l or 0) for r in total_cost), 2
    )
    return {
        "points": points,
        "monthly_avg": monthly_avg,
        "overall_l100": overall,
        "total_liters": total_liters,
        "total_cost": cost_sum,
        "record_count": len(total_cost),
    }
