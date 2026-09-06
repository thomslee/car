# -*- coding: utf-8 -*-
"""全局配置"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # E:\car\backend
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_HOST = os.getenv("CAR_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("CAR_DB_PORT", "3306"))
DB_USER = os.getenv("CAR_DB_USER", "root")
DB_PASSWORD = os.getenv("CAR_DB_PASSWORD", "123456")
DB_NAME = os.getenv("CAR_DB_NAME", "car_system")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

JWT_SECRET = os.getenv("CAR_JWT_SECRET", "car-system-dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

# 默认提醒提前天数（保险/年检）
DEFAULT_REMIND_THRESHOLD_DAYS = 30

# AI 相关
AI_TIMEOUT_SECONDS = 60
