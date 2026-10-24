"""
[2~3단계: 주제 기획 및 벤치마킹 역설계 기반 대본/스토리보드 생성 모듈]
- 레퍼런스 영상의 성공 공식(초반 후킹 멘트 구조, 컷 전환 속도, 장면 구성)을 그대로 벤치마킹하여
  내가 홍보할 제품(쿠팡 파트너스, 쇼핑몰 상품, 또는 롱폼 주제)에 맞춘 대본과 이미지 프롬프트를 생성합니다.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


def generate_topic_angles(
    product_name: str,
    product_features: str,
    target_audience: str,
    ref_analysis: Dict[str, Any] = None,
) -> List[Dict[str, str]]:
    """
    [2단계] 제품 정보와 1단계에서 선택한 고조회수 레퍼런스 영상의 후킹 공식을 결합해
    3가지 마케팅 앵글(주제 기획안)을 제안합니다.
    """
    features_list = [f.strip() for f in product_features.replace("\n", ",").split(",") if f.strip()]
    main_feature = features_list[0] if features_list else "압도적인 편리함과 가성비"

    ref_cut_speed = "2.5~3.0초"
    ref_hook_sample = ""
    if ref_analysis:
        avg_cut = ref_analysis.get("visual_and_editing", {}).get("avg_cut_duration_sec")
        if avg_cut and avg_cut < 15:
            ref_cut_speed = f"{avg_cut}초"
        ref_hook_sample = ref_analysis.get("hook_analysis", {}).get("first_3_seconds_audio", "")

    benchmark_hook = (
        f"[떡상 영상 공식 적용] {target_audience}이라면 주목! '{product_name}' 써보고 진짜 신세계 경험했습니다!"
        if not ref_hook_sample
        else f"({ref_hook_sample[:18]}... 패턴 응용) 아직도 불편하게 참으세요? '{product_name}' 하나로 끝냈습니다!"
    )

    return [
        {
            "angle_id": "angle_benchmark",
            "title": "🏆 [레퍼런스 1:1 벤치마킹형] 선택한 인기 영상의 후킹 & 컷 템포 그대로 복제",
            "hook": benchmark_hook,
            "concept": f"1단계에서 분석한 고조회수 영상의 평균 컷 전환 속도({ref_cut_speed})와 초반 3초 시선 강탈 화법을 그대로 내 상품('{product_name}')에 이식한 구성",
        },
        {
            "angle_id": "angle_2",
            "title": "😱 [반전·경고 후킹형] '절대 사지 마세요' 역발상 호기심 앵글",
            "hook": "이거 절대 사지 마세요... 한 번 쓰면 예전으로 절대 못 돌아갑니다.",
            "concept": "초반 3초 동안 부정적인 멘트로 스크롤을 멈추게 한 뒤, 반전으로 핵심 장점 3가지를 폭격하여 댓글 참여와 구매 전환을 유도하는 구성",
        },
        {
            "angle_id": "angle_3",
            "title": f"🔥 [가성비·리뷰 검증형] 쿠팡 후기 폭발 & {main_feature} 찐추천 앵글",
            "hook": f"요즘 쿠팡에서 왜 이렇게 품절 대란인가 했더니... '{product_name}' 직접 써보고 소름 돋았습니다.",
            "concept": "수많은 사람들이 선택한 이유(사회적 증거)를 앞세워 신뢰감을 주고 핵심 디테일을 짚어주는 리뷰형 구성",
        },
    ]


def generate_script_storyboard(
    product_name: str,
    product_features: str,
    target_audience: str,
    selected_angle: Dict[str, str],
    tone: str = "친근하고 텐션 높은 추천 톤 (~해요/!)",
    total_duration: int = 25,
) -> List[Dict[str, Any]]:
    """
    [3단계] 선택된 주제 앵글을 바탕으로 초 단위 나레이션 대사와
    4~5단계에서 사용할 장면별 이미지/모션 생성 프롬프트를 세트로 생성합니다.
    """
    features = [f.strip() for f in product_features.replace("\n", ",").split(",") if f.strip()]
    while len(features) < 3:
        features.append(f"{product_name}만의 놀라운 디테일과 편리함")

    hook_line = selected_angle.get("hook", f"요즘 쿠팡에서 난리 난 {product_name}, 알고 계셨나요?")

    if "반말" in tone:
        p2_line = f"솔직히 {target_audience}이라면 한 번쯤 이런 불편함 겪어봤을 거야."
        p3_line = f"그럴 땐 이 '{product_name}' 써봐! {features[0]} 덕분에 진짜 편해져."
        p4_line = f"게다가 {features[1]} 기능까지 있어서 활용도가 미쳤어."
        p5_line = f"특히 {features[2]}까지 완벽하니까 안 쓸 이유가 없겠지?"
        cta_line = "가격이랑 상세 정보는 고정 댓글 링크에 남겨뒀으니 품절되기 전에 확인해 봐!"
    elif "뉴스" in tone or "전문가" in tone:
        p2_line = f"최근 {target_audience} 사이에서 기존 방식의 불편함을 호소하는 분들이 많습니다."
        p3_line = f"해결책으로 주목받는 '{product_name}'입니다. 첫째, {features[0]} 기능이 탁월합니다."
        p4_line = f"둘째, {features[1]} 설계를 통해 사용 편의성을 극대화했습니다."
        p5_line = f"셋째, {features[2]}까지 갖춰 가성비와 실용성을 동시에 잡았습니다."
        cta_line = "최저가 구매 좌표는 고정 댓글과 프로필 링크에서 바로 확인하실 수 있습니다."
    else:
        p2_line = f"평소에 {target_audience} 분들이라면 이런 불편함 진짜 공감하실 텐데요!"
        p3_line = f"이 '{product_name}' 하나로 고민 끝입니다! {features[0]} 덕분에 너무 편해요."
        p4_line = f"뿐만 아니라 {features[1]}까지 가능해서 활용도가 정말 미쳤습니다!"
        p5_line = f"여기에 {features[2]}까지 완벽하니까 후기가 좋을 수밖에 없겠죠?"
        cta_line = "지금 쿠팡 특가 정보는 고정 댓글 링크에 걸어뒀으니 품절 전에 꼭 확인해 보세요!"

    storyboard = [
        {
            "scene_no": 1,
            "time_range": "00:00 ~ 00:03",
            "duration_sec": 3,
            "step_role": "🪝 초반 3초 후킹",
            "narration": hook_line,
            "subtitle_highlight": "🔥 요즘 난리 난 꿀템!",
            "visual_prompt_ko": f"{product_name} 제품을 클로즈업으로 보여주며 시선을 강탈하는 임팩트 있는 첫 장면, 밝고 선명한 조명",
            "visual_prompt_en": f"Vertical 9:16 commercial shot, dramatic close-up of {product_name}, bright studio lighting, ultra detailed, eye-catching hook scene",
            "camera_motion": "빠른 줌인 (Fast Zoom-In)",
        },
        {
            "scene_no": 2,
            "time_range": "00:03 ~ 00:07",
            "duration_sec": 4,
            "step_role": "😫 문제 제기 & 공감",
            "narration": p2_line,
            "subtitle_highlight": "😫 이런 불편함 공감하시죠?",
            "visual_prompt_ko": f"{target_audience}가 일상에서 불편함을 겪는 상황 묘사 후 {product_name}가 등장하는 전환 장면",
            "visual_prompt_en": f"Vertical 9:16 lifestyle shot, {target_audience} experiencing daily inconvenience in a modern Korean home setting, realistic photography",
            "camera_motion": "좌우 패닝 (Pan Left-to-Right)",
        },
        {
            "scene_no": 3,
            "time_range": "00:07 ~ 00:12",
            "duration_sec": 5,
            "step_role": "✨ 핵심 장점 1 (해결책)",
            "narration": p3_line,
            "subtitle_highlight": f"✅ 포인트 1: {features[0][:12]}",
            "visual_prompt_ko": f"{product_name}의 첫 번째 장점({features[0]})을 실제로 사용하는 깔끔한 시연 장면",
            "visual_prompt_en": f"Vertical 9:16 product demonstration shot of {product_name}, showcasing {features[0]}, clean modern background, high resolution",
            "camera_motion": "부드러운 줌인 (Slow Zoom-In)",
        },
        {
            "scene_no": 4,
            "time_range": "00:12 ~ 00:17",
            "duration_sec": 5,
            "step_role": "🔥 핵심 장점 2 (디테일)",
            "narration": p4_line,
            "subtitle_highlight": f"✅ 포인트 2: {features[1][:12]}",
            "visual_prompt_ko": f"{product_name}의 두 번째 장점({features[1]}) 디테일 컷, 깔끔한 인테리어 배경",
            "visual_prompt_en": f"Vertical 9:16 macro detail shot of {product_name}, highlighting {features[1]}, warm aesthetic lighting, commercial quality",
            "camera_motion": "줌아웃 (Zoom-Out)",
        },
        {
            "scene_no": 5,
            "time_range": "00:17 ~ 00:21",
            "duration_sec": 4,
            "step_role": "👍 핵심 장점 3 (차별점)",
            "narration": p5_line,
            "subtitle_highlight": f"✅ 포인트 3: {features[2][:12]}",
            "visual_prompt_ko": f"{product_name}의 세 번째 장점({features[2]})과 전체적인 만족감을 보여주는 장면",
            "visual_prompt_en": f"Vertical 9:16 happy user holding or using {product_name} in a bright room, premium product showcase",
            "camera_motion": "상하 틸트 (Tilt Up)",
        },
        {
            "scene_no": 6,
            "time_range": "00:21 ~ 00:25",
            "duration_sec": 4,
            "step_role": "🛒 구매 유도 (CTA)",
            "narration": cta_line,
            "subtitle_highlight": "👇 고정 댓글 특가 링크 확인!",
            "visual_prompt_ko": f"{product_name} 전체 풀샷과 함께 '고정 댓글 링크 확인' 화살표가 어울리는 깔끔한 엔딩 컷",
            "visual_prompt_en": f"Vertical 9:16 hero product shot of {product_name} on a clean pedestal with space for text overlay, commercial ending scene",
            "camera_motion": "강조 줌인 & 진동 효과 (Pulse Zoom)",
        },
    ]

    return storyboard


def save_script_data(output_dir: Path, project_data: Dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "storyboard_script.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)
    return save_path
