import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="확률 + 합성 시뮬레이터", layout="wide")
st.title("🎲 확률 + 합성 시뮬레이터 (Web)")

# 확률표 업로드
uploaded_file = st.file_uploader("📁 확률표 엑셀 파일 업로드", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)

        # 확률 값 확인 및 보정
        if df["확률"].max() <= 1:
            df["확률"] *= 100

        df = df.sort_values(by="확률", ascending=False).reset_index(drop=True)
        df["누적확률"] = df["확률"].cumsum()

        st.success("✅ 확률표 로드 완료!")
        st.dataframe(df)

        # 시뮬레이션 설정
        tab1, tab2 = st.tabs(["🎰 뽑기 시뮬레이터", "🔨 합성 시뮬레이터"])

        with tab1:
            st.subheader("🎰 뽑기 시뮬레이션")
            draw_count = st.number_input("뽑기 횟수", min_value=1, value=100)
            pity_limit = st.number_input("천장 횟수", min_value=1, value=20)

            if st.button("뽑기 시작"):
                pity_counter = 0
                s_pool = df[df["등급"] == "S"]
                draw_results = []

                for i in range(1, draw_count + 1):
                    is_pity = pity_counter >= pity_limit
                    if is_pity and not s_pool.empty:
                        chosen = s_pool.sample(1).iloc[0]
                        pity_counter = 0
                    else:
                        rand = random.uniform(0, 100)
                        chosen = df[df["누적확률"] > rand].iloc[0]
                        pity_counter = 0 if chosen["등급"] == "S" else pity_counter + 1

                    draw_results.append({
                        "회차": i,
                        "등급": chosen["등급"],
                        "구성품": chosen["구성품"],
                        "천장": "천장 발동!" if is_pity else ""
                    })

                result_df = pd.DataFrame(draw_results)
                st.dataframe(result_df)

                # 등급별 통계
                grade_counts = result_df["등급"].value_counts()
                st.write("등급별 통계:", grade_counts)

                # 천장 발동 횟수
                pity_count = (result_df["천장"] == "천장 발동!").sum()
                st.write(f"천장 발동 횟수: {pity_count}")

                # 등급별 + 천장 발동 구분된 통계 테이블
                pivot_table = pd.pivot_table(result_df, index="등급", columns="천장", aggfunc="size", fill_value=0)
                st.write("등급별 & 천장 발동 여부 통계:")
                st.dataframe(pivot_table)

                # 비용 계산
                cost_per_11pull = 27500
                total_11pulls = draw_count // 11 + (1 if draw_count % 11 != 0 else 0)
                total_cost = total_11pulls * cost_per_11pull
                s_count = grade_counts.get("S", 0)

                st.write(f"총 뽑기 비용: {total_cost}원")
                if s_count:
                    st.write(f"S등급 1개당 평균 비용: {total_cost / s_count:.2f}원")

        with tab2:
            st.subheader("🔨 합성 시뮬레이터")
            start_grade = st.selectbox("시작 등급 선택", ["A", "S", "R"])
            synth_count = st.number_input("합성 횟수", min_value=1, value=20)
            synth_pity = st.number_input("합성 천장", min_value=1, value=5)

            synthesis_rates = {"C": 25, "B": 21, "A": 18, "S": 16, "R": 15}
            grade_order = ["C", "B", "A", "S", "R", "SR"]

            def get_next_grade(g):
                idx = grade_order.index(g)
                return grade_order[idx + 1] if idx + 1 < len(grade_order) else g

            if st.button("합성 시작"):
                success = 0
                fail = 0
                pity_success = 0
                fail_streak = 0
                logs = []
                next_grade = get_next_grade(start_grade)
                rate = synthesis_rates.get(start_grade, 0)

                for i in range(1, synth_count + 1):
                    is_pity = fail_streak >= synth_pity
                    rand = random.randint(1, 100)

                    if is_pity or rand <= rate:
                        logs.append(f"{i:2}회차: {start_grade} → {next_grade} [성공]" + (" (천장 발동!)" if is_pity else ""))
                        success += 1
                        if is_pity:
                            pity_success += 1
                        fail_streak = 0
                    else:
                        logs.append(f"{i:2}회차: {start_grade} → 실패")
                        fail += 1
                        fail_streak += 1

                st.text_area("🎯 결과 로그", "\n".join(logs), height=300)
                st.write(f"총 시도: {synth_count}, 성공: {success}, 실패: {fail}, 천장 성공: {pity_success}")
                st.write(f"성공률: {success / synth_count * 100:.2f}%")

    except Exception as e:
        st.error(f"❌ 파일을 읽는 중 오류 발생: {e}")
else:
    st.info("👆 먼저 확률표 엑셀 파일을 업로드해 주세요.")
