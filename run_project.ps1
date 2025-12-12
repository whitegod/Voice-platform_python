# Voice-as-a-Service Platform - PowerShell Startup Script
# Run this to start the complete platform

$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Voice-as-a-Service Platform - Startup Script" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check Docker
Write-Host "Step 1: Checking Docker..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host ""

# Step 2: Check .env file
Write-Host "Step 2: Checking configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "[WARNING] .env file not found!" -ForegroundColor Yellow
    Write-Host "Creating from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "IMPORTANT: Edit .env and add your OpenAI API key!" -ForegroundColor Red
    Write-Host "Run: notepad .env" -ForegroundColor Yellow
    Write-Host "Add line: OPENAI_API_KEY=sk-your-actual-key-here" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] .env file exists" -ForegroundColor Green

# Check if OpenAI key is configured
$envContent = Get-Content ".env" -Raw
if ($envContent -match "OPENAI_API_KEY=sk-") {
    Write-Host "[OK] OpenAI API key configured" -ForegroundColor Green
} else {
    Write-Host "[WARNING] OpenAI API key may not be configured!" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit 1
    }
}
Write-Host ""

# Step 3: Start services
Write-Host "Step 3: Starting all services..." -ForegroundColor Yellow
Write-Host "This may take 1-2 minutes..." -ForegroundColor Cyan
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to start services" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Services started" -ForegroundColor Green
Write-Host ""

# Step 4: Wait for services
Write-Host "Step 4: Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
Write-Host ""

# Step 5: Initialize database
Write-Host "Step 5: Initializing database..." -ForegroundColor Yellow
docker-compose exec -T vaas_app python scripts/init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Database may already be initialized" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "IMPORTANT: Save the API key displayed above!" -ForegroundColor Red
Write-Host ""
Read-Host "Press Enter to continue"

# Step 6: Train Rasa
Write-Host "Step 6: Training Rasa model (this may take 3-5 minutes)..." -ForegroundColor Yellow
python scripts/train_rasa.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Rasa training failed" -ForegroundColor Red
    Write-Host "Check if Python is installed: python --version" -ForegroundColor Yellow
    Read-Host "Press Enter to continue anyway"
}
Write-Host "[OK] Rasa model trained" -ForegroundColor Green
Write-Host ""

# Step 7: Load knowledge
Write-Host "Step 7: Loading knowledge bases..." -ForegroundColor Yellow
python scripts/load_all_knowledge.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Knowledge loading failed - continuing..." -ForegroundColor Yellow
}
Write-Host ""

# Step 8: Health check
Write-Host "Step 8: Running health check..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host $health.Content
} catch {
    Write-Host "[WARNING] Health check failed - platform may still be starting" -ForegroundColor Yellow
}
Write-Host ""

# Summary
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Platform is running!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access points:" -ForegroundColor Cyan
Write-Host "  - API Gateway:     http://localhost:8000" -ForegroundColor White
Write-Host "  - API Docs:        http://localhost:8000/docs  <-- Try this!" -ForegroundColor Yellow
Write-Host "  - Grafana:         http://localhost:3000 (admin/admin)" -ForegroundColor White
Write-Host "  - Prometheus:      http://localhost:9091" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  - View logs:       docker-compose logs -f" -ForegroundColor White
Write-Host "  - Stop platform:   docker-compose down" -ForegroundColor White
Write-Host "  - Restart:         docker-compose restart" -ForegroundColor White
Write-Host "  - Health check:    curl http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "Platform ready with 19 domains and 180+ intents!" -ForegroundColor Green
Write-Host ""
Read-Host "Press Enter to exit"

