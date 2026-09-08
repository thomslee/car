# -*- coding: utf-8 -*-
"""提醒扫描：保险/年检/保养到期自动生成待办"""
from datetime import date, timedelta

from sqlalchemy.orm import Session

from ..models import InsurancePolicy, Inspection, MaintenanceRecord, ParkingRecord, Reminder, User, Vehicle
from . import ai_service


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    days_in_month = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return date(y, m, min(d.day, days_in_month))


def _calc_next_inspection(reg_date: date, today: date) -> dict | None:
    """根据注册登记日期推算下一次年检（非营运小微型客车，2022年10月政策）。
    第2、4、8年免检申领标志，第6、10年上线检测，10年以上每年上线检测。"""
    if not reg_date:
        return None
    milestones = [2, 4, 6, 8, 10]
    online_years = {6, 10}
    for years in milestones:
        due_date = _add_months(reg_date, years * 12)
        if due_date > today:
            inspection_type = "上线检测" if years in online_years else "免检申领标志"
            return {"next_date": due_date, "inspection_type": inspection_type, "years": years}
    # 超过10年，每年一次
    next_years = 11
    due_date = _add_months(reg_date, next_years * 12)
    while due_date <= today:
        next_years += 1
        due_date = _add_months(reg_date, next_years * 12)
    return {"next_date": due_date, "inspection_type": "上线检测", "years": next_years}


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
        # 保险到期（同一辆车只推一个提醒，取最早到期的保单；交强险和商业险一起办时合并提醒）
        policies = (
            db.query(InsurancePolicy)
            .filter(InsurancePolicy.vehicle_id == v.id)
            .all()
        )
        active_policies = [p for p in policies if p.end_date]
        if active_policies:
            earliest = min(active_policies, key=lambda p: p.end_date)
            days_left = (earliest.end_date - today).days
            if 0 <= days_left <= threshold_days:
                # 清理旧的保单级提醒（source_id为保单id），避免重复
                db.query(Reminder).filter(
                    Reminder.user_id == user.id,
                    Reminder.vehicle_id == v.id,
                    Reminder.remind_type == "保险",
                    Reminder.source_id != v.id,
                    Reminder.status == "待处理",
                ).update({"status": "已处理"}, synchronize_session=False)

                same_date = all(p.end_date == earliest.end_date for p in active_policies)
                if same_date and len(active_policies) > 1:
                    title = f"保险到期：{earliest.company or '未填公司'}（交强险+商业险）"
                    msg = f"交强险和商业险均将于 {earliest.end_date} 到期，剩余 {days_left} 天，请及时续保"
                else:
                    title = f"保险到期：{earliest.company or '未填公司'} {earliest.policy_type}"
                    msg = f"{earliest.policy_type}将于 {earliest.end_date} 到期，剩余 {days_left} 天"
                _upsert(
                    db, user.id, v.id, "保险", v.id,
                    title, earliest.end_date, msg, threshold_days,
                )
        # 年检到期（优先用手动录入的最新有效记录，否则根据注册登记日期按现行政策推算）
        latest_ins = (
            db.query(Inspection)
            .filter(Inspection.vehicle_id == v.id, Inspection.expire_at.isnot(None))
            .order_by(Inspection.expire_at.desc())
            .first()
        )
        if latest_ins and latest_ins.expire_at and latest_ins.expire_at > today:
            days_left = (latest_ins.expire_at - today).days
            if 0 <= days_left <= threshold_days:
                _upsert(
                    db, user.id, v.id, "年检", v.id,
                    "年检到期",
                    latest_ins.expire_at,
                    f"年检有效期至 {latest_ins.expire_at}，剩余 {days_left} 天",
                    threshold_days,
                )
        elif v.registration_date:
            next_ins = _calc_next_inspection(v.registration_date, today)
            if next_ins:
                days_left = (next_ins["next_date"] - today).days
                if 0 <= days_left <= threshold_days:
                    _upsert(
                        db, user.id, v.id, "年检", v.id,
                        f"年检到期：{next_ins['inspection_type']}",
                        next_ins["next_date"],
                        f"车辆注册登记于 {v.registration_date}，按现行政策第{next_ins['years']}年需{next_ins['inspection_type']}，"
                        f"到期日 {next_ins['next_date']}，剩余 {days_left} 天，请及时办理",
                        threshold_days,
                    )
        # 停车到期（长租车位，到期前1个月提醒续租或退租）
        for pk in (
            db.query(ParkingRecord)
            .filter(ParkingRecord.vehicle_id == v.id, ParkingRecord.end_date.isnot(None))
            .all()
        ):
            days_left = (pk.end_date - today).days
            if 0 <= days_left <= threshold_days:
                _upsert(
                    db, user.id, v.id, "停车", pk.id,
                    f"车位到期：{pk.parking_address or '未填地址'} {pk.parking_no or ''}",
                    pk.end_date,
                    f"车位{pk.parking_no or ''}租期将于 {pk.end_date} 到期，剩余 {days_left} 天，请及时续租或退租",
                    threshold_days,
                )
        # 保养到期（基于车辆保养周期，或的关系：时间或里程任一先到）
        try:
            interval_months = v.maint_interval_months or 12
            interval_km = v.maint_interval_km or 10000
            last_maint = (
                db.query(MaintenanceRecord)
                .filter(MaintenanceRecord.vehicle_id == v.id)
                .order_by(MaintenanceRecord.occurred_at.desc(), MaintenanceRecord.id.desc())
                .first()
            )
            if last_maint:
                base_date = last_maint.occurred_at if isinstance(last_maint.occurred_at, date) else last_maint.occurred_at.date()
                base_km = last_maint.mileage or 0
            else:
                base_date = v.purchase_date if isinstance(v.purchase_date, date) else (v.purchase_date.date() if v.purchase_date else today)
                base_km = v.current_mileage or 0
            next_d = _add_months(base_date, interval_months)
            next_km = base_km + interval_km
            days_left = (next_d - today).days
            km_left = next_km - (v.current_mileage or 0)
            # 或的关系：时间临期/到期 OR 里程临期/到期（1000km内）
            if days_left <= threshold_days or km_left <= 1000:
                if days_left <= 0 or km_left <= 0:
                    status_text = "已到期"
                else:
                    status_text = "即将到期"
                msg_parts = []
                if days_left <= 0:
                    msg_parts.append(f"时间已超期{-days_left}天")
                elif days_left <= threshold_days:
                    msg_parts.append(f"剩余{days_left}天")
                if km_left <= 0:
                    msg_parts.append(f"里程已超期{-km_left}km")
                elif km_left <= 1000:
                    msg_parts.append(f"剩余{km_left}km")
                _upsert(
                    db, user.id, v.id, "保养", v.id,
                    f"保养提醒：{v.name or v.brand}",
                    next_d,
                    f"{status_text}（周期{interval_months}个月/{interval_km}公里，或）。"
                    f"下次保养约{next_d}或{next_km}km，{'、'.join(msg_parts)}。",
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
