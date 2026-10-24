@echo off
cd /d "%~dp0"
chcp 65001 > nul
echo ========================================================
echo [Shorts Automation Studio] Starting Web Studio Server...
echo Browser will open at http://localhost:8501
echo ========================================================
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
)
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501
pause
