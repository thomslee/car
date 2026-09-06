# -*- coding: utf-8 -*-
"""提醒扫描：保险/年检/保养到期自动生成待办"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..models import InsurancePolicy, Inspection, Reminder, User, Vehicle
from . import ai_service


def _upsert(db: Session, user_id: int, vehicle_id: int, remind_type: str, source_id: int,
            title: str, target_date, message: str, threshold_days: int):
    exists = (
        db.query(Reminder)
        .filter(
            Reminder.user_id == user_id,
            Reminder.vehicle_id == vehicle_id,
            Reminder.remind_type == remind_type,
            Reminder.source_id == source_id,
            Reminder.status == "待处理",
        )
        .first()
    )
    if exists:
        return
    db.add(
        Reminder(
            user_id=user_id,
            vehicle_id=vehicle_id,
            remind_type=remind_type,
            title=title,
            target_date=target_date,
            threshold_days=threshold_days,
            message=message,
            source_id=source_id,
            status="待处理",
        )
    )


def scan_for_user(db: Session, user: User, threshold_days: int):
    """为该用户的所有在用车辆生成/更新到期提醒"""
    today = date.today()
    vehicles = db.query(Vehicle).filter(Vehicle.user_id == user.id, Vehicle.is_active.is_(True)).all()
    for v in vehicles:
        # 保险到期
        for p in (
            db.query(InsurancePolicy)
            .filter(InsurancePolicy.vehicle_id == v.id)
            .all()
        ):
            if p.end_date:
                days_left = (p.end_date - today).days
                if 0 <= days_left <= threshold_days:
                    _upsert(
                        db, user.id, v.id, "保险", p.id,
                        f"保险到期：{p.company or '未填公司'} {p.policy_type}",
                        p.end_date,
                        f"{p.policy_type}将于 {p.end_date} 到期，剩余 {days_left} 天",
                        threshold_days,
                    )
        # 年检到期
        for ins in (
            db.query(Inspection)
            .filter(Inspection.vehicle_id == v.id)
            .all()
        ):
            if ins.expire_at:
                days_left = (ins.expire_at - today).days
                if 0 <= days_left <= threshold_days:
                    _upsert(
                        db, user.id, v.id, "年检", ins.id,
                        "年检到期",
                        ins.expire_at,
                        f"年检有效期至 {ins.expire_at}，剩余 {days_left} 天",
                        threshold_days,
                    )
        # 保养到期（基于 AI 预测）
        try:
            plan = ai_service.maintenance_plan(db, v)
            if plan.get("next_maintenance_date"):
                next_d = date.fromisoformat(plan["next_maintenance_date"])
                days_left = (next_d - today).days
                if days_left <= threshold_days:
                    item_names = "、".join(i["item_name"] for i in plan.get("due_items", [])[:5])
                    _upsert(
                        db, user.id, v.id, "保养", v.id,
                        f"保养提醒：{v.name or v.brand}",
                        next_d,
                        f"预计下次保养 {next_d}（或 {plan.get('next_maintenance_mileage')} 公里），"
                        f"建议项目：{item_names or '基础保养'}",
                        threshold_days,
                    )
        except Exception:
            pass
    db.commit()


def scan_all(db: Session):
    from ..models import Setting

    threshold = 30
    row = db.get(Setting, "reminder_threshold_days")
    if row and row.value.isdigit():
        threshold = int(row.value)
    users = db.query(User).all()
    for u in users:
        scan_for_user(db, u, threshold)
