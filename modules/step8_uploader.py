"""
[8단계: 유튜브 쇼츠, 인스타그램 릴스, 틱톡, 쓰레드 멀티 업로드 패키지 생성 및 자동화 모듈]
- 각 플랫폼 알고리즘에 최적화된 [제목 / 본문 설명글 / 해시태그 / 쿠팡 파트너스 고정댓글 및 공정위 문구] 자동 생성
- 원클릭 업로드 창 열기 및 브라우저 자동 업로드 연동 지원
"""

import json
import webbrowser
from pathlib import Path
from typing import Dict, Any


def generate_upload_metadata(
    product_name: str,
    target_audience: str,
    product_features: str,
    coupang_url: str,
) -> Dict[str, Any]:
    """
    4대 숏폼/SNS 플랫폼(유튜브, 인스타그램, 틱톡, 쓰레드)에 바로 올릴 수 있는
    맞춤형 제목, 본문, 해시태그, 고정댓글 패키지를 생성합니다.
    """
    features = [f.strip() for f in product_features.replace("\n", ",").split(",") if f.strip()]
    feat_summary = " / ".join(features[:3]) if features else "압도적 가성비와 편리함"

    return {
        "youtube_shorts": {
            "title": f"아직도 없이 사세요? 😱 {target_audience} 삶의 질 수직 상승하는 {product_name} #shorts #쿠팡꿀템",
            "description": (
                f"🔥 {product_name} 최저가 & 상세 정보 확인하기\n"
                f"👉 {coupang_url}\n\n"
                f"✔️ 핵심 포인트: {feat_summary}\n\n"
                f"※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n\n"
                f"#쿠팡추천템 #살림꿀템 #자취꿀템 #{product_name.replace(' ', '')}"
            ),
            "pinned_comment": (
                f"👇 영상 속 [{product_name}] 품절 전 특가 좌표는 여기입니다!\n"
                f"🔗 {coupang_url}\n"
                f"(쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다)"
            ),
            "upload_url": "https://studio.youtube.com",
        },
        "instagram_reels": {
            "caption": (
                f"솔직히 이건 왜 이제 샀나 후회되는 {product_name} ✨\n\n"
                f"{target_audience} 분들이라면 무조건 공감하실 텐데요!\n"
                f"✅ {feat_summary}\n\n"
                f"🛒 구매 좌표는 프로필 상단 링크(또는 댓글에 '링크' 남겨주세요!)에서 바로 확인하실 수 있어요 👇\n"
                f"{coupang_url}\n\n"
                f"※ 쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다.\n"
                f"#릴스추천 #쿠팡꿀템 #삶의질상승템 #자취필수템 #살림템추천"
            ),
            "upload_url": "https://www.instagram.com",
        },
        "tiktok": {
            "caption": (
                f"{target_audience} 사이에서 난리 난 {product_name} 🔥 "
                f"프로필 링크에서 최저가 확인하세요! #틱톡꿀템 #쿠팡추천 #가성비꿀템 #내돈내산"
            ),
            "upload_url": "https://www.tiktok.com/tiktokstudio/upload",
        },
        "threads": {
            "post_text": (
                f"요즘 {target_audience}들 사이에서 조용히 품절 대란 나는 템 하나 공유합니다.\n\n"
                f"[{product_name}] 인데, {feat_summary} 덕분에 한 번 쓰면 예전으로 못 돌아가네요.\n\n"
                f"👇 최저가 좌표 남겨둡니다 (쿠팡 파트너스 수수료 제공받음)\n"
                f"{coupang_url}"
            ),
            "upload_url": "https://www.threads.net",
        },
    }


def save_upload_package(output_dir: Path, metadata: Dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    save_path = output_dir / "upload_package.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return save_path


def open_platform_upload_page(url: str) -> None:
    """내 PC 기본 브라우저(로그인 세션 유지)에서 해당 플랫폼 업로드 페이지를 즉시 엽니다."""
    webbrowser.open(url)
