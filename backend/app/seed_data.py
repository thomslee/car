# -*- coding: utf-8 -*-
"""种子数据：沃尔沃保养基准 / 参考价区间 / 大模型模板 / 默认设置 / 初始管理员"""
import os

from sqlalchemy.orm import Session

from .models import AiProvider, MaintenanceManual, ReferencePrice, Setting, User
from .security import hash_password

# 沃尔沃官方基础保养周期（来源：volvocars.com.cn S60 保养页 + 车主手册共识）
VOLVO_MANUAL = [
    ("机油及机油滤清器", 10000, 12, "官方周期：1万公里或12个月，先到为准"),
    ("空调滤芯", 20000, 24, "官方第2年项目；空气差地区可提前"),
    ("发动机空滤", 30000, 36, "官方第3年项目"),
    ("燃油滤清器", 30000, 36, "官方第3年项目"),
    ("火花塞", 40000, 48, "官方第4年项目"),
    ("制动液", 40000, 24, "建议每2年或4万公里更换"),
    ("补胎液检查", 20000, 24, "官方第2年项目"),
    ("全车安全检查", 10000, 12, "随基础保养执行"),
]

# 内置参考价区间（估算值，仅作参考；实际以门店报价为准）
VOLVO_PRICES = [
    ("机油及机油滤清器", 900, 1500),
    ("空调滤芯", 300, 600),
    ("发动机空滤", 300, 500),
    ("燃油滤清器", 300, 600),
    ("火花塞", 800, 1500),
    ("制动液", 300, 500),
    ("全车安全检查", 0, 0),
]

# 大模型模板（默认 DeepSeek，需填写 api_key 后启用）
PROVIDER_TEMPLATES = [
    dict(
        name="DeepSeek",
        base_url="https://api.deepseek.com",
        api_key="",
        model_name="deepseek-chat",
        capabilities="text",
        is_default=True,
        is_enabled=False,
    ),
    dict(
        name="豆包（火山方舟）",
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key="",
        model_name="doubao-1-5-pro-32k-250115",
        capabilities="text",
        is_default=False,
        is_enabled=False,
    ),
]

DEFAULT_SETTINGS = {
    "reminder_threshold_days": "30",
}


def seed_if_empty(db: Session):
    # 初始管理员：仅当系统中完全没有用户时创建（全新部署兜底）
    if db.query(User).count() == 0:
        admin_pwd = os.getenv("ADMIN_INITIAL_PASSWORD", "admin123456")
        db.add(
            User(
                username="admin",
                password_hash=hash_password(admin_pwd),
                display_name="系统管理员",
                role="admin",
                is_active=True,
            )
        )
        print(
            "[seed] 已创建默认管理员账号 admin / %s，"
            "请立即登录并在「用户管理」中修改密码或改用已有账号！" % admin_pwd
        )
    if db.query(MaintenanceManual).count() == 0:
        for item, km, months, note in VOLVO_MANUAL:
            db.add(
                MaintenanceManual(
                    brand="沃尔沃",
                    item_name=item,
                    interval_km=km,
                    interval_months=months,
                    note=note,
                )
            )
    if db.query(ReferencePrice).count() == 0:
        for item, lo, hi in VOLVO_PRICES:
            db.add(
                ReferencePrice(
                    item_name=item,
                    vehicle_level="豪华",
                    price_min=lo,
                    price_max=hi,
                    source="内置",
                )
            )
    if db.query(AiProvider).count() == 0:
        for p in PROVIDER_TEMPLATES:
            db.add(AiProvider(**p))
    for k, v in DEFAULT_SETTINGS.items():
        if db.get(Setting, k) is None:
            db.add(Setting(key=k, value=v))
    db.commit()
