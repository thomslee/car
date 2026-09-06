@echo off
rem ============================================
rem  Car Archive System - Backend (port 8002)
rem  Run from E:\car\backend
rem ============================================
cd /d E:\car\backend
.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
pause
