# -*- coding: utf-8 -*-
"""AI 分析：规则引擎为底座，大模型可选生成解读"""
import json
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from ..models import (
    MaintenanceItem,
    MaintenanceManual,
    MaintenanceRecord,
    MileageRecord,
    ReferencePrice,
    RefuelRecord,
    Vehicle,
)
from . import llm_service

# 判定阈值：实际间隔 < 建议间隔 * 70% 视为过早
EARLY_RATIO = 0.7
# 未来多少天内/公里内视为"临期"
DUE_DAYS = 30
DUE_KM = 2000

# 项目名称归一化：标准名 -> 匹配关键词列表（按优先级从上到下匹配）
ITEM_ALIASES = [
    ("机油及机油滤清器", ["机油滤清器", "油过滤器", "全合成机油", "原厂基础保养", "机油"]),
    ("空调滤芯", ["空调滤", "花粉滤", "乘客室空气"]),
    ("发动机空滤", ["空气滤", "空滤", "空气过滤器插片", "空气过滤器"]),
    ("燃油滤清器", ["燃油滤", "汽滤", "燃料过滤"]),
    ("火花塞", ["火花塞"]),
    ("制动液", ["制动液", "刹车油"]),
    ("刹车片", ["制动衬片", "刹车片"]),
    ("刹车盘", ["刹车盘", "制动盘"]),
    ("轮胎", ["轮胎"]),
    ("变速箱油", ["变速箱油", "变速器油"]),
    ("蓄电池", ["蓄电池", "电瓶"]),
    ("雨刮片", ["雨刮", "雨刷"]),
    ("防冻液", ["防冻液", "冷却液"]),
    ("节气门清洗", ["节气门"]),
    ("气门积碳清洗", ["气门积碳", "干冰清洗", "干冰"]),
    ("喷油嘴清洗", ["喷油嘴", "燃油系统清洗"]),
    ("三元催化清洗", ["三元催化"]),
    ("空调清洗", ["空调清洗", "空调风道", "空调免费清洗"]),
    ("发动机舱清洁", ["发动机舱", "机舱清洗"]),
    ("全车安全检查", ["全车检查", "健康检查", "安全检测", "免费检测"]),
    ("四轮定位", ["四轮定位", "动平衡"]),
    ("空调压缩机油", ["压缩机油"]),
    ("补胎液检查", ["补胎液"]),
]


def _normalize_item_name(name: str) -> str:
    """将各种写法的项目名归一到标准名；未命中返回原始名称。"""
    if not name:
        return name or ""
    n = name.strip()
    for standard, keywords in ITEM_ALIASES:
        for kw in keywords:
            if kw in n:
                return standard
    return n


def _add_months(d: date, months: int) -> date:
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


def _monthly_km(db: Session, vehicle: Vehicle) -> float:
    """估算月均行驶里程（公里/月）；数据不足时按 1000 估算并标注"""
    points = []  # (date, mileage)
    for r in (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle.id)
        .order_by(MaintenanceRecord.occurred_at)
        .all()
    ):
        if r.mileage and r.occurred_at:
            points.append((r.occurred_at, r.mileage))
    for r in (
        db.query(RefuelRecord)
        .filter(RefuelRecord.vehicle_id == vehicle.id)
        .order_by(RefuelRecord.refueled_at)
        .all()
    ):
        if r.mileage and r.refueled_at:
            points.append((r.refueled_at, r.mileage))
    for r in (
        db.query(MileageRecord)
        .filter(MileageRecord.vehicle_id == vehicle.id)
        .order_by(MileageRecord.recorded_at)
        .all()
    ):
        if r.mileage and r.recorded_at:
            points.append((r.recorded_at, r.mileage))
    points.sort(key=lambda x: x[0])
    if len(points) >= 2:
        d0, m0 = points[0]
        d1, m1 = points[-1]
        days = (d1 - d0).days
        if days >= 14 and m1 > m0:
            return round((m1 - m0) / days * 30.4, 1)
    if vehicle.purchase_date and vehicle.current_mileage:
        days = max((date.today() - vehicle.purchase_date).days, 1)
        if days >= 30:
            return round(vehicle.current_mileage / days * 30.4, 1)
    return 1000.0  # 兜底估算


def _manual_map(db: Session) -> dict:
    """item_name -> manual 基准（取沃尔沃记录）"""
    out = {}
    for m in db.query(MaintenanceManual).all():
        out.setdefault(m.item_name, m)
    return out


def maintenance_plan(db: Session, vehicle: Vehicle) -> dict:
    today = date.today()
    monthly = _monthly_km(db, vehicle)
    manual_map = _manual_map(db)

    # 最近一次各定期项目的出现（归一化后），以及未命中标准项目的其他记录
    last_occurrence = {}
    other_occurrence = {}  # 原始名 -> (date, mileage)
    records = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle.id)
        .order_by(MaintenanceRecord.occurred_at, MaintenanceRecord.id)
        .all()
    )
    for rec in records:
        for it in rec.items:
            if not it.is_routine:
                continue
            normalized = _normalize_item_name(it.item_name)
            if normalized in manual_map:
                # 取该项目的最后一次（遍历顺序即时间正序）
                last_occurrence[normalized] = (rec.occurred_at, rec.mileage)
            else:
                other_occurrence[it.item_name] = (rec.occurred_at, rec.mileage)

    plan_items = []
    for name, manual in sorted(manual_map.items(), key=lambda x: x[0]):
        base = last_occurrence.get(name)
        if base:
            last_date, last_km = base
            due_date = _add_months(last_date, manual.interval_months)
            due_km = (last_km or 0) + manual.interval_km
            never_done = False
            elapsed_days = (today - last_date).days
            elapsed_km = (vehicle.current_mileage or 0) - (last_km or 0)
        else:
            never_done = True
            base_date = vehicle.purchase_date or today
            base_km = vehicle.current_mileage or 0
            due_date = _add_months(base_date, manual.interval_months)
            due_km = base_km + manual.interval_km
            elapsed_days = None
            elapsed_km = None

        days_left = (due_date - today).days
        km_left = due_km - (vehicle.current_mileage or 0)
        if never_done and (days_left <= 0 or km_left <= 0):
            status = "未记录"
        elif days_left <= 0 or km_left <= 0:
            status = "已到期"
        elif days_left <= DUE_DAYS or km_left <= DUE_KM:
            status = "临期"
        else:
            status = "未到期"
        plan_items.append(
            {
                "item_name": name,
                "last_date": str(base[0]) if base else None,
                "last_mileage": base[1] if base else None,
                "due_date": str(due_date),
                "due_mileage": due_km,
                "days_left": days_left,
                "km_left": km_left,
                "elapsed_days": elapsed_days,
                "elapsed_km": elapsed_km,
                "interval_months": manual.interval_months,
                "interval_km": manual.interval_km,
                "status": status,
                "manual_note": manual.note or "",
            }
        )

    # 排序：已到期→临期→未到期→未记录，同级按 days_left 升序
    status_order = {"已到期": 0, "临期": 1, "未到期": 2, "未记录": 3}
    plan_items.sort(key=lambda x: (status_order.get(x["status"], 9), x["days_left"]))

    due_items = [p for p in plan_items if p["status"] in ("已到期", "临期")]

    # 车辆级下次保养（与车辆主页一致：12月/10000km 或的关系）
    interval_months = vehicle.maint_interval_months or 12
    interval_km = vehicle.maint_interval_km or 10000
    last_maint = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle.id)
        .order_by(MaintenanceRecord.occurred_at.desc(), MaintenanceRecord.id.desc())
        .first()
    )
    if last_maint:
        v_base_date = last_maint.occurred_at if isinstance(last_maint.occurred_at, date) else last_maint.occurred_at.date()
        v_base_km = last_maint.mileage or 0
    else:
        v_base_date = vehicle.purchase_date if isinstance(vehicle.purchase_date, date) else (vehicle.purchase_date.date() if vehicle.purchase_date else today)
        v_base_km = vehicle.current_mileage or 0
    v_next_date = _add_months(v_base_date, interval_months)
    v_next_km = v_base_km + interval_km
    v_days_left = (v_next_date - today).days
    v_km_left = v_next_km - (vehicle.current_mileage or 0)
    if v_days_left <= 0 or v_km_left <= 0:
        v_status = "已到期"
    elif v_days_left <= 30 or v_km_left <= 1000:
        v_status = "临期"
    else:
        v_status = "未到期"

    # 其他项目（归一化未命中的）
    other_items = [
        {"item_name": name, "last_date": str(d), "last_mileage": m}
        for name, (d, m) in sorted(other_occurrence.items(), key=lambda x: x[1][0], reverse=True)
    ]

    result = {
        "vehicle_id": vehicle.id,
        "generated_at": str(today),
        "monthly_km_estimate": monthly,
        "estimate_note": "月均里程由记录推算；数据不足时按 1000 公里/月估算",
        "next_maintenance": {
            "next_date": str(v_next_date),
            "next_mileage": v_next_km,
            "status": v_status,
            "days_left": v_days_left,
            "km_left": v_km_left,
            "interval_months": interval_months,
            "interval_km": interval_km,
        },
        "due_items": due_items,
        "plan_items": plan_items,
        "other_items": other_items,
    }
    return result


def over_maintenance(db: Session, vehicle: Vehicle) -> dict:
    manual_map = _manual_map(db)
    # 每个定期项目（归一化后）按时间排序的所有出现
    occurrences = {}
    records = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle.id)
        .order_by(MaintenanceRecord.occurred_at, MaintenanceRecord.id)
        .all()
    )
    for rec in records:
        for it in rec.items:
            if it.is_routine:
                normalized = _normalize_item_name(it.item_name)
                if normalized in manual_map:
                    occurrences.setdefault(normalized, []).append((rec.occurred_at, rec.mileage))

    findings = []
    for name, occ in occurrences.items():
        manual = manual_map.get(name)
        if manual is None or len(occ) < 2:
            continue
        for prev, cur in zip(occ, occ[1:]):
            km_interval = cur[1] - prev[1] if (prev[1] and cur[1]) else None
            month_interval = (cur[0] - prev[0]).days / 30.4
            too_early_km = (
                km_interval is not None
                and manual.interval_km > 0
                and km_interval < manual.interval_km * EARLY_RATIO
            )
            too_early_month = (
                manual.interval_months > 0
                and month_interval < manual.interval_months * EARLY_RATIO
            )
            judgment = "正常"
            if too_early_km or too_early_month:
                judgment = "可能过早"
            findings.append(
                {
                    "item_name": name,
                    "prev_date": str(prev[0]),
                    "cur_date": str(cur[0]),
                    "km_interval": km_interval,
                    "month_interval": round(month_interval, 1),
                    "manual_interval_km": manual.interval_km,
                    "manual_interval_months": manual.interval_months,
                    "judgment": judgment,
                    "suggestion": (
                        f"该品牌建议 {manual.interval_km} 公里/{manual.interval_months} 个月一次，"
                        "本次间隔明显偏短，如无特殊原因可延长间隔，避免过度保养。"
                        if judgment == "可能过早"
                        else "间隔符合建议周期。"
                    ),
                }
            )
    return {
        "vehicle_id": vehicle.id,
        "generated_at": str(today := date.today()),
        "findings": findings,
        "early_count": sum(1 for f in findings if f["judgment"] == "可能过早"),
    }


def price_estimate(db: Session, vehicle: Vehicle, item_names: list[str]) -> dict:
    result = []
    for name in item_names:
        # 1) 用户历史均价（优先）
        items = (
            db.query(MaintenanceItem)
            .join(MaintenanceRecord, MaintenanceItem.record_id == MaintenanceRecord.id)
            .filter(
                MaintenanceRecord.vehicle_id == vehicle.id,
                MaintenanceItem.item_name.like(f"%{name}%"),
            )
            .all()
        )
        if items:
            vals = [float(it.part_cost or 0) + float(it.labor_cost or 0) for it in items if (it.part_cost or it.labor_cost)]
            if vals:
                result.append(
                    {
                        "item_name": name,
                        "price_min": round(min(vals), 2),
                        "price_max": round(max(vals), 2),
                        "avg": round(sum(vals) / len(vals), 2),
                        "source": "你的历史记录",
                        "sample_count": len(vals),
                    }
                )
                continue
        # 2) 内置参考区间
        ref = (
            db.query(ReferencePrice)
            .filter(ReferencePrice.item_name.like(f"%{name}%"))
            .first()
        )
        if ref and (ref.price_min or ref.price_max):
            result.append(
                {
                    "item_name": name,
                    "price_min": float(ref.price_min),
                    "price_max": float(ref.price_max),
                    "avg": round((float(ref.price_min) + float(ref.price_max)) / 2, 2),
                    "source": "内置参考（估算）",
                    "sample_count": 0,
                }
            )
            continue
        result.append(
            {"item_name": name, "price_min": None, "price_max": None, "avg": None, "source": "暂无参考", "sample_count": 0}
        )
    return {
        "vehicle_id": vehicle.id,
        "note": "价格区间为估算值，实际以门店报价为准；有历史记录时优先采用你的消费均值",
        "items": result,
    }


def health_report(db: Session, vehicle: Vehicle) -> dict:
    plan = maintenance_plan(db, vehicle)
    over = over_maintenance(db, vehicle)
    monthly = plan["monthly_km_estimate"]
    records = (
        db.query(MaintenanceRecord)
        .filter(MaintenanceRecord.vehicle_id == vehicle.id)
        .all()
    )
    repair_count = sum(1 for r in records if r.record_type == "维修")
    maint_count = sum(1 for r in records if r.record_type == "保养")

    # 简单评分 0-100
    score = 80
    if over["early_count"] > 0:
        score -= min(over["early_count"] * 8, 24)
    if repair_count >= 3:
        score -= 10
    if monthly > 2000:
        score -= 5
    if not records:
        score = 50
    score = max(0, min(100, score))

    data = {
        "vehicle_id": vehicle.id,
        "score": score,
        "monthly_km": monthly,
        "maintenance_count": maint_count,
        "repair_count": repair_count,
        "early_maintenance_count": over["early_count"],
        "next_maintenance_date": plan["next_maintenance"]["next_date"],
        "next_maintenance_mileage": plan["next_maintenance"]["next_mileage"],
    }
    return data


def narrate(db: Session, plan: dict | None = None, over: dict | None = None, price: dict | None = None) -> str | None:
    """可选：用配置的默认模型生成自然语言解读"""
    provider = llm_service.get_default_provider(db)
    if provider is None or not provider.api_key:
        return None
    parts = []
    if plan:
        parts.append("保养预测：" + json.dumps(plan, ensure_ascii=False))
    if over:
        parts.append("过度保养检测：" + json.dumps(over, ensure_ascii=False))
    if price:
        parts.append("价格估算：" + json.dumps(price, ensure_ascii=False))
    if not parts:
        return None
    try:
        return llm_service.call_chat(
            provider,
            "你是汽车养护顾问，请用通俗中文、分条给出结论与建议，语气务实，不夸大。",
            "\n".join(parts),
            temperature=0.4,
        )
    except Exception:
        return None
