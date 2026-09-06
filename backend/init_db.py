# -*- coding: utf-8 -*-
"""初始化 car_system 数据库（仅建库，表由后端 init_db 创建）"""
import pymysql

conn = pymysql.connect(host="127.0.0.1", user="root", password="123456", autocommit=True)
cur = conn.cursor()
cur.execute(
    "CREATE DATABASE IF NOT EXISTS car_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
)
cur.execute("SHOW DATABASES LIKE 'car_system'")
print("databases:", cur.fetchall())
cur.execute("SELECT VERSION()")
print("mysql version:", cur.fetchone())
conn.close()
print("OK")
