"""
쇼츠 광고 제작 자동화 시스템 - 1단계 실행기
[1단계: 레퍼런스 영상 다운로드 및 무료 로컬 AI 정밀 분석]
"""

from modules.step1_analyzer import (
    create_project_dirs,
    download_by_url,
    search_and_download_by_keyword,
    analyze_video,
)


def main():
    print("=" * 60)
    print("🎬 [쇼츠 광고 자동화 시스템] Step 1: 레퍼런스 영상 분석기")
    print("=" * 60)

    project_name = input("\n📁 작업할 프로젝트 이름을 입력하세요 (엔터 시 'coupang_001'): ").strip()
    if not project_name:
        project_name = "coupang_001"

    dirs = create_project_dirs(project_name)
    ref_dir = dirs["step1_ref"]

    print("\n어떻게 레퍼런스 영상을 가져올까요?")
    print("  [1] 영상 링크(URL) 직접 입력 (유튜브 쇼츠 / 틱톡 / 인스타 릴스)")
    print("  [2] 키워드로 인기 쇼츠 자동 검색 (예: 쿠팡 꿀템, 자취 추천템)")
    mode = input("👉 번호 선택 (1 또는 2): ").strip()

    collected_videos = []

    if mode == "1":
        url = input("\n🔗 분석할 영상의 URL을 붙여넣으세요: ").strip()
        if not url:
            print("❌ URL이 입력되지 않았습니다.")
            return
        meta = download_by_url(url, ref_dir)
        collected_videos.append(meta)

    elif mode == "2":
        keyword = input("\n🔍 검색할 키워드를 입력하세요 (예: 쿠팡 꿀템): ").strip()
        if not keyword:
            print("❌ 키워드가 입력되지 않았습니다.")
            return
        count_str = input("👉 몇 개의 영상을 가져올까요? (엔터 시 기본 1개): ").strip()
        max_results = int(count_str) if count_str.isdigit() else 1
        collected_videos = search_and_download_by_keyword(keyword, ref_dir, max_results=max_results)

    else:
        print("❌ 잘못된 선택입니다.")
        return

    if not collected_videos:
        print("⚠️ 다운로드된 영상이 없습니다.")
        return

    print("\n" + "-" * 60)
    print(f"✅ 총 {len(collected_videos)}개의 영상 준비 완료! 무료 로컬 정밀 분석을 시작합니다.")
    print("-" * 60)

    for idx, meta in enumerate(collected_videos, start=1):
        print(f"\n[{idx}/{len(collected_videos)}] 분석 중: {meta.get('title')}")
        try:
            analyze_video(meta, ref_dir)
        except Exception as e:
            print(f"❌ 분석 중 오류 발생: {e}")

    print("\n" + "=" * 60)
    print(f"🎉 1단계 완료! 결과물이 아래 폴더에 저장되었습니다:\n👉 {ref_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
