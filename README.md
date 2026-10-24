# 🎬 쇼츠 & 롱폼 광고 제작 올인원 자동화 웹 스튜디오

인기 쇼츠/롱폼 영상의 성공 공식을 조회수 기반으로 탐색·역설계(Benchmarking)하고, 내 상품을 대입해 **초 단위 대본 작성 ➔ 이미지 생성 ➔ 카메라 모션 영상 변환 ➔ AI 성우 나레이션(TTS) ➔ 자막 합성 렌더링 ➔ 4대 플랫폼 멀티 업로드**까지 한곳에서 조율하는 웹 스튜디오입니다.

## 🚀 빠른 실행 방법

### 1. Windows에서 실행
- 폴더 내 `실행하기_웹스튜디오.bat` 더블클릭
- 또는 터미널에서:
```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\streamlit run app.py
```

### 2. Mac (M3 Max 등 Apple Silicon)에서 실행
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 📋 8단계 파이프라인 구조
1. **1단계 (`modules/step1_analyzer.py`)**: 고조회수(인기순) 레퍼런스 영상 탐색 + 초반 3초 연속 프레임 캡처 + 시청자 댓글 반응 + 장면별 1:1 역설계 분석
2. **2~3단계 (`modules/step2_3_planner_scripter.py`)**: 상품 맞춤 후킹 앵글 기획 & 초 단위 대본/스토리보드 생성
3. **4단계 (`modules/step4_image_gen.py`)**: 장면별 AI 이미지 생성 (`Flux` 무료 / 로컬 `ComfyUI`) & 실제 상품 사진 쇼츠 규격 자동 맞춤
4. **5단계 (`modules/step5_video_gen.py`)**: 6종 다이내믹 카메라 모션 영상 클립 변환
5. **6단계 (`modules/step6_tts.py`)**: 신경망 AI 성우 나레이션(`Edge-TTS`) 생성 및 음성 길이 측정
6. **7단계 (`modules/step7_editor.py`)**: 영상 + 음성 + 한국형 쇼츠 강조 자막 자동 합성 및 최종 `.mp4` 출력
7. **8단계 (`modules/step8_uploader.py`)**: 유튜브 쇼츠, 인스타 릴스, 틱톡, 쓰레드 맞춤 제목/해시태그/고정댓글 생성 및 업로드 연동
