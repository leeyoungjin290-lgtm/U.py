import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="냉각장치와 비열비", page_icon="❄️", layout="centered")

# ------------------------------------------------------------------
# 고정 설정 (발표용이라 사용자가 바꾸는 값은 압력비 하나뿐)
# ------------------------------------------------------------------
T1_C = 20.0          # 압축기 흡입 온도 (°C)
LIMIT_C = 150.0      # 윤활유가 견딜 수 있는 온도 (°C, 가정값)
GAS_BIG = ("비열비가 큰 기체", 1.67)    # 예: 헬륨, 아르곤 (γ = 5/3)
GAS_SMALL = ("비열비가 작은 기체", 1.10)  # 예: 냉매 증기 (γ ≈ 1.1)


def discharge_temp_C(ratio, gamma):
    """단열 압축 후 온도: T2 = T1 * (P2/P1)^((γ-1)/γ)"""
    T1_K = T1_C + 273.15
    return T1_K * ratio ** ((gamma - 1) / gamma) - 273.15


st.title("❄️ 냉각장치에는 왜 비열비가 작은 기체를 쓸까?")

tab1, tab2, tab3 = st.tabs(["1️⃣ 냉각장치 원리", "2️⃣ 기체 비교", "3️⃣ 결론"])

# ------------------------------------------------------------------
# 탭 1: 작동 원리 (단계를 고르면 해당 부품이 강조됨)
# ------------------------------------------------------------------
with tab1:
    st.subheader("냉매는 이렇게 돌면서 열을 옮깁니다")

    STEPS = {
        "① 압축기 흡입": ("압축기", "증발기에서 나온 **저압 기체** 냉매가 압축기로 들어옵니다."),
        "② 압축기 토출": ("압축기", "냉매가 압축되어 **압력과 온도가 높아진 상태**로 나갑니다. 🔥 이 온도가 핵심!"),
        "③ 응축기": ("응축기", "냉매가 **바깥으로 열을 버리며** 액체로 변합니다."),
        "④ 모세관": ("모세관", "냉매의 **압력이 낮아집니다.**"),
        "⑤ 증발기": ("증발기", "냉매가 **주변의 열을 흡수**하며 다시 기체로 변합니다. → 냉장고 안이 시원해집니다."),
    }
    step = st.radio("단계를 선택하세요", list(STEPS.keys()), horizontal=True)
    active, desc = STEPS[step]
    hot = step == "② 압축기 토출"

    def node(name):
        if name == active:
            color = "#ff6b6b" if hot else "#4dabf7"
            return f'"{name}" [style=filled, fillcolor="{color}", fontcolor=white, penwidth=3]'
        return f'"{name}" [style=filled, fillcolor="#f1f3f5"]'

    dot = f"""
    digraph G {{
        rankdir=LR;
        node [shape=box, style="rounded,filled", fontname="sans-serif", fontsize=16, margin="0.25,0.15"];
        edge [fontname="sans-serif", fontsize=12];
        {node("증발기")}
        {node("압축기")}
        {node("응축기")}
        {node("모세관")}
        "증발기" -> "압축기" [label="저압 기체"];
        "압축기" -> "응축기" [label="고온·고압 기체"];
        "응축기" -> "모세관" [label="고압 액체"];
        "모세관" -> "증발기" [label="저압 액체"];
    }}
    """
    st.graphviz_chart(dot, use_container_width=True)
    st.info(desc)

# ------------------------------------------------------------------
# 탭 2: 기체 비교 (슬라이더 하나)
# ------------------------------------------------------------------
with tab2:
    st.subheader("같은 압력으로 압축했을 때, 기체마다 얼마나 뜨거워질까?")
    ratio = st.slider("압축 정도 (압력비 P₂/P₁)", 2.0, 12.0, 8.0, 0.5,
                      help="압축기 출구 압력이 입구 압력의 몇 배인지")

    names = [GAS_BIG[0], GAS_SMALL[0]]
    temps = [discharge_temp_C(ratio, GAS_BIG[1]), discharge_temp_C(ratio, GAS_SMALL[1])]
    colors = ["#ff6b6b" if t > LIMIT_C else "#51cf66" for t in temps]

    fig = go.Figure(go.Bar(
        x=names, y=temps, marker_color=colors,
        text=[f"{t:.0f}°C" for t in temps], textposition="outside", textfont=dict(size=22),
    ))
    fig.add_hline(y=LIMIT_C, line_dash="dash", line_color="red",
                  annotation_text="윤활유 한계 온도", annotation_position="top left")
    fig.update_layout(yaxis_title="압축기 토출 온도 (°C)", yaxis_range=[0, max(temps + [LIMIT_C]) * 1.25],
                      height=450, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    for col, (name, g), t in zip((c1, c2), (GAS_BIG, GAS_SMALL), temps):
        with col:
            st.markdown(f"**{name}** (γ = {g:.2f})")
            if t > LIMIT_C:
                st.error("🔥 윤활유가 타고 부품이 손상됩니다!")
            else:
                st.success("✅ 안전한 온도입니다.")

    st.caption("T₂ = T₁ × (P₂/P₁)^((γ-1)/γ), 흡입 온도 20°C 가정. "
               "이상기체 단열 압축 모델이며 실제 냉매의 값과는 차이가 있을 수 있습니다.")

# ------------------------------------------------------------------
# 탭 3: 결론
# ------------------------------------------------------------------
with tab3:
    st.subheader("정리")
    st.markdown(
        """
        1. 압축기에서 냉매를 압축하면 **온도가 오릅니다.**
        2. **비열비가 큰 기체**일수록 같은 압축에서 **더 뜨거워집니다.**
        3. 너무 뜨거우면 **윤활유가 변질**되고 **부품이 손상**되어 압축기 수명이 줄어듭니다.
        4. 그래서 냉각장치에는 **비열비가 작은 기체**를 쓰는 것이 유리합니다.
        """
    )
    st.success("효율만이 아니라 **수명**까지 생각해야 오래 쓰는 냉각장치가 됩니다.")
