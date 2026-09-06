# -*- coding: utf-8 -*-
"""FastAPI 入口：路由注册 / 静态文件 / 定时提醒扫描"""
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import UPLOAD_DIR
from .database import Base, SessionLocal, engine
from .routers import (
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


def _create_tables_and_seed():
    Base.metadata.create_all(bind=engine)
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
