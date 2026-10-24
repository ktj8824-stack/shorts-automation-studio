@echo off
chcp 65001 > nul
echo ========================================================
echo 🎬 쇼츠 광고 제작 자동화 웹 스튜디오를 시작합니다...
echo 잠시 후 인터넷 브라우저 창이 자동으로 열립니다!
echo ========================================================
cd /d "%~dp0"
set PYTHONUTF8=1
.\.venv\Scripts\streamlit.exe run app.py --server.port 8501
pause
