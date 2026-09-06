# -*- coding: utf-8 -*-
"""数据导出：按车辆打包 CSV（utf-8-sig，Excel 可直接打开）"""
import csv
import io
import zipfile
from datetime import date
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, get_vehicle_or_404
from ..models import (
    Inspection,
    InsurancePolicy,
    MaintenanceRecord,
    MileageRecord,
    RefuelRecord,
    User,
    Vehicle,
    ViolationRecord,
)

router = APIRouter(prefix="/api/export", tags=["export"])


def _csv_bytes(headers: list[str], rows: list[list]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for r in rows:
        w.writerow(r)
    return buf.getvalue().encode("utf-8-sig")


@router.get("")
def export_vehicle(
    vehicle_id: int = Query(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    v = get_vehicle_or_404(db, vehicle_id, user)
    zf = io.BytesIO()
    with zipfile.ZipFile(zf, "w", zipfile.ZIP_DEFLATED) as z:

        def add(name, headers, rows):
            z.writestr(f"{name}.csv", _csv_bytes(headers, rows))

        add("01_车辆档案", ["字段", "值"], [[k, getattr(v, k)] for k in
            ["name", "brand", "series", "model_year", "model_name", "vin", "plate_no",
             "engine_no", "purchase_date", "initial_mileage", "current_mileage",
             "fuel_type", "displacement", "transmission", "color", "notes"]])

        add("02_保养维修", ["日期", "里程", "门店", "类型", "类别", "标题", "费用", "发票号", "备注"],
            [[r.occurred_at, r.mileage, r.shop_name, r.record_type, r.category, r.title,
              float(r.total_cost or 0), r.invoice_no, r.notes]
             for r in db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle_id)
             .order_by(MaintenanceRecord.occurred_at).all()])

        add("03_保养项目明细", ["日期", "项目", "数量", "材料费", "工时费", "定期项"],
            [[r.occurred_at, i.item_name, i.quantity, float(i.part_cost or 0),
              float(i.labor_cost or 0), "是" if i.is_routine else "否"]
             for r in db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle_id).all()
             for i in r.items])

        add("04_加油记录", ["日期", "里程", "油量L", "单价", "金额", "加油站", "加满"],
            [[r.refueled_at, r.mileage, float(r.fuel_amount_l or 0), float(r.unit_price or 0),
              float(r.total_cost or 0), r.station, "是" if r.is_full else "否"]
             for r in db.query(RefuelRecord).filter(RefuelRecord.vehicle_id == vehicle_id)
             .order_by(RefuelRecord.refueled_at).all()])

        add("05_保险", ["公司", "保单号", "类型", "险种", "保费", "起", "止", "备注"],
            [[p.company, p.policy_no, p.policy_type, p.items_json, float(p.premium or 0),
              p.start_date, p.end_date, p.note]
             for p in db.query(InsurancePolicy).filter(InsurancePolicy.vehicle_id == vehicle_id).all()])

        add("06_年检", ["检测日期", "到期日期", "结果", "检测站", "费用"],
            [[i.inspected_at, i.expire_at, i.result, i.station, float(i.cost or 0)]
             for i in db.query(Inspection).filter(Inspection.vehicle_id == vehicle_id).all()])

        add("07_违章", ["日期", "地点", "行为", "扣分", "罚款", "状态", "处理日期"],
            [[x.occurred_at, x.location, x.behavior, x.points, float(x.fine or 0), x.status, x.handle_date]
             for x in db.query(ViolationRecord).filter(ViolationRecord.vehicle_id == vehicle_id).all()])

        add("08_里程记录", ["日期", "里程", "来源", "备注"],
            [[m.recorded_at, m.mileage, m.source, m.note]
             for m in db.query(MileageRecord).filter(MileageRecord.vehicle_id == vehicle_id)
             .order_by(MileageRecord.recorded_at).all()])

    zf.seek(0)
    ascii_name = f"car_export_{vehicle_id}_{date.today()}.zip"
    display_name = quote(f"car_{v.plate_no or v.name or v.id}_{date.today()}.zip")
    return StreamingResponse(
        zf,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{display_name}"
            )
        },
    )
