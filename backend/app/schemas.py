# -*- coding: utf-8 -*-
"""Pydantic 出入参"""
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------- 认证 ----------
class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    display_name: str
    role: str = "user"
    is_active: bool = True
    created_at: Optional[Any] = None

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    token: str
    user: UserOut


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=100)


# ---------- 管理员：用户管理 ----------
class AdminUserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    display_name: str = ""
    role: str = "user"  # admin / user


class AdminUserUpdate(BaseModel):
    display_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=100)
    role: Optional[str] = None
    is_active: Optional[bool] = None


# ---------- 车辆 ----------
class VehicleIn(BaseModel):
    name: str = ""
    brand: str = "沃尔沃"
    series: str = ""
    model_year: str = ""
    model_name: str = ""
    vin: str = ""
    plate_no: str = ""
    engine_no: str = ""
    purchase_date: Optional[date] = None
    initial_mileage: int = 0
    current_mileage: int = 0
    fuel_type: str = "汽油"
    displacement: str = ""
    transmission: str = ""
    color: str = ""
    maint_interval_months: int = 12
    maint_interval_km: int = 10000
    notes: str = ""


class VehicleOut(VehicleIn):
    id: int
    is_active: bool
    created_at: Any = None
    updated_at: Any = None

    class Config:
        from_attributes = True


class MileageIn(BaseModel):
    recorded_at: date
    mileage: int
    source: str = "手工"
    note: str = ""


# ---------- 保养维修 ----------
class MaintenanceItemIn(BaseModel):
    item_type: str = "材料"  # 材料/工时
    item_name: str
    quantity: float = 1
    unit_price: float = 0
    part_cost: float = 0
    labor_cost: float = 0
    is_original: bool = False
    is_routine: bool = True
    note: str = ""


class MaintenanceDiscountIn(BaseModel):
    name: str
    amount: float = 0


class MaintenanceDiscountOut(MaintenanceDiscountIn):
    id: int

    class Config:
        from_attributes = True


class MaintenanceIn(BaseModel):
    vehicle_id: int
    occurred_at: date
    mileage: int = 0
    shop_name: str = ""
    record_type: str = "保养"
    category: str = ""
    title: str = ""
    description: str = ""
    total_cost: float = 0
    original_total_cost: float = 0
    discount_amount: float = 0
    paid_amount: float = 0
    confirmed_at: Optional[datetime] = None
    skipped_note: str = ""
    invoice_no: str = ""
    warranty: bool = False
    notes: str = ""
    items: list[MaintenanceItemIn] = []
    discounts: list[MaintenanceDiscountIn] = []


class MaintenanceItemOut(MaintenanceItemIn):
    id: int

    class Config:
        from_attributes = True


class MaintenanceOut(BaseModel):
    id: int
    vehicle_id: int
    occurred_at: date
    mileage: int
    shop_name: str
    record_type: str
    category: str
    title: str
    description: str
    total_cost: float
    original_total_cost: float = 0
    discount_amount: float = 0
    paid_amount: float = 0
    confirmed_at: Any = None
    skipped_note: Optional[str] = ""
    invoice_no: str
    warranty: bool
    notes: str
    created_at: Any = None
    items: list[MaintenanceItemOut] = []
    discounts: list[MaintenanceDiscountOut] = []

    class Config:
        from_attributes = True


# ---------- 加油 ----------
class RefuelIn(BaseModel):
    vehicle_id: int
    refueled_at: datetime
    mileage: Optional[int] = None
    fuel_amount_l: float = 0
    unit_price: float = 0
    total_cost: float = 0  # 应付金额
    paid_amount: float = 0  # 实付金额（优惠后）
    fuel_grade: str = "95"  # 油标：92/95/98
    station: str = ""
    fuel_type: str = "汽油"
    is_full: bool = True
    note: str = ""


class RefuelOut(RefuelIn):
    id: int
    created_at: Any = None

    class Config:
        from_attributes = True


# ---------- 保险 ----------
class InsuranceIn(BaseModel):
    vehicle_id: int
    company: str = ""
    policy_no: str = ""
    policy_type: str = "商业险"
    items_json: str = "[]"
    premium: float = 0
    vehicle_tax: float = 0
    service_phone: str = ""
    vehicle_model: str = ""
    plate_no: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    attachment: Optional[str] = ""
    note: str = ""


class InsuranceOut(InsuranceIn):
    id: int
    created_at: Any = None

    class Config:
        from_attributes = True


# ---------- 年检 ----------
class InspectionIn(BaseModel):
    vehicle_id: int
    inspected_at: Optional[date] = None
    expire_at: Optional[date] = None
    result: str = "合格"
    station: str = ""
    cost: float = 0
    attachment: str = ""
    note: str = ""


class InspectionOut(InspectionIn):
    id: int
    created_at: Any = None

    class Config:
        from_attributes = True


# ---------- 违章 ----------
class ViolationIn(BaseModel):
    vehicle_id: int
    occurred_at: Optional[date] = None
    location: str = ""
    behavior: str = ""
    points: int = 0
    fine: float = 0
    status: str = "未处理"
    handle_date: Optional[date] = None
    attachment: str = ""
    note: str = ""


class ViolationOut(ViolationIn):
    id: int
    created_at: Any = None

    class Config:
        from_attributes = True


# ---------- 提醒 ----------
class ReminderIn(BaseModel):
    vehicle_id: Optional[int] = None
    remind_type: str = "自定义"
    title: str = ""
    target_date: Optional[date] = None
    target_mileage: Optional[int] = None
    threshold_days: int = 30
    message: str = ""


class ReminderOut(BaseModel):
    id: int
    vehicle_id: Optional[int]
    remind_type: str
    title: str
    target_date: Optional[date]
    target_mileage: Optional[int]
    threshold_days: int
    message: str
    status: str
    created_at: Any = None

    class Config:
        from_attributes = True


class ReminderHandleIn(BaseModel):
    status: str = "已完成"  # 已完成/已忽略


# ---------- 大模型配置 ----------
class ProviderIn(BaseModel):
    name: str
    base_url: str
    api_key: str = ""
    model_name: str
    capabilities: str = "text"
    is_default: bool = False
    is_enabled: bool = False


class ProviderOut(ProviderIn):
    id: int

    class Config:
        from_attributes = True


# ---------- AI ----------
class MaintenancePlanIn(BaseModel):
    vehicle_id: int


class PriceEstimateIn(BaseModel):
    vehicle_id: int
    items: list[str] = []
