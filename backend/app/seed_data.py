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
    # 易磨损件
    ("刹车片", 40000, 24, "视驾驶习惯，前片通常先换"),
    ("刹车盘", 80000, 48, "通常随第二副刹车片更换"),
    ("轮胎", 50000, 36, "视磨损和老化，5年或花纹≤1.6mm"),
    ("雨刮片", 20000, 12, "视老化刮不干净即换"),
    ("蓄电池", 40000, 36, "视使用情况，启动无力即换"),
    # 油液
    ("变速箱油", 60000, 48, "自动变速箱，视工况"),
    ("防冻液", 40000, 24, "视冰点检测，2年或4万公里"),
    ("空调压缩机油", 60000, 60, "视空调制冷效果"),
    # 清洗养护
    ("节气门清洗", 20000, 12, "视积碳情况，怠速抖动即洗"),
    ("气门积碳清洗", 30000, 24, "直喷发动机建议，干冰清洗"),
    ("喷油嘴清洗", 30000, 24, "可选养护，动力下降时洗"),
    ("三元催化清洗", 30000, 24, "可选养护"),
    ("空调清洗", 0, 12, "每年换季，空调异味即洗"),
    ("发动机舱清洁", 0, 12, "可选养护，保持机舱整洁"),
    # 其他
    ("四轮定位", 20000, 0, "视跑偏/吃胎，换胎后建议做"),
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
    ("刹车片", 800, 1800),
    ("刹车盘", 1500, 3000),
    ("轮胎", 800, 2000),
    ("雨刮片", 100, 300),
    ("蓄电池", 800, 1500),
    ("变速箱油", 1000, 2500),
    ("防冻液", 300, 600),
    ("空调压缩机油", 300, 800),
    ("节气门清洗", 200, 500),
    ("气门积碳清洗", 500, 1500),
    ("喷油嘴清洗", 200, 600),
    ("三元催化清洗", 300, 800),
    ("空调清洗", 100, 400),
    ("发动机舱清洁", 50, 200),
    ("四轮定位", 200, 500),
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
