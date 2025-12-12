@echo off
REM Start VaaS Admin Dashboard

echo ============================================================
echo VaaS Platform - Admin Dashboard
echo ============================================================
echo.
echo Starting dashboard server...
echo.
echo Dashboard will be available at: http://localhost:3000
echo.
echo Make sure VaaS platform is running on port 8000!
echo.
echo ============================================================
echo.

python dashboard/server.py

pause

