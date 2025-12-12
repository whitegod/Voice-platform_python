@echo off
echo ============================================================
echo   CLEAN START - Removing cache and restarting
echo ============================================================
echo.

echo Step 1: Killing old Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 1 /nobreak > nul

echo Step 2: Cleaning Python cache files...
del /s /q *.pyc 2>nul
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

echo Step 3: Starting server with FIXED natural conversation...
echo.
echo ✅ No more robotic "help - I can help you with: search_property..."
echo ✅ Now responds naturally!
echo.
echo Opening in browser shortly...
echo Server URL: http://localhost:8000/docs
echo.

timeout /t 2 /nobreak > nul
start http://localhost:8000/docs

python run_offline.py

pause

