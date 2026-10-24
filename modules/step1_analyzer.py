"""
[1단계 업그레이드: 고조회수 벤치마킹 영상 탐색기 & 심층 역설계(Reverse-Engineering) 분석 엔진]
- 기능 1 (인기순/조회수순 정밀 검색): 유튜브 Protobuf 필터(sp)를 활용해 조회수 수십만~수백만 회 이상의 검증된 쇼츠 및 롱폼 영상을 탐색
- 기능 2 (후보 영상 미리보기): 무작정 다운로드하지 않고 [썸네일, 실제 조회수, 길이, 채널명]을 먼저 확인 후 원하는 고퀄리티 영상만 선택 분석
- 기능 3 (심층 벤치마킹 해부):
  1) 초반 3초 후킹 연속 캡처 (0.5초 / 1.5초 / 2.5초 프레임)
  2) 실제 시청자 베스트 댓글 수집 및 구매 전환 트리거 분석
  3) 장면(컷)별 캡처 이미지 + 해당 구간 나레이션 대사 1:1 매칭 역설계 스토리보드
  4) 이 영상의 구조/템포를 2~3단계 내 대본 생성기로 즉시 복제(Clone)하는 벤치마킹 데이터 생성
"""

import os
import sys
import json
import base64
import subprocess
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any

import cv2
import numpy as np
import yt_dlp
import imageio_ffmpeg
from faster_whisper import WhisperModel
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def get_ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def create_project_dirs(project_name: str) -> Dict[str, Path]:
    base_dir = Path(__file__).resolve().parent.parent / "workspace" / project_name
    dirs = {
        "base": base_dir,
        "step1_ref": base_dir / "1_reference",
        "step2_3_script": base_dir / "2_3_script",
        "step4_5_visuals": base_dir / "4_5_visuals",
        "step6_audio": base_dir / "6_audio",
        "step7_output": base_dir / "7_output",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def build_youtube_search_url(
    keyword: str,
    sort_by: str = "조회수 높은순 (인기순)",
    duration_filter: str = "숏폼/짧은 영상 (4분 미만)",
) -> str:
    """
    유튜브 검색 필터(sp 파라미터)를 정확히 생성하여 조회수 폭발 영상만 타겟팅합니다.
    """
    q = urllib.parse.quote(keyword)

    # Protobuf bytes 구성
    # sort: 3(조회수순), 2(업로드순), 0(관련도순)
    if "조회수" in sort_by:
        sort_byte = 3
    elif "최신" in sort_by:
        sort_byte = 2
    else:
        sort_byte = 0

    # duration: 1(4분 미만 Short), 3(4~20분 Medium), 2(20분 이상 Long)
    if "4분 미만" in duration_filter or "숏폼" in duration_filter:
        dur_bytes = [0x10, 0x01, 0x18, 0x01]  # Video + Short
    elif "롱폼" in duration_filter:
        dur_bytes = [0x10, 0x01, 0x18, 0x03]  # Video + 4~20min
    else:
        dur_bytes = [0x10, 0x01]  # Video 전체

    proto = bytes([0x08, sort_byte, 0x12, len(dur_bytes)] + dur_bytes)
    sp = urllib.parse.quote(base64.b64encode(proto).decode("ascii"))
    return f"https://www.youtube.com/results?search_query={q}&sp={sp}"


def search_benchmark_candidates(
    keyword: str,
    sort_by: str = "조회수 높은순 (인기순)",
    duration_filter: str = "숏폼/짧은 영상 (4분 미만)",
    min_views: int = 10000,
    max_candidates: int = 12,
) -> List[Dict[str, Any]]:
    """
    무작정 다운로드하지 않고, 먼저 조회수가 검증된 고퀄리티 후보 영상 목록을 빠르게 스캔하여 반환합니다.
    """
    search_url = build_youtube_search_url(keyword, sort_by, duration_filter)
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "playlistend": 30,
        "no_warnings": True,
    }

    candidates: List[Dict[str, Any]] = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        res = ydl.extract_info(search_url, download=False)
        entries = res.get("entries", []) if res else []

        for entry in entries:
            if not entry:
                continue
            vid = entry.get("id")
            if not vid:
                continue
            views = entry.get("view_count") or 0
            dur = entry.get("duration") or 0

            if views < min_views:
                continue

            thumbs = entry.get("thumbnails") or []
            thumb_url = thumbs[-1].get("url") if thumbs else f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
            video_url = entry.get("url") or f"https://www.youtube.com/watch?v={vid}"
            if not video_url.startswith("http"):
                video_url = f"https://www.youtube.com/watch?v={vid}"

            candidates.append({
                "id": vid,
                "title": entry.get("title", "제목 없음"),
                "channel": entry.get("channel") or entry.get("uploader") or "채널 미상",
                "view_count": int(views),
                "duration": int(dur),
                "thumbnail": thumb_url,
                "url": video_url,
            })

    # 조회수 높은 순으로 한 번 더 정렬
    candidates.sort(key=lambda x: x["view_count"], reverse=True)
    return candidates[:max_candidates]


def download_by_url(url: str, output_dir: Path, fetch_comments: bool = True) -> Dict[str, Any]:
    """
    선택한 고퀄리티 영상(또는 직접 입력한 유튜브/틱톡/인스타 URL)과 베스트 댓글을 함께 다운로드합니다.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = get_ffmpeg_path()

    ydl_opts = {
        "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "ffmpeg_location": ffmpeg_exe,
        "merge_output_format": "mp4",
        "getcomments": fetch_comments,
        "extractor_args": {"youtube": {"max_comments": ["20", "20", "0", "0"], "comment_sort": ["top"]}},
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info.get("id", "video")
        video_path = output_dir / f"{video_id}.mp4"

        raw_comments = info.get("comments") or []
        top_comments = []
        for c in raw_comments[:15]:
            txt = (c.get("text") or "").strip()
            if txt:
                top_comments.append({
                    "author": c.get("author", ""),
                    "text": txt,
                    "likes": c.get("like_count") or 0,
                })

        metadata = {
            "id": video_id,
            "title": info.get("title", ""),
            "uploader": info.get("uploader") or info.get("channel") or "",
            "view_count": info.get("view_count") or 0,
            "like_count": info.get("like_count") or 0,
            "comment_count": info.get("comment_count") or len(top_comments),
            "duration": info.get("duration") or 0,
            "description": info.get("description") or "",
            "tags": info.get("tags") or [],
            "top_comments": top_comments,
            "webpage_url": info.get("webpage_url", url),
            "local_video_path": str(video_path),
        }

        meta_path = output_dir / f"{video_id}_meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata


def search_and_download_by_keyword(
    keyword: str, output_dir: Path, max_results: int = 1, min_views: int = 10000
) -> List[Dict[str, Any]]:
    """인기순 검색 후 상위 고조회수 영상을 다운로드합니다."""
    candidates = search_benchmark_candidates(keyword, min_views=min_views, max_candidates=max_results * 2)
    collected = []
    for cand in candidates[:max_results]:
        try:
            meta = download_by_url(cand["url"], output_dir)
            collected.append(meta)
        except Exception as e:
            print(f"⚠️ 다운로드 건너뜀: {e}")
    return collected


def extract_visual_scenes_opencv(video_path: Path, frames_dir: Path) -> Dict[str, Any]:
    """
    1) 초반 3초 후킹 프레임 연속 캡처 (0.5초, 1.5초, 2.5초)
    2) 전체 영상의 컷 전환(Scene Cut) 감지 및 대표 프레임 저장
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"영상을 열 수 없습니다: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = round(total_frames / fps, 2) if fps > 0 else 0

    # 1. 초반 3초 후킹 프레임 3장 (0.5초, 1.5초, 2.5초) 캡처
    hook_frames = []
    for hk_sec in [0.5, 1.5, 2.5]:
        if hk_sec < duration:
            cap.set(cv2.CAP_PROP_POS_MSEC, hk_sec * 1000)
            ret, frm = cap.read()
            if ret:
                hk_path = frames_dir / f"hook_{hk_sec:.1f}s.jpg"
                ok, enc = cv2.imencode(".jpg", frm)
                if ok:
                    enc.tofile(str(hk_path))
                    hook_frames.append({"time_sec": hk_sec, "image_path": str(hk_path)})

    # 2. 전체 컷 전환 스캔
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    prev_hist = None
    cut_timestamps = [0.0]
    saved_frames = []

    frame_idx = 0
    sample_interval = max(1, int(fps / 5))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_interval == 0:
            current_sec = round(frame_idx / fps, 2)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
            cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)

            is_cut = False
            if prev_hist is None:
                is_cut = True
            else:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                if diff < 0.65 and (current_sec - cut_timestamps[-1]) >= 0.8:
                    is_cut = True

            if is_cut:
                if current_sec > 0:
                    cut_timestamps.append(current_sec)
                if len(saved_frames) < 16:
                    img_name = f"scene_{len(saved_frames)+1:02d}_{current_sec:.1f}s.jpg"
                    img_path = frames_dir / img_name
                    ok, encoded_img = cv2.imencode(".jpg", frame)
                    if ok:
                        encoded_img.tofile(str(img_path))
                        saved_frames.append({"time_sec": current_sec, "image_path": str(img_path)})

            prev_hist = hist
        frame_idx += 1

    cap.release()

    total_cuts = len(cut_timestamps)
    avg_cut_len = round(duration / max(1, total_cuts), 2)

    return {
        "resolution": f"{width}x{height}",
        "fps": round(fps, 1),
        "duration_sec": duration,
        "total_cuts": total_cuts,
        "avg_cut_duration_sec": avg_cut_len,
        "cut_timestamps": cut_timestamps,
        "hook_3s_frames": hook_frames,
        "captured_keyframes": saved_frames,
    }


def load_audio_ffmpeg(video_path: Path, sr: int = 16000) -> np.ndarray:
    ffmpeg_exe = get_ffmpeg_path()
    cmd = [
        ffmpeg_exe,
        "-nostdin",
        "-threads", "0",
        "-i", str(video_path),
        "-f", "s16le",
        "-ac", "1",
        "-acodec", "pcm_s16le",
        "-ar", str(sr),
        "-",
    ]
    out = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0


def transcribe_audio_local(video_path: Path) -> Dict[str, Any]:
    audio_array = load_audio_ffmpeg(video_path)
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments_gen, info = model.transcribe(audio_array, language="ko", beam_size=5)

    segments = []
    full_text_list = []
    first_3s_text = []

    for seg in segments_gen:
        text = seg.text.strip()
        start_t = round(seg.start, 2)
        end_t = round(seg.end, 2)
        segments.append({"start": start_t, "end": end_t, "text": text})
        full_text_list.append(text)
        if start_t <= 4.0:
            first_3s_text.append(text)

    return {
        "language": info.language,
        "first_3_seconds_hook_script": " ".join(first_3s_text),
        "full_transcript": " ".join(full_text_list),
        "segments": segments,
    }


def analyze_audience_comments(top_comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """수집된 베스트 댓글을 분석하여 시청자의 주요 반응(구매 문의, 공감, 가격 반응 등)을 도출합니다."""
    if not top_comments:
        return {
            "comment_summary": "댓글 데이터가 없거나 비활성화된 영상입니다.",
            "buying_signals": [],
            "top_comments_sample": [],
        }

    buying_keywords = ["링크", "어디", "얼마", "정보", "좌표", "구매", "쿠팡", "사야", "사고", "품절", "추천"]
    buying_signals = []
    for c in top_comments:
        if any(k in c["text"] for k in buying_keywords):
            buying_signals.append(c["text"])

    return {
        "comment_summary": f"수집된 인기 댓글 {len(top_comments)}개 중 구매/정보 관심 반응 {len(buying_signals)}건 감지",
        "buying_signals": buying_signals[:5],
        "top_comments_sample": top_comments[:8],
    }


def build_marketing_analysis(
    video_meta: Dict[str, Any],
    visual_info: Dict[str, Any],
    audio_info: Dict[str, Any],
) -> Dict[str, Any]:
    hook_text = audio_info.get("first_3_seconds_hook_script") or "(초반 나레이션 없음 - 시각/음악 후킹)"
    full_script = audio_info.get("full_transcript") or ""
    segments = audio_info.get("segments", [])
    duration = visual_info.get("duration_sec") or video_meta.get("duration") or 30
    keyframes = visual_info.get("captured_keyframes", [])

    # 후킹 유형 정밀 분류
    hook_type = "직관적 제품 시연 & 시각 충격형"
    if any(k in hook_text for k in ["?", "아직도", "설마", "왜", "모르", "이걸"]):
        hook_type = "질문 / 호기심 자극형"
    elif any(k in hook_text for k in ["절대", "사지", "마세요", "주의", "단점", "후회", "큰일"]):
        hook_type = "경고 / 역발상 반전 후킹형"
    elif any(k in hook_text for k in ["쿠팡", "가성비", "천원", "만원", "할인", "꿀템", "추천", "1위"]):
        hook_type = "가성비 / 랭킹 추천형"

    # 문장 구간별 설득 역할 + 가장 가까운 캡처 프레임 1:1 매칭
    scenes_breakdown = []
    for idx, seg in enumerate(segments):
        s_t = seg["start"]
        e_t = seg["end"]
        ratio = s_t / max(1.0, duration)
        if s_t <= 4.0:
            role = "🪝 1. 초반 후킹 (시선 강탈)"
        elif ratio < 0.30:
            role = "😫 2. 문제 제기 & 공감"
        elif ratio < 0.80:
            role = "✨ 3. 핵심 기능 & 장점 시연"
        else:
            role = "🛒 4. 결론 & 구매 유도(CTA)"

        # 해당 시간대에 가장 가까운 캡처 이미지 매칭
        matched_img = ""
        if keyframes:
            closest_kf = min(keyframes, key=lambda k: abs(k["time_sec"] - s_t))
            matched_img = closest_kf["image_path"]

        scenes_breakdown.append({
            "scene_no": idx + 1,
            "time_range": f"{s_t:05.2f}s ~ {e_t:05.2f}s",
            "duration_sec": round(max(2.0, e_t - s_t), 1),
            "narration": seg["text"],
            "role": role,
            "matched_frame": matched_img,
        })

    comment_analysis = analyze_audience_comments(video_meta.get("top_comments", []))

    return {
        "summary": (
            f"조회수 {video_meta.get('view_count', 0):,}회 달성! "
            f"총 {duration}초 동안 {visual_info.get('total_cuts')}번의 화면 전환(평균 {visual_info.get('avg_cut_duration_sec')}초/컷)으로 구성된 검증된 레퍼런스 영상"
        ),
        "hook_analysis": {
            "first_3_seconds_audio": hook_text,
            "hook_type": hook_type,
            "why_it_works": (
                f"초반 3초에 '{hook_text}' 대사로 호기심을 자극하고, "
                f"평균 {visual_info.get('avg_cut_duration_sec')}초 간격의 빠른 화면 전환으로 시청자 이탈을 막음"
            ),
        },
        "script_structure": {
            "full_transcript": full_script,
            "segment_count": len(segments),
        },
        "audience_reaction": comment_analysis,
        "visual_and_editing": visual_info,
        "scenes_breakdown": scenes_breakdown,
        "winning_formula_for_our_ad": {
            "recommended_duration": f"{int(duration)}초",
            "recommended_cut_speed": f"{visual_info.get('avg_cut_duration_sec')}초",
            "benchmark_hook": hook_text,
            "reusable_hook_template": [
                f"[원본 응용] {hook_text[:20]}... 아직도 이거 없이 고생하세요?",
                "쿠팡에서 후기 폭발 중인 삶의 질 수직 상승 꿀템 TOP 픽!",
                "솔직히 이건 왜 이제 샀나 후회되는 가성비 끝판왕 아이템!",
            ],
        },
    }


def analyze_video(video_meta: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    video_id = video_meta["id"]
    video_path = Path(video_meta["local_video_path"])
    frames_dir = output_dir / f"{video_id}_frames"

    visual_info = extract_visual_scenes_opencv(video_path, frames_dir)
    audio_info = transcribe_audio_local(video_path)
    analysis_data = build_marketing_analysis(video_meta, visual_info, audio_info)

    json_path = output_dir / f"{video_id}_analysis.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)

    return analysis_data
