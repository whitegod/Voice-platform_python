@echo off
echo ============================================================
echo   Testing Natural Conversation - NO MORE ROBOTIC RESPONSES!
echo ============================================================
echo.
echo Starting server in background...
start /B python run_offline.py
echo Waiting 5 seconds for server to start...
timeout /t 5 /nobreak > nul
echo.
echo ============================================================
echo   TEST 1: "I need a room"
echo ============================================================
echo.
curl -X POST "http://localhost:8000/api/v1/process/text" -H "Content-Type: application/json" -d "{\"text\": \"I need a room\", \"user_id\": \"test\", \"domain\": \"real_estate\"}"
echo.
echo.
echo ============================================================
echo   TEST 2: "$5500, 3 rooms, in London"
echo ============================================================
echo.
curl -X POST "http://localhost:8000/api/v1/process/text" -H "Content-Type: application/json" -d "{\"text\": \"$5500, 3 rooms, in london\", \"user_id\": \"test\", \"domain\": \"real_estate\"}"
echo.
echo.
echo ============================================================
echo   TEST 3: "Calculate mortgage"
echo ============================================================
echo.
curl -X POST "http://localhost:8000/api/v1/process/text" -H "Content-Type: application/json" -d "{\"text\": \"Calculate mortgage\", \"user_id\": \"test\", \"domain\": \"real_estate\"}"
echo.
echo.
echo ============================================================
echo   Tests complete! Check the responses above.
echo   Open http://localhost:8000/docs to test more.
echo ============================================================
echo.
pause

