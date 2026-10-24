@echo off
cd /d "%~dp0"
set PYTHONUTF8=1

netstat -ano | findstr ":8501 " | findstr "LISTENING" > nul
if %errorlevel%==0 (
    start http://localhost:8501
    exit /b 0
)

echo ========================================================
echo [Shorts Automation Studio] Starting Web Studio Server...
echo Opening http://localhost:8501 in your browser...
echo ========================================================

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)

".venv\Scripts\python.exe" -m streamlit run app.py --server.port 8501 --server.headless false
pause
