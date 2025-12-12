@echo off
REM Launch VaaS Enterprise Dashboard
REM Starts both platform and dashboard automatically

echo.
echo ============================================================
echo   VaaS Enterprise Platform - Dashboard Launcher
echo ============================================================
echo.
echo Starting services...
echo.

REM Start VaaS platform in background
echo [1/2] Starting VaaS Platform (port 8000)...
start "VaaS Platform" cmd /k "cd /d %~dp0 && python run_offline.py"

REM Wait for platform to start
timeout /t 5 /nobreak >nul

REM Start dashboard server in background  
echo [2/2] Starting Dashboard (port 3000)...
start "Dashboard Server" cmd /k "cd /d %~dp0 && python dashboard/server.py"

REM Wait for dashboard to start
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo   DASHBOARD IS READY!
echo ============================================================
echo.
echo   Open in your browser: http://localhost:3000
echo.
echo   Two windows opened:
echo   - Window 1: VaaS Platform (port 8000)
echo   - Window 2: Dashboard Server (port 3000)
echo.
echo   Close those windows to stop the services.
echo.
echo   Opening dashboard in browser...
echo ============================================================
echo.

REM Open browser
start http://localhost:3000

echo.
echo Dashboard launched! Check your browser.
echo.
echo Press any key to exit this launcher...
pause >nul

