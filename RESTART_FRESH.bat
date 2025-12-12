@echo off
echo ============================================================
echo   FRESH RESTART - Killing old server and starting new one
echo ============================================================
echo.

echo Killing any running Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak > nul

echo.
echo Starting fresh server with NATURAL conversation...
echo.
echo Open in browser: http://localhost:8000/docs
echo.

python run_offline.py

pause

