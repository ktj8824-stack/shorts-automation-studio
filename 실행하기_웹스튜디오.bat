@echo off
cd /d "%~dp0"
set PYTHONUTF8=1

REM 1. 이미 8501 포트에서 서버가 켜져 있는지 확인
netstat -ano | findstr ":8501 " | findstr "LISTENING" > nul
if %errorlevel%==0 (
    echo [Shorts Studio] 서버가 이미 실행 중입니다! 브라우저 창을 엽니다...
    start http://localhost:8501
    exit /b 0
)

REM 2. 서버가 꺼져 있으면 가상환경 확인 후 서버 시작 (브라우저 자동 열림)
echo ========================================================
echo [Shorts Automation Studio] 웹 스튜디오 서버를 시작합니다...
echo 잠시 후 인터넷 창(http://localhost:8501)이 자동으로 열립니다!
echo ========================================================
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
)
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8501 --server.headless false
pause
