"""
[6단계: AI 성우 나레이션(TTS) 생성 및 음성 길이/자막 타임스탬프 추출 모듈]
- 무료 고품질 신경망 성우(Microsoft Edge-TTS) 기본 탑재 (선희 / 인준 / 현수)
- 배속(예: +15%) 및 톤 조절 지원
- 생성된 MP3 파일의 정확한 재생 시간(초)을 측정하여 5단계 영상 길이 및 7단계 자막 싱크에 자동 반영
"""

import asyncio
import re
import subprocess
from pathlib import Path
from typing import Dict, Any

import edge_tts
import imageio_ffmpeg

VOICE_PRESETS = {
    "👩 선희 (SunHi - 밝고 또렷한 쇼츠 추천 1위 여성 톤)": "ko-KR-SunHiNeural",
    "👨 인준 (InJoon - 신뢰감 있고 깔끔한 정보 전달 남성 톤)": "ko-KR-InJoonNeural",
    "🧑 현수 (Hyunsu - 차분하고 깊이 있는 스토리텔링 남성 톤)": "ko-KR-HyunsuMultilingualNeural",
}


def get_audio_duration_sec(audio_path: Path) -> float:
    """내장 ffmpeg를 이용해 생성된 오디오 파일(.mp3)의 정확한 길이(초)를 측정합니다."""
    if not audio_path.exists():
        return 3.5
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg_exe, "-i", str(audio_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    stderr_text = proc.stderr or ""
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", stderr_text)
    if match:
        hours = int(match.group(1))
        mins = int(match.group(2))
        secs = float(match.group(3))
        return round(hours * 3600 + mins * 60 + secs, 2)
    return 4.0


async def _synthesize_edge_tts_async(
    text: str,
    voice_id: str,
    rate_str: str,
    pitch_str: str,
    output_mp3_path: Path,
) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice_id, rate=rate_str, pitch=pitch_str)
    await communicate.save(str(output_mp3_path))


def generate_scene_tts(
    text: str,
    output_mp3_path: Path,
    voice_label: str = "👩 선희 (SunHi - 밝고 또렷한 쇼츠 추천 1위 여성 톤)",
    speed_percent: int = 15,
    pitch_hz: int = 0,
) -> Dict[str, Any]:
    """
    단일 장면의 나레이션 대사를 MP3로 생성하고 정확한 음성 길이를 반환합니다.
    """
    output_mp3_path.parent.mkdir(parents=True, exist_ok=True)
    voice_id = VOICE_PRESETS.get(voice_label, "ko-KR-SunHiNeural")
    rate_str = f"{speed_percent:+d}%"
    pitch_str = f"{pitch_hz:+d}Hz"

    clean_text = text.strip() or "주목해 주세요!"

    asyncio.run(
        _synthesize_edge_tts_async(
            text=clean_text,
            voice_id=voice_id,
            rate_str=rate_str,
            pitch_str=pitch_str,
            output_mp3_path=output_mp3_path,
        )
    )

    dur = get_audio_duration_sec(output_mp3_path)
    return {
        "audio_path": str(output_mp3_path),
        "duration_sec": dur,
        "voice_id": voice_id,
        "text": clean_text,
    }
