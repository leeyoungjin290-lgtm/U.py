import streamlit as st
from openai import OpenAI
import json

st.set_page_config(
    page_title="시간 관리 효율 계산기",
    page_icon="⏱️",
    layout="centered"
)

# =========================
# OpenAI 설정
# =========================

try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except Exception:
    client = None


# =========================
# 기본 설정
# =========================

st.title("⏱️ 시간 관리 효율 계산기")
st.write("할 일의 효율을 기준으로 적정 시간을 계산해줍니다.")

st.info(
    "기준 예시: 1시간에 효율 10을 낼 수 있다면 "
    "효율 20의 일은 약 2시간이 적정합니다."
)

# =========================
# 기준 효율
# =========================

st.subheader("1. 나의 기준 효율")

base_efficiency = st.number_input(
    "1시간 동안 낼 수 있는 효율",
    min_value=0.1,
    value=10.0,
    step=0.5
)

st.write(f"현재 기준: **1시간 = 효율 {base_efficiency:g}**")


# =========================
# 직접 계산
# =========================

st.subheader("2. 목표 효율 입력")

target_efficiency = st.number_input(
    "목표 효율",
    min_value=0.1,
    value=20.0,
    step=0.5
)

required_hours = target_efficiency / base_efficiency

hours = int(required_hours)
minutes = round((required_hours - hours) * 60)

if hours > 0:
    time_text = f"{hours}시간 {minutes}분"
else:
    time_text = f"{minutes}분"

st.success(
    f"### 추천 시간: {time_text}"
)

st.write(
    f"효율 {target_efficiency:g}을 목표로 한다면 "
    f"약 **{required_hours:.2f}시간**을 사용하는 것이 적정합니다."
)


# =========================
# 효율 분석
# =========================

st.subheader("3. 효율 분석")

actual_hours = st.number_input(
    "실제로 사용할 시간",
    min_value=0.1,
    value=float(required_hours),
    step=0.5
)

actual_efficiency = actual_hours * base_efficiency

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "예상 효율",
        f"{actual_efficiency:.1f}"
    )

with col2:
    difference = actual_efficiency - target_efficiency

    if difference >= 0:
        st.metric(
            "목표와의 차이",
            f"+{difference:.1f}"
        )
    else:
        st.metric(
            "목표와의 차이",
            f"{difference:.1f}"
        )


# =========================
# OpenAI AI 분석
# =========================

st.divider()

st.subheader("🤖 AI 시간 분석")

task = st.text_area(
    "할 일을 입력하세요",
    placeholder="예: 물리 수행평가 보고서를 작성해야 한다."
)

if st.button("AI에게 적정 시간 분석받기", use_container_width=True):

    if client is None:
        st.error(
            "OPENAI_API_KEY가 설정되어 있지 않습니다. "
            "Streamlit Cloud의 Secrets에 OPENAI_API_KEY를 추가해주세요."
        )

    elif not task.strip():
        st.warning("할 일을 먼저 입력해주세요.")

    else:

        with st.spinner("AI가 작업량을 분석하고 있습니다..."):

            prompt = f"""
너는 시간 관리 전문가다.

사용자가 입력한 할 일을 분석해서 적정 작업 시간을 계산한다.

사용자의 기준 효율:
1시간당 {base_efficiency} 효율

할 일:
{task}

다음 기준으로 분석한다.

1. 이 작업의 난이도
2. 예상되는 목표 효율
3. 기준 효율을 이용한 적정 작업 시간
4. 너무 짧게 했을 때 발생할 문제
5. 너무 오래 했을 때 발생할 문제
6. 효율적인 작업 방법

계산 공식:
적정 시간 = 목표 효율 / 시간당 기준 효율

반드시 JSON 형식으로만 답한다.

JSON 형식:
{{
    "difficulty": "쉬움/보통/어려움",
    "target_efficiency": 숫자,
    "recommended_hours": 숫자,
    "short_time_problem": "설명",
    "long_time_problem": "설명",
    "method": "효율적인 작업 방법"
}}
"""

            try:

                response = client.responses.create(
                    model="gpt-5.4-nano",
                    input=prompt
                )

                result_text = response.output_text

                # JSON 부분만 추출
                result_text = result_text.strip()

                if result_text.startswith("```"):
                    result_text = result_text.replace("```json", "")
                    result_text = result_text.replace("```", "")
                    result_text = result_text.strip()

                result = json.loads(result_text)

                # =========================
                # 결과 출력
                # =========================

                st.success("AI 분석 완료!")

                st.write(
                    f"### 난이도: {result['difficulty']}"
                )

                ai_efficiency = float(
                    result["target_efficiency"]
                )

                ai_hours = float(
                    result["recommended_hours"]
                )

                ai_minutes = round(ai_hours * 60)

                st.metric(
                    "AI 추천 효율",
                    f"{ai_efficiency:g}"
                )

                st.metric(
                    "AI 추천 작업 시간",
                    f"{ai_minutes}분"
                )

                st.write("### 📌 분석")

                st.write(
                    f"**짧게 끝내면:** "
                    f"{result['short_time_problem']}"
                )

                st.write(
                    f"**너무 오래 하면:** "
                    f"{result['long_time_problem']}"
                )

                st.write(
                    f"**추천 방법:** "
                    f"{result['method']}"
                )

                # 계산 검증
                calculated_time = (
                    ai_efficiency / base_efficiency
                )

                st.info(
                    f"기준 효율로 계산한 예상 시간: "
                    f"**{calculated_time:.2f}시간 "
                    f"({calculated_time * 60:.0f}분)**"
                )

            except json.JSONDecodeError:
                st.error(
                    "AI가 올바른 형식으로 응답하지 않았습니다."
                )
                st.write(result_text)

            except Exception as e:
                st.error(
                    f"AI 분석 중 오류가 발생했습니다: {e}"
                )


# =========================
# 계산 공식 표시
# =========================

st.divider()

st.subheader("📐 계산 공식")

st.code(
    "적정 시간 = 목표 효율 ÷ 시간당 기준 효율"
)

st.write(
    f"예시: {target_efficiency:g} ÷ "
    f"{base_efficiency:g} = "
    f"{required_hours:.2f}시간"
)
