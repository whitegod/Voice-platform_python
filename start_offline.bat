@echo off
REM Ultra-Simple Offline Launcher
REM No configuration needed!

echo.
echo ============================================================
echo   Voice-as-a-Service - FREE OFFLINE MODE
echo ============================================================
echo.
echo   NO Docker Required!
echo   NO API Keys Required!
echo   NO Configuration Required!
echo   100%% FREE!
echo.
echo ============================================================
echo.

REM Step 1: Check Python
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo.
    echo During installation, make sure to:
    echo   [X] Add Python to PATH  ^<-- Check this box!
    echo.
    echo After installing Python, run this script again.
    echo.
    pause
    exit /b 1
)

echo OK - Python is ready
echo.

REM Step 2: Install required packages (if needed)
echo Installing required packages (one-time only)...
pip install --quiet fastapi uvicorn pydantic 2>nul
if errorlevel 1 (
    echo Installing packages...
    pip install fastapi uvicorn pydantic
)
echo OK - Packages ready
echo.

REM Step 3: Run the application
echo ============================================================
echo Starting Platform...
echo ============================================================
echo.
echo This will open on: http://localhost:8000
echo.
echo To test: http://localhost:8000/docs
echo API Key: offline_demo_key
echo.
echo Press Ctrl+C to stop
echo.

python run_offline.py

pause

