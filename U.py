import streamlit as st
from openai import OpenAI
import json

st.set_page_config(
    page_title="상황별 영어 문장 추천",
    page_icon="💬",
    layout="centered"
)

# OpenAI 설정
try:
    api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=api_key)
except Exception:
    client = None

# 화면
st.title("💬 상황별 영어 문장 추천")
st.write("원하는 상황을 입력하면 그 상황에서 사용할 수 있는 영어 문장을 추천해줍니다.")

st.info(
    "예시: 친구에게 숙제를 같이 하자고 말하고 싶어"
)

# 상황 입력
situation = st.text_area(
    "어떤 상황인가요?",
    placeholder="예: 외국인 친구에게 길을 물어보고 싶어",
    height=120
)

# 영어 수준과 문장 수
col1, col2 = st.columns(2)

with col1:
    level = st.selectbox(
        "영어 수준",
        ["쉬운 영어", "보통 영어", "자연스러운 영어"]
    )

with col2:
    number = st.selectbox(
        "추천받을 문장 수",
        [3, 5, 7]
    )

# AI 분석
if st.button(
    "✨ 영어 문장 추천받기",
    use_container_width=True
):

    if client is None:
        st.error(
            "OPENAI_API_KEY가 설정되어 있지 않습니다. "
            "Streamlit Cloud의 Secrets에 OPENAI_API_KEY를 추가해주세요."
        )

    elif not situation.strip():
        st.warning("상황을 먼저 입력해주세요.")

    else:

        with st.spinner("상황에 맞는 영어 문장을 만들고 있습니다..."):

            prompt = f"""
너는 영어 회화 전문가다.

사용자가 설명한 상황을 이해하고,
그 상황에서 실제로 사용할 수 있는 영어 문장을 추천해라.

상황:
{situation}

영어 수준:
{level}

추천 문장 수:
{number}개

규칙:
1. 실제 일상생활에서 자연스럽게 사용할 수 있는 문장을 만들어라.
2. 상황과 관계없는 문장은 만들지 마라.
3. 너무 어려운 표현은 피하라.
4. 각 문장마다 한국어 뜻을 제공하라.
5. 각 문장이 언제 사용하기 좋은지 짧게 설명하라.
6. 가능하면 서로 다른 표현을 추천하라.
7. 문법적으로 정확해야 한다.
8. 사용자가 바로 복사해서 사용할 수 있도록 문장을 완성형으로 작성하라.
9. 학생이 이해하기 쉽게 설명하라.

다음 JSON 형식으로만 답해라.

{{
    "situation": "상황 요약",
    "sentences": [
        {{
            "english": "영어 문장",
            "korean": "한국어 뜻",
            "usage": "사용하기 좋은 상황"
        }}
    ]
}}
"""

            try:

                response = client.responses.create(
                    model="gpt-5.4-nano",
                    input=prompt
                )

                result_text = response.output_text.strip()

                # AI가 코드블록으로 답한 경우 제거
                if result_text.startswith("```"):
                    result_text = result_text.replace(
                        "```json", ""
                    )
                    result_text = result_text.replace(
                        "```", ""
                    )
                    result_text = result_text.strip()

                result = json.loads(result_text)

                # 결과 출력
                st.success("문장 추천 완료!")

                st.write(
                    f"### 📌 상황\n{result['situation']}"
                )

                st.divider()

                for i, sentence in enumerate(
                    result["sentences"], 1
                ):

                    st.markdown(
                        f"### {i}. {sentence['english']}"
                    )

                    st.write(
                        f"🇰🇷 **뜻:** {sentence['korean']}"
                    )

                    st.caption(
                        f"💡 {sentence['usage']}"
                    )

                    st.divider()

            except json.JSONDecodeError:
                st.error(
                    "AI의 응답을 읽는 중 오류가 발생했습니다."
                )
                st.code(result_text)

            except Exception as e:
                st.error(
                    f"AI 분석 중 오류가 발생했습니다: {e}"
                )

# 사용 예시
st.subheader("💡 입력 예시")

examples = [
    "친구에게 숙제를 같이 하자고 말하고 싶어",
    "선생님에게 질문하고 싶어",
    "외국인 친구에게 처음 인사하고 싶어",
    "식당에서 음식을 주문하고 싶어",
    "친구에게 미안하다고 말하고 싶어",
    "영어 발표를 시작할 때 사용할 문장이 필요해"
]

for example in examples:
    st.write(f"• {example}")
