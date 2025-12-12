@echo off
REM Simple VaaS Runner - No Docker Required!

echo ============================================================
echo Voice-as-a-Service Platform - Simplified Mode (No Docker)
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
    pause
    exit /b 1
)
echo [OK] Python is installed
echo.

REM Check .env file
if not exist ".env" (
    echo [INFO] Creating .env file...
    
    REM Create .env from template if it exists
    if exist ".env.template" (
        copy .env.template .env
    ) else if exist ".env.example" (
        copy .env.example .env
    ) else (
        REM Create basic .env file directly
        echo # Voice-as-a-Service Configuration > .env
        echo OPENAI_API_KEY=your-openai-api-key-here >> .env
        echo OPENAI_MODEL=gpt-4-turbo-preview >> .env
        echo ENVIRONMENT=development >> .env
        echo DEBUG=true >> .env
        echo LOG_LEVEL=INFO >> .env
        echo API_HOST=0.0.0.0 >> .env
        echo API_PORT=8000 >> .env
    )
    
    echo [OK] .env file created
    echo.
    echo ============================================================
    echo IMPORTANT: Add your OpenAI API key!
    echo ============================================================
    echo.
    echo Opening .env in Notepad...
    echo.
    echo Please REPLACE this line:
    echo   OPENAI_API_KEY=your-openai-api-key-here
    echo.
    echo With your actual key:
    echo   OPENAI_API_KEY=sk-your-actual-key-from-openai
    echo.
    echo Get your key from: https://platform.openai.com/api-keys
    echo.
    echo After saving and closing Notepad, run this script again.
    echo ============================================================
    echo.
    
    notepad .env
    pause
    exit /b 0
)

REM Check if OpenAI key is configured
findstr /C:"OPENAI_API_KEY=sk-" .env >nul 2>&1
if errorlevel 1 (
    echo [WARNING] OpenAI API key not configured!
    echo.
    echo Edit .env and add your OpenAI API key:
    echo OPENAI_API_KEY=sk-your-key-here
    echo.
    echo Get your key from: https://platform.openai.com/api-keys
    echo.
    set /p continue="Continue anyway? (Y/N): "
    if /i not "%continue%"=="Y" exit /b 1
)
echo [OK] OpenAI API key configured
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
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

REM Install dependencies
echo [INFO] Installing minimal dependencies...
echo This may take 2-3 minutes on first run...
echo.
pip install -q -r requirements_minimal.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    echo.
    echo Try manually: pip install fastapi uvicorn openai pydantic python-dotenv
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Run the simplified server
echo ============================================================
echo Starting VaaS Platform in Simplified Mode
echo ============================================================
echo.
echo ✅ No Docker required!
echo ✅ Uses OpenAI for all AI tasks
echo ✅ In-memory storage (no database needed)
echo ✅ All 19 domains working!
echo.
echo The platform will start on: http://localhost:8000
echo API Docs will be at: http://localhost:8000/docs
echo.
echo Test API key: demo_key_12345
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

REM Run the application
python run_simple.py

pause

