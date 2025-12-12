@echo off
REM Voice-as-a-Service Platform - Windows Startup Script
REM Run this to start the complete platform

echo ============================================================
echo Voice-as-a-Service Platform - Startup Script
echo ============================================================
echo.

REM Check if Docker is running
echo Step 1: Checking Docker...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo [OK] Docker is running
echo.

REM Check if .env file exists
echo Step 2: Checking configuration...
if not exist ".env" (
    echo [WARNING] .env file not found!
    echo Creating from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your OpenAI API key!
    echo Run: notepad .env
    echo Add line: OPENAI_API_KEY=sk-your-actual-key-here
    echo.
    pause
    exit /b 1
)
echo [OK] .env file exists
echo.

REM Check if OpenAI key is configured
findstr /C:"OPENAI_API_KEY=sk-" .env >nul 2>&1
if errorlevel 1 (
    echo [WARNING] OpenAI API key may not be configured!
    echo Make sure .env contains: OPENAI_API_KEY=sk-your-key-here
    echo.
    set /p continue="Continue anyway? (Y/N): "
    if /i not "%continue%"=="Y" exit /b 1
)
echo [OK] Configuration looks good
echo.

REM Start services
echo Step 3: Starting all services...
echo This may take 1-2 minutes...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start services
    pause
    exit /b 1
)
echo [OK] Services started
echo.

REM Wait for services to be ready
echo Step 4: Waiting for services to initialize...
timeout /t 30 /nobreak
echo.

REM Initialize database
echo Step 5: Initializing database...
docker-compose exec -T vaas_app python scripts/init_db.py
if errorlevel 1 (
    echo [WARNING] Database may already be initialized
)
echo.
echo IMPORTANT: Save the API key displayed above!
echo.
pause

REM Train Rasa
echo Step 6: Training Rasa model (this may take 3-5 minutes)...
python scripts/train_rasa.py
if errorlevel 1 (
    echo [ERROR] Rasa training failed
    echo Check if Python is installed: python --version
    pause
    exit /b 1
)
echo [OK] Rasa model trained
echo.

REM Load knowledge
echo Step 7: Loading knowledge bases...
python scripts/load_all_knowledge.py
if errorlevel 1 (
    echo [WARNING] Knowledge loading failed - continuing...
)
echo.

REM Health check
echo Step 8: Running health check...
timeout /t 10 /nobreak
curl -s http://localhost:8000/health
echo.
echo.

REM Summary
echo ============================================================
echo Platform is running!
echo ============================================================
echo.
echo Access points:
echo   - API Gateway:     http://localhost:8000
echo   - API Docs:        http://localhost:8000/docs  ^<-- Try this!
echo   - Grafana:         http://localhost:3000 (admin/admin)
echo   - Prometheus:      http://localhost:9091
echo.
echo Next steps:
echo   1. Save your API key (shown above)
echo   2. Test API at: http://localhost:8000/docs
echo   3. Try different domains: customer_support, healthcare, ecommerce, etc.
echo.
echo Useful commands:
echo   - View logs:       docker-compose logs -f
echo   - Stop platform:   docker-compose down
echo   - Restart:         docker-compose restart
echo.
pause

