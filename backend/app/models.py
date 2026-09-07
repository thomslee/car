# -*- coding: utf-8 -*-
"""数据模型"""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(50), default="")
    role = Column(String(20), default="user", nullable=False)  # admin / user
    is_active = Column(Boolean, default=True, nullable=False)  # False=已禁用
    created_at = Column(DateTime, default=datetime.now)

    vehicles = relationship("Vehicle", back_populates="owner")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(50), default="")  # 别名，如"大白"
    brand = Column(String(50), default="沃尔沃")
    series = Column(String(50), default="")  # 车系，如 S60
    model_year = Column(String(10), default="")
    model_name = Column(String(50), default="")  # 具体车型
    vin = Column(String(50), default="")  # 车架号
    plate_no = Column(String(20), default="")
    engine_no = Column(String(50), default="")
    purchase_date = Column(Date, nullable=True)
    initial_mileage = Column(Integer, default=0)
    current_mileage = Column(Integer, default=0)
    fuel_type = Column(String(20), default="汽油")
    displacement = Column(String(20), default="")
    transmission = Column(String(20), default="")
    color = Column(String(20), default="")
    is_active = Column(Boolean, default=True)  # False=归档
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    owner = relationship("User", back_populates="vehicles")


class MileageRecord(Base):
    __tablename__ = "mileage_records"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    recorded_at = Column(Date, nullable=False)
    mileage = Column(Integer, nullable=False)
    source = Column(String(20), default="手工")  # 手工/加油/保养
    note = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.now)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    occurred_at = Column(Date, nullable=False)
    mileage = Column(Integer, default=0)
    shop_name = Column(String(100), default="")
    record_type = Column(String(10), default="保养")  # 保养/维修/年检/其他
    category = Column(String(20), default="")  # 常规保养/大保养/维修...
    title = Column(String(100), default="")
    description = Column(Text, default="")
    total_cost = Column(Numeric(10, 2), default=0)
    original_total_cost = Column(Numeric(10, 2), default=0)  # 原价合计
    discount_amount = Column(Numeric(10, 2), default=0)  # 折扣金额（正数）
    paid_amount = Column(Numeric(10, 2), default=0)  # 已支付
    confirmed_at = Column(DateTime, nullable=True)  # 客户确认时间
    skipped_note = Column(Text, default="")  # 本次未做项目
    invoice_no = Column(String(50), default="")
    warranty = Column(Boolean, default=False)  # 是否质保内
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    items = relationship(
        "MaintenanceItem",
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="MaintenanceItem.id",
    )
    discounts = relationship(
        "MaintenanceDiscount",
        back_populates="record",
        cascade="all, delete-orphan",
        order_by="MaintenanceDiscount.id",
    )


class MaintenanceItem(Base):
    __tablename__ = "maintenance_items"

    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey("maintenance_records.id"), nullable=False, index=True)
    item_type = Column(String(10), default="材料")  # 材料/工时
    item_name = Column(String(100), nullable=False)
    quantity = Column(Numeric(6, 2), default=1)
    unit_price = Column(Numeric(10, 2), default=0)  # 单价
    part_cost = Column(Numeric(10, 2), default=0)
    labor_cost = Column(Numeric(10, 2), default=0)
    is_original = Column(Boolean, default=False)  # 是否原厂件（材料类）
    is_routine = Column(Boolean, default=True)  # 是否定期保养项
    note = Column(String(200), default="")

    record = relationship("MaintenanceRecord", back_populates="items")


class MaintenanceDiscount(Base):
    __tablename__ = "maintenance_discounts"

    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey("maintenance_records.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # 折扣名称
    amount = Column(Numeric(10, 2), default=0)  # 折扣金额（正数）

    record = relationship("MaintenanceRecord", back_populates="discounts")


class RefuelRecord(Base):
    __tablename__ = "refuel_records"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    refueled_at = Column(DateTime, nullable=False)
    mileage = Column(Integer, nullable=True)
    fuel_amount_l = Column(Numeric(8, 2), default=0)
    unit_price = Column(Numeric(6, 2), default=0)
    total_cost = Column(Numeric(10, 2), default=0)  # 应付金额
    paid_amount = Column(Numeric(10, 2), default=0)  # 实付金额（优惠后）
    fuel_grade = Column(String(10), default="95")  # 油标：92/95/98
    station = Column(String(100), default="")
    fuel_type = Column(String(20), default="汽油")
    is_full = Column(Boolean, default=True)  # 是否加满
    note = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.now)


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    company = Column(String(100), default="")
    policy_no = Column(String(50), default="")
    policy_type = Column(String(20), default="商业险")  # 交强险/商业险
    items_json = Column(Text, default="[]")  # 险种明细 JSON
    premium = Column(Numeric(10, 2), default=0)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    attachment = Column(String(255), default="")
    note = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.now)


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    inspected_at = Column(Date, nullable=True)
    expire_at = Column(Date, nullable=True)
    result = Column(String(20), default="合格")
    station = Column(String(100), default="")
    cost = Column(Numeric(10, 2), default=0)
    attachment = Column(String(255), default="")
    note = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.now)


class ViolationRecord(Base):
    __tablename__ = "violation_records"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    occurred_at = Column(Date, nullable=True)
    location = Column(String(200), default="")
    behavior = Column(String(200), default="")  # 违章行为
    points = Column(Integer, default=0)  # 扣分
    fine = Column(Numeric(10, 2), default=0)  # 罚款
    status = Column(String(10), default="未处理")  # 未处理/已处理
    handle_date = Column(Date, nullable=True)
    attachment = Column(String(255), default="")
    note = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.now)


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    remind_type = Column(String(20), nullable=False)  # 保养/保险/年检/自定义
    title = Column(String(100), default="")
    target_date = Column(Date, nullable=True)
    target_mileage = Column(Integer, nullable=True)
    threshold_days = Column(Integer, default=30)
    message = Column(String(500), default="")
    status = Column(String(10), default="待处理")  # 待处理/已完成/已忽略
    source_id = Column(Integer, nullable=True)  # 关联保险单/年检/保养记录 id
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    biz_type = Column(String(30), default="")  # 保养单/保单/发票/行驶证/违章单/照片
    biz_id = Column(Integer, default=0)
    file_path = Column(String(255), nullable=False)
    original_name = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.now)


class OcrTask(Base):
    __tablename__ = "ocr_tasks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    image_path = Column(String(255), default="")
    raw_text = Column(Text, default="")
    parsed_json = Column(Text, default="")
    status = Column(String(20), default="待识别")
    provider = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.now)


class MaintenanceManual(Base):
    """保养手册基准（种子数据：沃尔沃）"""

    __tablename__ = "maintenance_manual"

    id = Column(Integer, primary_key=True)
    brand = Column(String(50), default="沃尔沃")
    series = Column(String(50), default="")  # 空=全系通用
    item_name = Column(String(100), nullable=False)
    interval_km = Column(Integer, default=0)
    interval_months = Column(Integer, default=0)
    is_routine = Column(Boolean, default=True)
    note = Column(String(200), default="")


class ReferencePrice(Base):
    """参考价区间（内置估算 + 用户历史均值）"""

    __tablename__ = "reference_prices"

    id = Column(Integer, primary_key=True)
    item_name = Column(String(100), nullable=False, index=True)
    vehicle_level = Column(String(20), default="豪华")  # 豪华/中级/经济
    price_min = Column(Numeric(10, 2), default=0)
    price_max = Column(Numeric(10, 2), default=0)
    unit = Column(String(20), default="元")
    source = Column(String(50), default="内置")  # 内置/用户均值
    created_at = Column(DateTime, default=datetime.now)


class AiProvider(Base):
    """大模型配置（多品牌可配置）"""

    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    base_url = Column(String(255), nullable=False)
    api_key = Column(String(255), default="")
    model_name = Column(String(100), nullable=False)
    capabilities = Column(String(50), default="text")  # text / vision
    is_default = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(50), primary_key=True)
    value = Column(String(255), default="")


class AiAnalysis(Base):
    """AI 分析结果缓存"""

    __tablename__ = "ai_analyses"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    analysis_type = Column(String(30), nullable=False)
    result_json = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
