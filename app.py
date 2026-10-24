"""
🎬 쇼츠 & 롱폼 광고 제작 올인원 웹 스튜디오 (1~8단계 풀 파이프라인 Web UI)
- 1단계 (전면 업그레이드): 조회수 폭발(인기순) 필터 검색 ➔ 썸네일·조회수 미리보기 선택 ➔ 초반 3초 연속 프레임 + 시청자 댓글 반응 + 장면별 1:1 역설계 심층 벤치마킹
- 2단계: 내 상품(쿠팡/쇼핑몰/롱폼 주제) 맞춤 기획 및 벤치마킹 앵글 선정
- 3단계: 초 단위 대본 및 장면별 이미지/모션 스토리보드 생성 및 실시간 웹 편집
- 4단계: 주제 맞춤 이미지 생성 (무료 Flux AI / M3 Max 로컬 ComfyUI / 내 상품 사진 쇼츠 규격 자동 편집)
- 5단계: 이미지를 움직이는 영상 클립으로 변환 (6가지 다이내믹 카메라 모션 렌더링)
- 6단계: AI 성우 나레이션(Edge-TTS) 생성 및 장면별 음성 미리듣기·배속 조절
- 7단계: 영상 + 음성 + 한국형 쇼츠 강조 자막 자동 합성 및 최종 MP4 완성본 출력
- 8단계: 유튜브 쇼츠, 인스타 릴스, 틱톡, 쓰레드 맞춤 제목/해시태그/고정댓글 생성 및 원클릭 업로드 연동
"""

import json
import random
from pathlib import Path
import streamlit as st
import pandas as pd

from modules.step1_analyzer import (
    create_project_dirs,
    search_benchmark_candidates,
    download_by_url,
    analyze_video,
)
from modules.step2_3_planner_scripter import (
    generate_topic_angles,
    generate_script_storyboard,
    save_script_data,
)
from modules.step4_image_gen import (
    STYLE_PRESETS,
    generate_image_pollinations_flux,
    generate_image_comfyui_local,
    format_product_image_for_shorts,
)
from modules.step5_video_gen import (
    MOTION_OPTIONS,
    render_dynamic_motion_clip,
)
from modules.step6_tts import (
    VOICE_PRESETS,
    generate_scene_tts,
    get_audio_duration_sec,
)
from modules.step7_editor import (
    render_scene_with_subtitles_and_audio,
    concat_scenes_to_final_video,
)
from modules.step8_uploader import (
    generate_upload_metadata,
    save_upload_package,
    open_platform_upload_page,
)

st.set_page_config(
    page_title="쇼츠 & 롱폼 자동화 웹 스튜디오",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header {
        font-size: 1.9rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #666;
        margin-bottom: 1.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 좌측 사이드바: 프로젝트 관리 및 전체 진행 상태
# ==========================================
with st.sidebar:
    st.title("⚙️ 프로젝트 컨트롤러")

    workspace_root = Path(__file__).resolve().parent / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    existing_projects = [d.name for d in workspace_root.iterdir() if d.is_dir()]
    if not existing_projects:
        existing_projects = ["coupang_001"]

    project_mode = st.radio("프로젝트 선택 방식", ["기존 프로젝트 열기", "새 프로젝트 만들기"], horizontal=True)
    if project_mode == "기존 프로젝트 열기":
        project_name = st.selectbox("📁 작업할 프로젝트", existing_projects)
    else:
        project_name = st.text_input("📁 새 프로젝트 이름 입력", value="coupang_002").strip() or "coupang_002"

    dirs = create_project_dirs(project_name)
    st.success(f"작업 폴더: `workspace/{project_name}`")

    st.divider()
    st.subheader("📋 1~8단계 파이프라인 가동 상태")
    st.markdown(
        """
        - 🟢 **1단계**: 고조회수 영상 탐색 & 심층 해부
        - 🟢 **2단계**: 상품 매칭 & 주제 정하기
        - 🟢 **3단계**: 초 단위 대본/스토리보드
        - 🟢 **4단계**: 주제 맞춤 이미지 생성
        - 🟢 **5단계**: 이미지를 영상으로 변환
        - 🟢 **6단계**: AI 성우 나레이션(TTS)
        - 🟢 **7단계**: 자막/음성 자동 편집 완성
        - 🟢 **8단계**: 4대 플랫폼 멀티 업로드
        """
    )

saved_sb_path = dirs["step2_3_script"] / "storyboard_script.json"
if "storyboard" not in st.session_state and saved_sb_path.exists():
    try:
        loaded = json.loads(saved_sb_path.read_text(encoding="utf-8"))
        st.session_state["storyboard"] = loaded.get("storyboard", [])
        st.session_state["product_name"] = loaded.get("product_name", "원터치 음식물 쓰레기 거름망 거치대")
        st.session_state["target_audience"] = loaded.get("target_audience", "자취생 및 주방 살림하는 분들")
        st.session_state["product_features"] = loaded.get(
            "product_features",
            "손에 음식물 묻힐 일 없이 원터치로 깔끔하게 버림\n수세미나 행주 거치대로도 1석 2조 활용 가능\n만원 이하 갓성비에 싱크대 공간 차지 안 함",
        )
    except Exception:
        pass

# ==========================================
# 상단 타이틀 및 1~8단계 탭 구성
# ==========================================
st.markdown('<div class="main-header">🎬 쇼츠 & 롱폼 광고 제작 올인원 자동화 스튜디오</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">수십만~수백만 조회수 검증된 영상만 골라 벤치마킹하고, 대본부터 영상 제작·업로드까지 한곳에서 조율하세요.</div>', unsafe_allow_html=True)

tabs = st.tabs([
    "1️⃣ 고조회수 벤치마킹 분석",
    "2️⃣ 주제 정하기",
    "3️⃣ 대본 작성",
    "4️⃣ 이미지 생성",
    "5️⃣ 영상 변환",
    "6️⃣ 나레이션(TTS)",
    "7️⃣ 편집·영상 완성",
    "8️⃣ 멀티 업로드",
])

# ==========================================
# [탭 1] 1단계 (전면 업그레이드): 고조회수 영상 탐색 & 심층 벤치마킹 해부
# ==========================================
with tabs[0]:
    st.subheader("1단계: 조회수 터진 검증된 레퍼런스 탐색 & 심층 역설계(Benchmarking) 스튜디오")
    col_search, col_report = st.columns([1.15, 1.45], gap="large")

    with col_search:
        st.markdown("#### 🔍 Step 1-A. 조회수 폭발 레퍼런스 영상 찾기")
        input_mode = st.radio(
            "레퍼런스 탐색 방식",
            ["🔥 인기순(조회수순) 키워드 필터 검색", "🔗 내가 찾은 떡상 영상 URL 직접 입력 (유튜브/틱톡/릴스)"],
            horizontal=True,
        )

        if "인기순" in input_mode:
            f_c1, f_c2 = st.columns([1.3, 1])
            with f_c1:
                keyword = st.text_input(
                    "검색 키워드 입력",
                    value="쿠팡 꿀템",
                    placeholder="예: 쿠팡 추천템, 자취 꿀템, 삶의질 수직상승, 다이소 꿀템",
                )
            with f_c2:
                min_view_label = st.selectbox(
                    "⚡ 최소 조회수 커트라인",
                    ["1만 회 이상", "5만 회 이상", "10만 회 이상", "50만 회 이상", "100만 회 이상"],
                    index=1,
                )
                min_view_map = {
                    "1만 회 이상": 10000,
                    "5만 회 이상": 50000,
                    "10만 회 이상": 100000,
                    "50만 회 이상": 500000,
                    "100만 회 이상": 1000000,
                }
                min_views_val = min_view_map[min_view_label]

            f_c3, f_c4 = st.columns(2)
            with f_c3:
                sort_choice = st.selectbox("정렬 기준", ["조회수 높은순 (인기순)", "최신 업로드순", "관련도순"])
            with f_c4:
                dur_choice = st.selectbox(
                    "타겟 영상 길이/포맷",
                    ["숏폼/짧은 영상 (4분 미만)", "롱폼 영상 (4분~20분)", "전체 길이"],
                )

            if st.button("🔎 조건에 맞는 고조회수 후보 영상 검색하기 (미리보기)", type="primary", width="stretch"):
                with st.spinner(f"유튜브에서 '{keyword}' 관련 {min_view_label} 인기 영상을 스캔하고 있습니다..."):
                    cands = search_benchmark_candidates(
                        keyword=keyword,
                        sort_by=sort_choice,
                        duration_filter=dur_choice,
                        min_views=min_views_val,
                        max_candidates=10,
                    )
                    st.session_state["benchmark_candidates"] = cands

            cands = st.session_state.get("benchmark_candidates", [])
            if cands:
                st.markdown(f"##### 🏆 검색된 고조회수 후보 영상 ({len(cands)}개) — 원하는 영상을 골라 분석하세요!")
                for c_idx, cand in enumerate(cands):
                    with st.container(border=True):
                        cc1, cc2 = st.columns([1, 2.2])
                        with cc1:
                            st.image(cand["thumbnail"], width="stretch")
                        with cc2:
                            st.markdown(f"**{cand['title']}**")
                            st.markdown(
                                f"🔥 **조회수: `{cand['view_count']:,}회`** | ⏱️ 길이: `{cand['duration']}초` | 📺 {cand['channel']}"
                            )
                            b_col1, b_col2 = st.columns([1.4, 1])
                            with b_col1:
                                if st.button(
                                    f"📥 다운로드 & 심층 해부하기",
                                    key=f"dl_cand_{cand['id']}_{c_idx}",
                                    type="primary",
                                    width="stretch",
                                ):
                                    with st.spinner(f"'{cand['title']}' 영상과 베스트 댓글을 다운로드하고 초 단위로 해부 중입니다..."):
                                        meta = download_by_url(cand["url"], dirs["step1_ref"], fetch_comments=True)
                                        analyze_video(meta, dirs["step1_ref"])
                                        st.session_state["selected_ref_id"] = meta["id"]
                                    st.success("심층 벤치마킹 분석 완료! 오른쪽 리포트를 확인하세요!")
                                    st.rerun()
                            with b_col2:
                                st.link_button("🔗 원본 영상 보기", cand["url"], width="stretch")
            elif "benchmark_candidates" in st.session_state:
                st.warning("해당 조회수 커트라인을 넘는 영상이 없습니다. 최소 조회수 조건을 한 단계 낮춰서 검색해보세요!")

        else:
            video_url = st.text_input(
                "유튜브 쇼츠 / 롱폼 / 틱톡 / 인스타 릴스 링크(URL)",
                placeholder="https://www.youtube.com/shorts/... 또는 https://www.youtube.com/watch?v=...",
            )
            if st.button("🚀 이 링크 영상 다운로드 & 심층 벤치마킹 해부 실행", type="primary", width="stretch"):
                if not video_url.strip():
                    st.warning("영상 URL을 입력해주세요!")
                else:
                    with st.spinner("영상을 다운로드하고 초반 3초 후킹/대본/댓글/컷 구조를 정밀 해부 중입니다..."):
                        meta = download_by_url(video_url.strip(), dirs["step1_ref"], fetch_comments=True)
                        analyze_video(meta, dirs["step1_ref"])
                        st.session_state["selected_ref_id"] = meta["id"]
                    st.success("심층 벤치마킹 해부 완료!")
                    st.rerun()

        st.divider()
        st.markdown("#### 📂 내 작업실에 분석 완료된 벤치마킹 영상 보관함")
        meta_files = sorted(dirs["step1_ref"].glob("*_meta.json"), key=lambda x: x.stat().st_mtime, reverse=True)

        selected_video_id = None
        meta_map = {}
        for mf in meta_files:
            try:
                mdata = json.loads(mf.read_text(encoding="utf-8"))
                vid = mdata["id"]
                meta_map[vid] = mdata
            except Exception:
                pass

        if meta_map:
            # 조회수가 높은 영상이 위에 오도록 정렬
            vid_options = sorted(meta_map.keys(), key=lambda k: meta_map[k].get("view_count", 0), reverse=True)
            default_idx = 0
            if st.session_state.get("selected_ref_id") in vid_options:
                default_idx = vid_options.index(st.session_state["selected_ref_id"])

            selected_video_id = st.selectbox(
                "오른쪽에 띄울 벤치마킹 리포트를 선택하세요",
                options=vid_options,
                index=default_idx,
                format_func=lambda x: f"🔥 조회수 {meta_map[x].get('view_count', 0):,}회 | {meta_map[x].get('title', x)} ({meta_map[x].get('duration')}초)",
            )
            st.session_state["selected_ref_id"] = selected_video_id
        else:
            st.info("아직 분석된 영상이 없습니다. 위에서 인기 영상을 검색해 선택해보세요!")

    # ==========================================
    # 우측: 선택한 고조회수 영상의 심층 벤치마킹 해부 리포트
    # ==========================================
    with col_report:
        if selected_video_id and selected_video_id in meta_map:
            cur_meta = meta_map[selected_video_id]
            analysis_path = dirs["step1_ref"] / f"{selected_video_id}_analysis.json"
            video_file = Path(cur_meta.get("local_video_path", ""))

            st.markdown(f"#### 📊 심층 벤치마킹 리포트: `{cur_meta.get('title')}`")

            top_c1, top_c2 = st.columns([1, 1.45])
            with top_c1:
                if video_file.exists():
                    st.video(str(video_file))
                st.caption(f"📺 채널: **{cur_meta.get('uploader')}** | [원본 링크 열기]({cur_meta.get('webpage_url')})")

            with top_c2:
                if analysis_path.exists():
                    adata = json.loads(analysis_path.read_text(encoding="utf-8"))
                    st.session_state["current_ref_analysis"] = adata
                    hook = adata.get("hook_analysis", {})
                    visual = adata.get("visual_and_editing", {})
                    script = adata.get("script_structure", {})
                    aud_react = adata.get("audience_reaction", {})

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("🔥 실제 조회수", f"{cur_meta.get('view_count', 0):,}회")
                    m2.metric("👍 좋아요", f"{cur_meta.get('like_count', 0):,}개")
                    m3.metric("✂️ 총 컷 전환", f"{visual.get('total_cuts', 0)}컷")
                    m4.metric("⚡ 평균 1컷 길이", f"{visual.get('avg_cut_duration_sec', 0)}초")

                    st.markdown("##### 🪝 1) 초반 3초 시선 강탈(Hook) 해부")
                    st.info(
                        f"**• 후킹 공식**: `{hook.get('hook_type')}`\n\n"
                        f"**• 초반 3초 실제 멘트**: **\"{hook.get('first_3_seconds_audio')}\"**\n\n"
                        f"**• 벤치마킹 포인트**: {hook.get('why_it_works')}"
                    )

                    # 초반 3초 프레임 연속 캡처 (0.5초 / 1.5초 / 2.5초) 표시
                    hook_frames = visual.get("hook_3s_frames", [])
                    if hook_frames:
                        st.markdown("**📸 초반 3초 시각 연출 연속 캡처 (0.5초 ➔ 1.5초 ➔ 2.5초)**")
                        hf_cols = st.columns(len(hook_frames))
                        for h_i, hf in enumerate(hook_frames):
                            hf_p = Path(hf["image_path"])
                            if hf_p.exists():
                                hf_cols[h_i].image(str(hf_p), caption=f"시작 후 {hf['time_sec']}초 화면", width="stretch")

                    if st.button(
                        "✨ 이 떡상 영상의 후킹 공식 & 템포를 내 대본(2~3단계)으로 복제하기!",
                        type="primary",
                        width="stretch",
                    ):
                        angles = generate_topic_angles(
                            st.session_state.get("product_name", "원터치 음식물 쓰레기 거름망 거치대"),
                            st.session_state.get("product_features", ""),
                            st.session_state.get("target_audience", "자취생 및 살림하는 분들"),
                            adata,
                        )
                        st.session_state["generated_angles"] = angles
                        st.session_state["selected_angle"] = angles[0]
                        st.toast("🎉 벤치마킹 공식이 2단계/3단계에 적용되었습니다! [2️⃣ 주제 정하기] 탭을 눌러보세요!")

            if analysis_path.exists():
                adata = json.loads(analysis_path.read_text(encoding="utf-8"))
                script = adata.get("script_structure", {})
                aud_react = adata.get("audience_reaction", {})

                st.divider()
                sub_tab1, sub_tab2, sub_tab3 = st.tabs([
                    "🎬 장면별 화면+대사 1:1 역설계 보드",
                    "💬 시청자 베스트 댓글 & 구매 반응",
                    "📝 추출된 전체 대본 원문",
                ])

                with sub_tab1:
                    st.markdown("##### ⏱️ 이 영상이 어떻게 시청자를 설득했는지 장면(Scene)별로 쪼갠 역설계 표입니다.")
                    scenes = adata.get("scenes_breakdown", [])
                    for sc in scenes[:12]:
                        with st.container(border=True):
                            sc_c1, sc_c2 = st.columns([1, 2.8])
                            with sc_c1:
                                mf = sc.get("matched_frame", "")
                                if mf and Path(mf).exists():
                                    st.image(mf, width="stretch")
                                else:
                                    st.caption("프레임 이미지 없음")
                            with sc_c2:
                                st.markdown(f"**{sc.get('role')}** (`{sc.get('time_range')}`)")
                                st.markdown(f"🎙️ **실제 대사**: \"{sc.get('narration')}\"")

                with sub_tab2:
                    st.markdown(f"**📊 {aud_react.get('comment_summary', '')}**")
                    signals = aud_react.get("buying_signals", [])
                    if signals:
                        st.success("**🛒 감지된 구매/정보 문의 댓글 반응:**\n" + "\n".join([f"- \"{s}\"" for s in signals]))
                    top_comms = aud_react.get("top_comments_sample", []) or cur_meta.get("top_comments", [])
                    if top_comms:
                        st.dataframe(pd.DataFrame(top_comms), width="stretch", hide_index=True)
                    else:
                        st.info("수집된 댓글이 없습니다.")

                with sub_tab3:
                    st.text_area(
                        "전체 나레이션 받아쓰기 원문 (복사 및 카피라이팅 참고용)",
                        value=script.get("full_transcript", ""),
                        height=220,
                    )

# ==========================================
# [탭 2] 2단계: 내 상품 입력 & 주제/후킹 기획
# ==========================================
with tabs[1]:
    st.subheader("2단계: 홍보할 상품 정보 입력 & 벤치마킹 주제(앵글) 정하기")
    p_col1, p_col2 = st.columns([1, 1.3], gap="large")

    with p_col1:
        st.markdown("#### 🛍️ 홍보할 내 상품 정보 입력")
        product_name = st.text_input(
            "1. 상품명 (또는 영상 주제)",
            value=st.session_state.get("product_name", "원터치 음식물 쓰레기 거름망 거치대"),
        )
        target_audience = st.text_input(
            "2. 핵심 타겟 시청자",
            value=st.session_state.get("target_audience", "자취생 및 주방 살림하는 분들"),
        )
        product_features = st.text_area(
            "3. 강조할 핵심 장점/특징 3가지 (줄바꿈으로 구분)",
            value=st.session_state.get(
                "product_features",
                "손에 음식물 묻힐 일 없이 원터치로 깔끔하게 버림\n수세미나 행주 거치대로도 1석 2조 활용 가능\n만원 이하 갓성비에 싱크대 공간 차지 안 함",
            ),
            height=120,
        )
        coupang_url = st.text_input(
            "4. 쿠팡 파트너스 / 쇼핑몰 구매 링크",
            value=st.session_state.get("coupang_url", "https://link.coupang.com/a/example"),
        )

        if st.button("💡 벤치마킹 공식을 결합해 3가지 쇼츠 주제(앵글) 뽑기", type="primary", width="stretch"):
            st.session_state["product_name"] = product_name
            st.session_state["target_audience"] = target_audience
            st.session_state["product_features"] = product_features
            st.session_state["coupang_url"] = coupang_url

            ref_adata = st.session_state.get("current_ref_analysis")
            angles = generate_topic_angles(product_name, product_features, target_audience, ref_adata)
            st.session_state["generated_angles"] = angles
            st.success("벤치마킹 공식이 반영된 3가지 맞춤 기획안이 생성되었습니다!")

    with p_col2:
        st.markdown("#### 🎯 추천 쇼츠 주제 & 초반 3초 후킹 기획안")
        angles = st.session_state.get("generated_angles", [])
        if not angles:
            angles = generate_topic_angles(product_name, product_features, target_audience, st.session_state.get("current_ref_analysis"))
            st.session_state["generated_angles"] = angles

        angle_titles = [a["title"] for a in angles]
        chosen_idx = st.radio(
            "마음에 드는 기획 앵글을 선택하세요:",
            options=range(len(angles)),
            format_func=lambda i: angle_titles[i],
        )

        chosen_angle = angles[chosen_idx]
        st.markdown("---")
        custom_hook = st.text_input("초반 3초 후킹 대사 (수정 가능)", value=chosen_angle["hook"])
        chosen_angle["hook"] = custom_hook
        st.caption(f"**기획 의도**: {chosen_angle['concept']}")
        st.session_state["selected_angle"] = chosen_angle

# ==========================================
# [탭 3] 3단계: 초 단위 대본 & 스토리보드 생성 및 편집
# ==========================================
with tabs[2]:
    st.subheader("3단계: 초 단위 대본 및 장면별 이미지/영상 프롬프트 편집기")

    s_col1, s_col2, s_col3 = st.columns([1.2, 1, 1])
    with s_col1:
        tone_option = st.selectbox(
            "🎙️ 대본 말투(톤앤매너) 선택",
            [
                "친근하고 텐션 높은 추천 톤 (~해요/!)",
                "친구에게 알려주는 반말 꿀팁 톤 (~해봐/!)",
                "신뢰감 있는 전문가/뉴스 리뷰 톤 (~합니다)",
            ],
        )
    with s_col2:
        target_dur = st.slider("⏱️ 목표 영상 길이(초)", min_value=15, max_value=45, value=25, step=5)
    with s_col3:
        st.write("")
        if st.button("✨ 초 단위 대본 & 스토리보드 자동 생성", type="primary", width="stretch"):
            sel_angle = st.session_state.get("selected_angle") or generate_topic_angles(
                product_name, product_features, target_audience
            )[0]
            sb = generate_script_storyboard(
                product_name=product_name,
                product_features=product_features,
                target_audience=target_audience,
                selected_angle=sel_angle,
                tone=tone_option,
                total_duration=target_dur,
            )
            st.session_state["storyboard"] = sb
            st.success("초 단위 대본과 장면별 이미지 프롬프트가 생성되었습니다!")

    if "storyboard" not in st.session_state:
        sel_angle = st.session_state.get("selected_angle") or generate_topic_angles(
            product_name, product_features, target_audience
        )[0]
        st.session_state["storyboard"] = generate_script_storyboard(
            product_name, product_features, target_audience, sel_angle, tone_option, target_dur
        )

    df_sb = pd.DataFrame(st.session_state["storyboard"])

    edited_df = st.data_editor(
        df_sb,
        width="stretch",
        num_rows="dynamic",
        column_config={
            "scene_no": st.column_config.NumberColumn("장면#", width="small"),
            "time_range": st.column_config.TextColumn("시간 구간", width="small"),
            "duration_sec": st.column_config.NumberColumn("길이(초)", width="small"),
            "step_role": st.column_config.TextColumn("설득 단계", width="medium"),
            "narration": st.column_config.TextColumn("🎙️ 나레이션 대사 (6단계 TTS용)", width="large"),
            "subtitle_highlight": st.column_config.TextColumn("💬 상단 배지 자막 (7단계용)", width="medium"),
            "visual_prompt_ko": st.column_config.TextColumn("🖼️ 장면 묘사(한글)", width="large"),
            "visual_prompt_en": st.column_config.TextColumn("🎨 AI 이미지 프롬프트(영문)", width="large"),
            "camera_motion": st.column_config.SelectboxColumn(
                "🎬 카메라 모션 (5단계 영상화용)",
                options=MOTION_OPTIONS,
                width="medium",
            ),
        },
        hide_index=True,
    )

    if st.button("💾 수정한 대본·스토리보드 저장하기", type="primary", width="stretch"):
        updated_records = edited_df.to_dict(orient="records")
        st.session_state["storyboard"] = updated_records
        payload = {
            "product_name": product_name,
            "target_audience": target_audience,
            "product_features": product_features,
            "coupang_url": coupang_url,
            "tone": tone_option,
            "storyboard": updated_records,
        }
        save_script_data(dirs["step2_3_script"], payload)
        st.success("✅ 대본 저장 완료! 이제 4~7단계에서 이 대본을 바탕으로 이미지, 음성, 영상을 제작합니다.")

# ==========================================
# [탭 4] 4단계: 주제에 맞는 장면별 이미지 생성
# ==========================================
with tabs[3]:
    st.subheader("4단계: 장면(Scene)별 맞춤 이미지 생성 및 내 상품 사진 합성")

    ctrl1, ctrl2, ctrl3 = st.columns([1.2, 1.2, 1])
    with ctrl1:
        img_engine = st.selectbox(
            "⚡ 사용할 이미지 생성 엔진",
            [
                "☁️ 무료 Flux AI 즉시 생성 (Pollinations - API 키 불필요)",
                "🍎 로컬 ComfyUI 연동 (M3 Max 맥북 / 고사양 PC용)",
            ],
        )
    with ctrl2:
        style_choice = st.selectbox("🎨 전체 AI 이미지 화풍(스타일)", list(STYLE_PRESETS.keys()))
    with ctrl3:
        aspect_choice = st.selectbox(
            "📐 화면 비율 선택",
            ["9:16 (쇼츠/릴스 세로형 - 1080x1920)", "16:9 (유튜브 롱폼 가로형 - 1920x1080)"],
        )

    storyboard_list = st.session_state.get("storyboard", [])
    visuals_dir = dirs["step4_5_visuals"]

    if st.button("🚀 모든 장면(Scene 1~6) AI 이미지 한 번에 자동 생성하기", type="primary", width="stretch"):
        progress_bar = st.progress(0, text="장면별 이미지를 생성하고 있습니다...")
        total_scenes = len(storyboard_list)
        for idx, scene in enumerate(storyboard_list):
            s_no = scene.get("scene_no", idx + 1)
            p_en = scene.get("visual_prompt_en") or scene.get("visual_prompt_ko", "commercial product shot")
            out_file = visuals_dir / f"scene_{s_no:02d}.png"
            progress_bar.progress(
                idx / max(1, total_scenes),
                text=f"🎨 [장면 {s_no}/{total_scenes}] 이미지 생성 중: {scene.get('step_role')}...",
            )
            if "ComfyUI" in img_engine:
                generate_image_comfyui_local(p_en, style_choice, out_file, "http://127.0.0.1:8188", aspect_choice, seed=100 + s_no)
            else:
                generate_image_pollinations_flux(p_en, style_choice, out_file, aspect_choice, seed=100 + s_no)
        progress_bar.progress(1.0, text="✅ 모든 장면 이미지 생성이 완료되었습니다!")
        st.success(f"총 {total_scenes}장의 이미지가 준비되었습니다!")
        st.rerun()

    st.divider()
    cols = st.columns(3, gap="medium")
    for idx, scene in enumerate(storyboard_list):
        s_no = scene.get("scene_no", idx + 1)
        img_path = visuals_dir / f"scene_{s_no:02d}.png"

        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**Scene #{s_no} | {scene.get('step_role')}**")
                st.caption(f"🎙️ {scene.get('narration')}")

                if img_path.exists():
                    st.image(str(img_path), width="stretch")
                else:
                    st.info("아직 생성된 이미지가 없습니다.")

                new_prompt_en = st.text_input(
                    f"장면 #{s_no} 영문 프롬프트",
                    value=scene.get("visual_prompt_en", ""),
                    key=f"prompt_en_{s_no}",
                )

                btn_c1, btn_c2 = st.columns(2)
                with btn_c1:
                    if st.button(f"🔄 AI 재생성 #{s_no}", key=f"regen_{s_no}", width="stretch"):
                        with st.spinner(f"장면 #{s_no} 생성 중..."):
                            generate_image_pollinations_flux(
                                new_prompt_en, style_choice, img_path, aspect_choice, seed=random.randint(1, 99999)
                            )
                        st.rerun()
                with btn_c2:
                    uploaded_prod = st.file_uploader(
                        f"🛍️ 상품 사진 #{s_no}",
                        type=["png", "jpg", "jpeg", "webp"],
                        key=f"upload_{s_no}",
                        label_visibility="collapsed",
                    )
                    if uploaded_prod is not None:
                        format_product_image_for_shorts(uploaded_prod.getvalue(), img_path, aspect_choice)
                        st.rerun()

# ==========================================
# [탭 5] 5단계: 이미지를 움직이는 영상으로 만들기
# ==========================================
with tabs[4]:
    st.subheader("5단계: 정지 이미지를 역동적인 모션 영상 클립(.mp4)으로 변환")

    if st.button("🎬 모든 장면(Scene 1~6) 모션 영상 클립 일괄 생성하기", type="primary", width="stretch"):
        v_prog = st.progress(0, text="장면별 모션 영상을 렌더링 중입니다...")
        total_scenes = len(storyboard_list)
        for idx, scene in enumerate(storyboard_list):
            s_no = scene.get("scene_no", idx + 1)
            img_p = visuals_dir / f"scene_{s_no:02d}.png"
            if not img_p.exists():
                generate_image_pollinations_flux(
                    scene.get("visual_prompt_en", "product shot"),
                    style_choice,
                    img_p,
                    aspect_choice,
                    seed=100 + s_no,
                )
            clip_p = visuals_dir / f"clip_{s_no:02d}.mp4"
            motion_name = scene.get("camera_motion", "부드러운 줌인 (Slow Zoom-In)")
            dur_s = float(scene.get("duration_sec", 4))
            v_prog.progress(idx / max(1, total_scenes), text=f"🎥 [장면 {s_no}/{total_scenes}] '{motion_name}' 모션 영상 렌더링 중...")
            render_dynamic_motion_clip(img_p, clip_p, motion_type=motion_name, duration_sec=dur_s)
        v_prog.progress(1.0, text="✅ 모든 장면의 영상 클립 변환이 완료되었습니다!")
        st.rerun()

    st.divider()
    v_cols = st.columns(3, gap="medium")
    for idx, scene in enumerate(storyboard_list):
        s_no = scene.get("scene_no", idx + 1)
        clip_p = visuals_dir / f"clip_{s_no:02d}.mp4"
        img_p = visuals_dir / f"scene_{s_no:02d}.png"

        with v_cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**Scene #{s_no} 영상 클립**")
                sel_motion = st.selectbox(
                    f"장면 #{s_no} 카메라 모션",
                    MOTION_OPTIONS,
                    index=MOTION_OPTIONS.index(scene.get("camera_motion")) if scene.get("camera_motion") in MOTION_OPTIONS else 0,
                    key=f"mot_{s_no}",
                )
                scene["camera_motion"] = sel_motion

                if clip_p.exists():
                    st.video(str(clip_p))
                else:
                    st.info("아직 변환된 영상 클립이 없습니다.")

                if st.button(f"🎥 이 모션으로 영상 다시 만들기 #{s_no}", key=f"reclip_{s_no}", width="stretch"):
                    if not img_p.exists():
                        st.warning("먼저 4단계에서 이미지를 생성해주세요!")
                    else:
                        with st.spinner(f"장면 #{s_no} 영상 변환 중..."):
                            render_dynamic_motion_clip(img_p, clip_p, motion_type=sel_motion, duration_sec=float(scene.get("duration_sec", 4)))
                        st.rerun()

# ==========================================
# [탭 6] 6단계: AI 성우 나레이션(TTS) 만들기
# ==========================================
with tabs[5]:
    st.subheader("6단계: 자연스러운 AI 성우 나레이션(TTS) 생성 및 미리듣기")
    audio_dir = dirs["step6_audio"]

    t_col1, t_col2, t_col3 = st.columns([1.4, 1, 1])
    with t_col1:
        voice_choice = st.selectbox("🎙️ AI 성우 목소리 선택", list(VOICE_PRESETS.keys()))
    with t_col2:
        speed_choice = st.slider("⚡ 말하기 속도 배속 (%)", min_value=-10, max_value=40, value=15, step=5)
    with t_col3:
        pitch_choice = st.slider("🎵 목소리 톤 높낮이 (Hz)", min_value=-10, max_value=10, value=0, step=2)

    if st.button("🎙️ 모든 장면(Scene 1~6) 나레이션 음성 한 번에 녹음하기", type="primary", width="stretch"):
        a_prog = st.progress(0, text="AI 성우가 대본을 읽고 있습니다...")
        total_scenes = len(storyboard_list)
        for idx, scene in enumerate(storyboard_list):
            s_no = scene.get("scene_no", idx + 1)
            mp3_p = audio_dir / f"tts_{s_no:02d}.mp3"
            a_prog.progress(idx / max(1, total_scenes), text=f"🎙️ [장면 {s_no}/{total_scenes}] 음성 합성 중...")
            res = generate_scene_tts(
                text=scene.get("narration", ""),
                output_mp3_path=mp3_p,
                voice_label=voice_choice,
                speed_percent=speed_choice,
                pitch_hz=pitch_choice,
            )
            scene["duration_sec"] = res["duration_sec"]
        a_prog.progress(1.0, text="✅ 전 구간 나레이션 녹음 완료!")
        st.rerun()

    st.divider()
    for idx, scene in enumerate(storyboard_list):
        s_no = scene.get("scene_no", idx + 1)
        mp3_p = audio_dir / f"tts_{s_no:02d}.mp3"
        ac1, ac2, ac3 = st.columns([2.2, 1.2, 0.8])
        with ac1:
            edited_nar = st.text_input(f"Scene #{s_no} 대사 ({scene.get('step_role')})", value=scene.get("narration", ""), key=f"tts_txt_{s_no}")
            scene["narration"] = edited_nar
        with ac2:
            if mp3_p.exists():
                dur = get_audio_duration_sec(mp3_p)
                st.audio(str(mp3_p))
                st.caption(f"⏱️ 실제 음성 길이: {dur}초")
            else:
                st.info("음성 미생성")
        with ac3:
            st.write("")
            if st.button(f"🔄 재녹음 #{s_no}", key=f"retts_{s_no}", width="stretch"):
                generate_scene_tts(edited_nar, mp3_p, voice_choice, speed_choice, pitch_choice)
                st.rerun()

# ==========================================
# [탭 7] 7단계: 최종 편집 & 쇼츠 영상 완성
# ==========================================
with tabs[6]:
    st.subheader("7단계: 영상 + 나레이션 + 쇼츠 강조 자막 자동 합성 (최종 MP4 출력)")
    output_dir = dirs["step7_output"]
    final_mp4_path = output_dir / f"{project_name}_final_shorts.mp4"

    e_col1, e_col2 = st.columns([1, 1.3], gap="large")
    with e_col1:
        st.markdown("#### 🎨 자막 및 렌더링 스타일 설정")
        sub_color_mode = st.radio(
            "하단 자막 강조 색상",
            ["노란색 강조 (쇼츠 기본 - 가독성 최고)", "순백색 깔끔 자막 (화이트 & 블랙 외곽선)"],
        )
        show_top_badge = st.checkbox("상단에 레드 포인트 후킹 배지 표시하기", value=True)

        st.markdown("---")
        if st.button("🎬 [원클릭 완성] 전 과정 통합 렌더링하여 최종 영상(.mp4) 뽑기!", type="primary", width="stretch"):
            r_prog = st.progress(0, text="최종 쇼츠 영상을 합성하고 있습니다...")
            total_scenes = len(storyboard_list)
            rendered_scene_files = []

            for idx, scene in enumerate(storyboard_list):
                s_no = scene.get("scene_no", idx + 1)
                img_p = visuals_dir / f"scene_{s_no:02d}.png"
                mp3_p = audio_dir / f"tts_{s_no:02d}.mp3"
                scene_out_mp4 = output_dir / f"rendered_scene_{s_no:02d}.mp4"

                if not img_p.exists():
                    generate_image_pollinations_flux(
                        scene.get("visual_prompt_en", "commercial product shot"),
                        style_choice,
                        img_p,
                        aspect_choice,
                        seed=100 + s_no,
                    )
                if not mp3_p.exists():
                    generate_scene_tts(scene.get("narration", ""), mp3_p, voice_choice, speed_choice, pitch_choice)

                r_prog.progress(idx / max(1, total_scenes), text=f"✂️ 장면 #{s_no}/{total_scenes} 카메라 모션 + 자막 + 음성 합성 중...")
                badge_txt = scene.get("subtitle_highlight", "") if show_top_badge else ""
                render_scene_with_subtitles_and_audio(
                    image_path=img_p,
                    audio_path=mp3_p,
                    output_scene_mp4=scene_out_mp4,
                    narration_text=scene.get("narration", ""),
                    highlight_badge=badge_txt,
                    motion_type=scene.get("camera_motion", "부드러운 줌인 (Slow Zoom-In)"),
                    subtitle_color_mode=sub_color_mode,
                )
                rendered_scene_files.append(scene_out_mp4)

            r_prog.progress(0.92, text="🔗 모든 장면을 하나의 쇼츠 영상으로 이어 붙이는 중...")
            concat_scenes_to_final_video(rendered_scene_files, final_mp4_path)
            r_prog.progress(1.0, text="🎉 최종 쇼츠 영상 완성!")
            st.balloons()
            st.rerun()

    with e_col2:
        st.markdown("#### 📺 최종 완성된 쇼츠 영상 미리보기 & 다운로드")
        if final_mp4_path.exists():
            v_preview_col, v_info_col = st.columns([1, 1])
            with v_preview_col:
                st.video(str(final_mp4_path))
            with v_info_col:
                file_mb = round(final_mp4_path.stat().st_size / (1024 * 1024), 2)
                st.success(f"✅ **완성 파일 준비 완료!**\n\n- 파일명: `{final_mp4_path.name}`\n- 용량: `{file_mb} MB`")
                with open(final_mp4_path, "rb") as f:
                    st.download_button(
                        label="📥 완성된 쇼츠 영상(.mp4) 내 컴퓨터로 다운로드",
                        data=f,
                        file_name=final_mp4_path.name,
                        mime="video/mp4",
                        type="primary",
                        width="stretch",
                    )
        else:
            st.info("왼쪽의 [🎬 원클릭 완성] 버튼을 눌러 첫 번째 쇼츠 영상을 뽑아보세요!")

# ==========================================
# [탭 8] 8단계: 유튜브, 인스타, 틱톡, 쓰레드 멀티 업로드
# ==========================================
with tabs[7]:
    st.subheader("8단계: 유튜브 쇼츠 · 인스타 릴스 · 틱톡 · 쓰레드 맞춤 업로드 패키지")

    meta_pkg = generate_upload_metadata(
        product_name=st.session_state.get("product_name", product_name),
        target_audience=st.session_state.get("target_audience", target_audience),
        product_features=st.session_state.get("product_features", product_features),
        coupang_url=st.session_state.get("coupang_url", coupang_url),
    )
    save_upload_package(dirs["step7_output"], meta_pkg)

    u_col1, u_col2 = st.columns(2, gap="large")

    with u_col1:
        with st.container(border=True):
            st.markdown("#### 🔴 YouTube Shorts (유튜브 쇼츠)")
            yt = meta_pkg["youtube_shorts"]
            st.text_input("유튜브 쇼츠 제목", value=yt["title"])
            st.text_area("유튜브 설명글", value=yt["description"], height=130)
            st.text_area("📌 고정 댓글용 문구", value=yt["pinned_comment"], height=90)
            if st.button("🚀 유튜브 스튜디오 업로드 창 바로 열기", width="stretch"):
                open_platform_upload_page(yt["upload_url"])

        with st.container(border=True):
            st.markdown("#### 🎵 TikTok (틱톡)")
            tk = meta_pkg["tiktok"]
            st.text_area("틱톡 캡션 & 해시태그", value=tk["caption"], height=100)
            if st.button("🚀 틱톡 스튜디오 업로드 창 바로 열기", width="stretch"):
                open_platform_upload_page(tk["upload_url"])

    with u_col2:
        with st.container(border=True):
            st.markdown("#### 🟣 Instagram Reels (인스타 릴스)")
            ig = meta_pkg["instagram_reels"]
            st.text_area("인스타 릴스 본문 캡션 & 해시태그", value=ig["caption"], height=180)
            if st.button("🚀 인스타그램 업로드 창 바로 열기", width="stretch"):
                open_platform_upload_page(ig["upload_url"])

        with st.container(border=True):
            st.markdown("#### ⚫ Threads (쓰레드 바이럴 글 + 영상)")
            th = meta_pkg["threads"]
            st.text_area("쓰레드 게시글 본문", value=th["post_text"], height=140)
            if st.button("🚀 쓰레드 업로드 창 바로 열기", width="stretch"):
                open_platform_upload_page(th["upload_url"])
