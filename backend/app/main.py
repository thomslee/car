# -*- coding: utf-8 -*-
"""FastAPI 入口：路由注册 / 静态文件 / 定时提醒扫描"""
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import UPLOAD_DIR
from .database import Base, SessionLocal, engine
from .routers import (
    admin_users,
    ai,
    attachments,
    auth,
    export,
    inspections,
    insurance,
    maintenance,
    ocr,
    refuels,
    reminders,
    stats,
    vehicles,
    violations,
)
from .seed_data import seed_if_empty
from .services import remind_service


def _ensure_user_role_schema():
    """幂等迁移：users 表补充 role/is_active 列；确保至少存在一名管理员。"""
    with engine.connect() as conn:
        cols = conn.execute(text("SHOW COLUMNS FROM users LIKE 'role'")).fetchall()
        if not cols:
            conn.execute(
                text(
                    "ALTER TABLE users "
                    "ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user', "
                    "ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1"
                )
            )
            conn.commit()
            print("[migrate] users 表已新增 role / is_active 列")
        admins = conn.execute(text("SELECT COUNT(*) FROM users WHERE role='admin'")).scalar()
        if admins == 0:
            first = conn.execute(text("SELECT id, username FROM users ORDER BY id LIMIT 1")).fetchone()
            if first:
                conn.execute(text("UPDATE users SET role='admin' WHERE id=:i"), {"i": first[0]})
                conn.commit()
                print(f"[migrate] 已将用户 {first[1]} 设为管理员")


def _ensure_maintenance_schema():
    """幂等迁移：保养记录/项目表补充新列，折扣表由 create_all 自动建。"""
    record_cols = {
        "original_total_cost": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "discount_amount": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "paid_amount": "DECIMAL(10,2) NOT NULL DEFAULT 0",
        "confirmed_at": "DATETIME NULL DEFAULT NULL",
        "skipped_note": "TEXT NOT NULL DEFAULT ''",
    }
    item_cols = {
        "item_type": "VARCHAR(10) NOT NULL DEFAULT '材料'",
        "is_original": "TINYINT(1) NOT NULL DEFAULT 0",
        "unit_price": "DECIMAL(10,2) NOT NULL DEFAULT 0",
    }
    with engine.connect() as conn:
        for col, ddl in record_cols.items():
            if not conn.execute(text(f"SHOW COLUMNS FROM maintenance_records LIKE '{col}'")).fetchall():
                conn.execute(text(f"ALTER TABLE maintenance_records ADD COLUMN {col} {ddl}"))
                conn.commit()
                print(f"[migrate] maintenance_records 已新增 {col}")
        for col, ddl in item_cols.items():
            if not conn.execute(text(f"SHOW COLUMNS FROM maintenance_items LIKE '{col}'")).fetchall():
                conn.execute(text(f"ALTER TABLE maintenance_items ADD COLUMN {col} {ddl}"))
                conn.commit()
                print(f"[migrate] maintenance_items 已新增 {col}")


def _create_tables_and_seed():
    Base.metadata.create_all(bind=engine)
    _ensure_user_role_schema()
    _ensure_maintenance_schema()
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()


def _start_scheduler():
    sched = BackgroundScheduler(timezone="Asia/Shanghai")

    def scan_job():
        db = SessionLocal()
        try:
            remind_service.scan_all(db)
        except Exception:
            pass
        finally:
            db.close()

    # 每天 8:00 与 20:00 各扫描一次，另启动后立即扫一次
    sched.add_job(scan_job, "cron", hour=8, minute=0, id="remind_morning")
    sched.add_job(scan_job, "cron", hour=20, minute=0, id="remind_evening")
    sched.add_job(scan_job, "interval", minutes=180, id="remind_interval", next_run_time=datetime.now())
    sched.start()
    return sched


@asynccontextmanager
async def lifespan(app: FastAPI):
    _create_tables_and_seed()
    scheduler = _start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="汽车档案系统 API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(admin_users.router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)
app.include_router(refuels.router)
app.include_router(insurance.router)
app.include_router(inspections.router)
app.include_router(violations.router)
app.include_router(reminders.router)
app.include_router(attachments.router)
app.include_router(ocr.router)
app.include_router(ai.router)
app.include_router(stats.router)
app.include_router(export.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "time": str(datetime.now())}
