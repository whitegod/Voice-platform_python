@echo off
REM Voice-as-a-Service - OFFLINE MODE
REM No Docker! No OpenAI! No API Keys! 100% FREE!

echo ============================================================
echo Voice-as-a-Service Platform - OFFLINE MODE
echo ============================================================
echo.
echo   NO DOCKER NEEDED!
echo   NO OPENAI API KEY NEEDED!
echo   NO INTERNET NEEDED (after setup)!
echo   100%% FREE!
echo.
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo.
    echo Download Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    echo See: INSTALL_PYTHON.md for help
    echo.
    pause
    exit /b 1
)
echo [OK] Python is installed
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment (one-time setup)...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install ONLY the minimal dependencies (no OpenAI!)
echo [INFO] Installing dependencies (one-time, takes 2-3 minutes)...
echo.
pip install -q fastapi uvicorn pydantic
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo.
    echo Try manually: pip install fastapi uvicorn pydantic
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Check for domain configs
if not exist "config\domains" (
    echo [WARNING] Domain configuration directory not found!
    echo Creating basic structure...
    mkdir config\domains
)

echo [OK] No configuration needed - Ready to go!
echo.

echo ============================================================
echo Starting VaaS Platform in OFFLINE MODE
echo ============================================================
echo.
echo FEATURES:
echo   [YES] All 19 domains working
echo   [YES] Intelligent intent recognition
echo   [YES] Conversation memory
echo   [YES] Multi-domain support
echo   [YES] Full REST API
echo   [YES] 100%% FREE - No API costs!
echo.
echo   [NO]  Voice input/output (text-only)
echo   [NO]  Database persistence (in-memory)
echo   [NO]  Cloud AI (uses rule-based AI)
echo.
echo PERFECT FOR:
echo   - Testing the platform
echo   - Learning how it works
echo   - Development
echo   - No-cost operation
echo.
echo ============================================================
echo.
echo API will start on: http://localhost:8000
echo API Docs (test here): http://localhost:8000/docs
echo.
echo Test API Key: offline_demo_key
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

REM Run the offline application
python run_offline.py

pause

