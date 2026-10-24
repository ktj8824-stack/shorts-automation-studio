"""
[5단계: 이미지를 역동적인 영상 클립으로 변환하는 모듈 (I2V & 다이내믹 카메라 모션)]
- 모드 1 (다이내믹 카메라 모션 엔진): 6가지 카메라 무빙(빠른 줌인, 부드러운 줌인, 줌아웃, 좌우 패닝, 상하 틸트, 강조 진동 줌)을
  30fps 부드러운 H.264 MP4 영상으로 고속 렌더링
- 모드 2 (로컬 AI 비디오 - ComfyUI Wan 2.1 / LTX-Video 연동): M3 Max 맥북 등에서 로컬 비디오 AI 서버 호출 지원
"""

import math
import subprocess
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image
import imageio_ffmpeg

MOTION_OPTIONS = [
    "빠른 줌인 (Fast Zoom-In)",
    "부드러운 줌인 (Slow Zoom-In)",
    "줌아웃 (Zoom-Out)",
    "좌우 패닝 (Pan Left-to-Right)",
    "상하 틸트 (Tilt Up)",
    "강조 줌인 & 진동 효과 (Pulse Zoom)",
]


def get_ffmpeg_exe() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def render_dynamic_motion_clip(
    image_path: Path,
    output_mp4_path: Path,
    motion_type: str = "부드러운 줌인 (Slow Zoom-In)",
    duration_sec: float = 4.0,
    fps: int = 30,
) -> Path:
    """
    정지 이미지(PNG/JPG)에 역동적인 카메라 모션을 적용하여 브라우저 및 모든 플랫폼에서
    즉시 재생 가능한 H.264(yuv420p) MP4 영상 클립을 생성합니다.
    """
    output_mp4_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    # 짝수 해상도 보장 (H.264 인코딩 필수 조건)
    w = (w // 2) * 2
    h = (h // 2) * 2
    if img.size != (w, h):
        img = img.resize((w, h), Image.Resampling.LANCZOS)

    total_frames = max(15, int(duration_sec * fps))
    ffmpeg_exe = get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "ultrafast",
        "-crf", "22",
        str(output_mp4_path),
    ]

    # 원본 이미지를 1.25배 크게 미리 확대해 두고 크롭 윈도우를 이동시켜 부드러운 모션 구현
    overscale = 1.28
    big_w, big_h = int(w * overscale), int(h * overscale)
    big_img = img.resize((big_w, big_h), Image.Resampling.BICUBIC)
    big_arr = np.asarray(big_img, dtype=np.uint8)

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        for f_idx in range(total_frames):
            t = f_idx / max(1, total_frames - 1)  # 0.0 ~ 1.0 진행률

            if "빠른 줌인" in motion_type:
                # 초반 0.4초 동안 빠르게 확대된 후 천천히 전진
                ease_t = 1 - pow(1 - t, 3)
                zoom = 1.0 + 0.24 * ease_t
                cx, cy = 0.5, 0.5
            elif "줌아웃" in motion_type:
                zoom = 1.24 - 0.22 * t
                cx, cy = 0.5, 0.5
            elif "좌우 패닝" in motion_type:
                zoom = 1.18
                cx = 0.25 + 0.50 * t
                cy = 0.5
            elif "상하 틸트" in motion_type:
                zoom = 1.18
                cx = 0.5
                cy = 0.75 - 0.50 * t
            elif "진동" in motion_type or "Pulse" in motion_type:
                pulse = 0.03 * math.sin(t * math.pi * 6)
                zoom = 1.12 + 0.10 * t + abs(pulse)
                cx = 0.5 + 0.015 * math.sin(t * math.pi * 12)
                cy = 0.5 + 0.015 * math.cos(t * math.pi * 12)
            else:
                # 부드러운 줌인 (Slow Zoom-In)
                zoom = 1.0 + 0.18 * t
                cx, cy = 0.5, 0.5

            crop_w = int(big_w / zoom)
            crop_h = int(big_h / zoom)
            max_x = max(0, big_w - crop_w)
            max_y = max(0, big_h - crop_h)

            x1 = int(max_x * min(1.0, max(0.0, cx)))
            y1 = int(max_y * min(1.0, max(0.0, cy)))

            cropped = big_arr[y1 : y1 + crop_h, x1 : x1 + crop_w]
            frame_pil = Image.fromarray(cropped).resize((w, h), Image.Resampling.BILINEAR)
            proc.stdin.write(frame_pil.tobytes())
    finally:
        if proc.stdin:
            proc.stdin.close()
        proc.wait()

    return output_mp4_path
