@echo off
echo Killing Python processes...
taskkill /F /FI "IMAGENAME eq python.exe" >nul 2>&1
timeout /t 2 /nobreak >nul
echo Starting backend...
cd /d D:\OwnProjects\mealmate_y\backend
"D:\OwnProjects\mealmate_y\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
