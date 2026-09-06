# -*- coding: utf-8 -*-
"""后端 API 冒烟测试"""
import json

import httpx

BASE = "http://127.0.0.1:8002"
c = httpx.Client(base_url=BASE, timeout=30)


def show(name, resp):
    try:
        data = resp.json()
    except Exception:
        data = resp.text[:300]
    print(f"[{resp.status_code}] {name}: {json.dumps(data, ensure_ascii=False)[:400]}")
    return data


# 1. 注册
r = show("register", c.post("/api/auth/register", json={
    "username": "testuser", "password": "test123456", "display_name": "测试用户"}))
if r.get("token"):
    c.headers["Authorization"] = f"Bearer {r['token']}"
else:
    # 已存在则登录
    r = show("login", c.post("/api/auth/login", json={"username": "testuser", "password": "test123456"}))
    c.headers["Authorization"] = f"Bearer {r['token']}"

# 2. 建车（沃尔沃）
v = show("create vehicle", c.post("/api/vehicles", json={
    "name": "大白", "brand": "沃尔沃", "series": "XC60", "model_year": "2022",
    "model_name": "XC60 B5", "vin": "LVY2XXXXX2022001", "plate_no": "京A12345",
    "purchase_date": "2022-06-01", "initial_mileage": 5, "current_mileage": 45000,
    "fuel_type": "汽油", "displacement": "2.0T", "transmission": "自动",
}))
vid = v["id"]

# 3. 保养记录（带明细）
m = show("create maintenance", c.post("/api/maintenance", json={
    "vehicle_id": vid, "occurred_at": "2026-08-01", "mileage": 44000,
    "shop_name": "沃尔沃4S店", "record_type": "保养", "category": "基础保养",
    "title": "4.4万公里保养", "total_cost": 1350,
    "items": [
        {"item_name": "机油及机油滤清器", "quantity": 1, "part_cost": 680, "labor_cost": 200, "is_routine": True},
        {"item_name": "空调滤芯", "quantity": 1, "part_cost": 380, "labor_cost": 90, "is_routine": True},
    ],
}))
show("list maintenance", c.get(f"/api/maintenance", params={"vehicle_id": vid}))

# 4. 加油记录（两次加满用于油耗）
show("refuel 1", c.post("/api/refuels", json={
    "vehicle_id": vid, "refueled_at": "2026-08-10", "mileage": 44500,
    "fuel_amount_l": 50, "unit_price": 7.8, "total_cost": 390, "station": "中石化", "is_full": True}))
show("refuel 2", c.post("/api/refuels", json={
    "vehicle_id": vid, "refueled_at": "2026-09-05", "mileage": 45000,
    "fuel_amount_l": 40, "unit_price": 7.9, "total_cost": 316, "station": "中石化", "is_full": True}))
show("fuel stats", c.get(f"/api/refuels/{vid}/stats"))

# 5. 保险 + 年检 + 违章
show("insurance", c.post("/api/insurance", json={
    "vehicle_id": vid, "company": "人保", "policy_no": "P2026001", "policy_type": "商业险",
    "premium": 4200, "start_date": "2026-06-01", "end_date": "2027-05-31"}))
show("inspection", c.post("/api/inspections", json={
    "vehicle_id": vid, "inspected_at": "2025-06-15", "expire_at": "2026-06-30", "cost": 300}))
show("violation", c.post("/api/violations", json={
    "vehicle_id": vid, "occurred_at": "2026-07-20", "location": "北京三环",
    "behavior": "违反禁止标线指示", "points": 3, "fine": 100, "status": "未处理"}))

# 6. 车辆主页汇总
show("vehicle summary", c.get(f"/api/vehicles/{vid}/summary"))

# 7. AI 分析
show("AI maintenance-plan", c.post("/api/ai/maintenance-plan", json={"vehicle_id": vid}))
show("AI over-maintenance", c.post("/api/ai/over-maintenance", json={"vehicle_id": vid}))
show("AI price-estimate", c.post("/api/ai/price-estimate", json={
    "vehicle_id": vid, "items": ["机油及机油滤清器", "火花塞"]}))
show("AI health-report", c.post("/api/ai/health-report", json={"vehicle_id": vid}))

# 8. 模型配置
show("providers", c.get("/api/ai/providers"))

# 9. 提醒
show("reminders", c.get("/api/reminders"))

# 10. 统计
show("annual cost", c.get("/api/stats/annual-cost", params={"vehicle_id": vid, "year": 2026}))
show("global summary", c.get("/api/stats/summary"))

# 11. 导出（只验证状态码）
r = c.get("/api/export", params={"vehicle_id": vid})
print(f"[{r.status_code}] export zip bytes: {len(r.content)}")

c.close()
print("SMOKE TEST DONE")
