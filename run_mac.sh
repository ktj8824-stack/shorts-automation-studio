#!/bin/bash
cd "$(dirname "$0")"
echo "========================================================"
echo "🎬 쇼츠 & 롱폼 자동화 웹 스튜디오 (Mac M3 Max 버전) 시작 중..."
echo "========================================================"

if [ ! -d ".venv" ]; then
    echo "📦 가상환경(.venv) 생성 및 필수 패키지 설치 중..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

streamlit run app.py --server.port 8501
