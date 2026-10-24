"""
쇼츠 & 롱폼 자동화 시스템 - 4~8단계 통합 실행 및 검증 스크립트
"""

import json
from pathlib import Path

from modules.step4_image_gen import generate_image_pollinations_flux, STYLE_PRESETS
from modules.step5_video_gen import render_dynamic_motion_clip
from modules.step6_tts import generate_scene_tts, VOICE_PRESETS
from modules.step7_editor import render_scene_with_subtitles_and_audio, concat_scenes_to_final_video
from modules.step8_uploader import generate_upload_metadata, save_upload_package


def run_project_pipeline(project_name: str = "coupang_001") -> None:
    base = Path(__file__).resolve().parent / "workspace" / project_name
    sb_file = base / "2_3_script" / "storyboard_script.json"
    if not sb_file.exists():
        raise FileNotFoundError(f"대본 파일이 없습니다: {sb_file}")

    data = json.loads(sb_file.read_text(encoding="utf-8"))
    storyboard = data["storyboard"]

    v_dir = base / "4_5_visuals"
    a_dir = base / "6_audio"
    o_dir = base / "7_output"

    style = list(STYLE_PRESETS.keys())[0]
    voice = list(VOICE_PRESETS.keys())[0]
    rendered_scenes = []

    for scene in storyboard:
        s_no = scene["scene_no"]
        img_p = v_dir / f"scene_{s_no:02d}.png"
        clip_p = v_dir / f"clip_{s_no:02d}.mp4"
        mp3_p = a_dir / f"tts_{s_no:02d}.mp3"
        out_scene_p = o_dir / f"rendered_scene_{s_no:02d}.mp4"

        print(f"\n--- [Scene #{s_no}] 처리 중 ---")
        if not img_p.exists():
            print(f"🎨 4단계: 이미지 생성 중 -> {img_p.name}")
            generate_image_pollinations_flux(
                scene["visual_prompt_en"], style, img_p, seed=100 + s_no
            )

        print(f"🎙️ 6단계: AI 성우 나레이션 생성 중 -> {mp3_p.name}")
        tts_info = generate_scene_tts(scene["narration"], mp3_p, voice_label=voice, speed_percent=15)

        print(f"🎥 5단계: 모션 영상 클립 변환 중 -> {clip_p.name} ({tts_info['duration_sec']}초)")
        render_dynamic_motion_clip(
            img_p, clip_p, motion_type=scene["camera_motion"], duration_sec=tts_info["duration_sec"]
        )

        print(f"✂️ 7단계: 자막 + 나레이션 + 모션 영상 합성 중 -> {out_scene_p.name}")
        render_scene_with_subtitles_and_audio(
            image_path=img_p,
            audio_path=mp3_p,
            output_scene_mp4=out_scene_p,
            narration_text=scene["narration"],
            highlight_badge=scene.get("subtitle_highlight", ""),
            motion_type=scene["camera_motion"],
        )
        rendered_scenes.append(out_scene_p)

    final_mp4 = o_dir / f"{project_name}_final_shorts.mp4"
    print(f"\n🔗 전체 장면 병합 중 -> {final_mp4}")
    concat_scenes_to_final_video(rendered_scenes, final_mp4)

    print("📤 8단계: 4대 플랫폼 업로드 패키지 생성 중...")
    meta_pkg = generate_upload_metadata(
        product_name=data.get("product_name", "원터치 음식물 쓰레기 거름망 거치대"),
        target_audience=data.get("target_audience", "자취생 및 주방 살림하는 분들"),
        product_features=data.get("product_features", ""),
        coupang_url=data.get("coupang_url", "https://link.coupang.com/a/example"),
    )
    save_upload_package(o_dir, meta_pkg)
    print(f"\n🎉 전 과정 완료! 최종 영상: {final_mp4} ({final_mp4.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    run_project_pipeline("coupang_001")
