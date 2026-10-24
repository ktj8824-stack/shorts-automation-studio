@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set PY=.venv\Scripts\python.exe) else (set PY=python)
start "" "http://localhost:8501"
%PY% -m streamlit run app.py --server.port 8501 --server.headless true
pause
