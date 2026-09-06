# -*- coding: utf-8 -*-
"""清理冒烟测试数据（保留种子数据：保养基准/参考价/模型模板/设置）"""
import pymysql

conn = pymysql.connect(host="127.0.0.1", user="root", password="123456", database="car_system", autocommit=True)
cur = conn.cursor()
cur.execute("SET FOREIGN_KEY_CHECKS=0")
tables = [
    "ai_analyses", "ocr_tasks", "attachments", "reminders", "violation_records",
    "inspections", "insurance_policies", "refuel_records", "maintenance_items",
    "maintenance_records", "mileage_records", "vehicles", "users",
]
for t in tables:
    cur.execute(f"TRUNCATE TABLE {t}")
cur.execute("SET FOREIGN_KEY_CHECKS=1")
cur.execute("SELECT COUNT(*) FROM vehicles")
print("vehicles after cleanup:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM users")
print("users after cleanup:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM maintenance_manual")
print("manual seeds:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM ai_providers")
print("providers seeds:", cur.fetchone()[0])
conn.close()
print("CLEANUP OK")
