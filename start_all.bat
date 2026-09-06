@echo off
rem ============================================
rem  Car Archive System - Start All
rem  Opens backend (8002) + frontend (5173)
rem ============================================
start "car-backend" cmd /k "cd /d E:\car\backend && .venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8002"
timeout /t 3 /nobreak >nul
start "car-frontend" cmd /k "cd /d E:\car\frontend && call npm run dev"
echo.
echo Car Archive System started:
echo   Backend:  http://127.0.0.1:8002/api/health
echo   Frontend: http://127.0.0.1:5173
pause
