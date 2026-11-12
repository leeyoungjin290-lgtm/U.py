import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="냉각장치 비열비 시뮬레이터", page_icon="❄️", layout="wide")

R = 8.314  # J/(mol·K)

# ------------------------------------------------------------------
# 기체 데이터 (비열비 γ). 이상기체는 γ = (f+2)/f 로 계산,
# 실제 냉매는 증기 상태의 근사값을 사용 (유효 자유도 f_eff = 2/(γ-1))
# ------------------------------------------------------------------
GASES = {
    "헬륨 He (단원자, f=3)": 5 / 3,
    "아르곤 Ar (단원자, f=3)": 5 / 3,
    "공기 / 질소 N₂ (이원자, f=5)": 7 / 5,
    "이산화탄소 CO₂ (다원자 근사, f=6)": 8 / 6,
    "암모니아 NH₃ (R-717, 근사)": 1.31,
    "프로판 (R-290, 근사)": 1.13,
    "R-134a (냉매 증기, 근사)": 1.10,
    "이소부탄 (R-600a, 근사)": 1.09,
}
CUSTOM = "직접 입력 (자유도 f)"


def gamma_from_f(f):
    return (f + 2) / f


def f_from_gamma(g):
    return 2 / (g - 1)


def adiabatic_T2(T1_K, ratio, gamma):
    """단열 압축 후 온도 (K)"""
    return T1_K * ratio ** ((gamma - 1) / gamma)


def life_years(T_C, L0, T_ref, dT_half):
    """T_ref 에서 수명 L0, 온도가 dT_half 올라갈 때마다 수명 절반 (간이 모델)"""
    return L0 * 2 ** (-(T_C - T_ref) / dT_half)


# ------------------------------------------------------------------
# 사이드바
# ------------------------------------------------------------------
st.sidebar.title("⚙️ 입력 조건")

choice = st.sidebar.selectbox("냉매(기체) 선택", list(GASES.keys()) + [CUSTOM], index=2)
if choice == CUSTOM:
    f = st.sidebar.slider("자유도 f", 3.0, 30.0, 5.0, 0.5)
    gamma = gamma_from_f(f)
else:
    gamma = GASES[choice]
    f = f_from_gamma(gamma)

st.sidebar.markdown("**압축기 운전 조건**")
T1_C = st.sidebar.number_input("흡입구 온도 T₁ (°C)", -30.0, 60.0, 20.0, 1.0)
P1 = st.sidebar.number_input("흡입 압력 P₁ (bar)", 0.5, 20.0, 1.0, 0.1)
P2 = st.sidebar.number_input("토출 압력 P₂ (bar)", 1.0, 60.0, 8.0, 0.5)

st.sidebar.markdown("**수명 모델 가정**")
oil_limit = st.sidebar.number_input("윤활유 허용 한계 온도 (°C)", 80.0, 250.0, 150.0, 5.0)
L0 = st.sidebar.number_input("기준 온도에서의 수명 (년)", 1.0, 50.0, 15.0, 1.0)
T_ref = st.sidebar.number_input("기준 온도 (°C)", 40.0, 200.0, 80.0, 5.0)
dT_half = st.sidebar.number_input("수명이 절반이 되는 온도 상승폭 (°C)", 5.0, 30.0, 10.0, 1.0)

if P2 <= P1:
    st.error("토출 압력 P₂는 흡입 압력 P₁보다 커야 합니다.")
    st.stop()

ratio = P2 / P1
T1_K = T1_C + 273.15
T2_K = adiabatic_T2(T1_K, ratio, gamma)
T2_C = T2_K - 273.15
Cv = f / 2 * R
Cp = (f + 2) / 2 * R
life = life_years(T2_C, L0, T_ref, dT_half)

# ------------------------------------------------------------------
# 본문
# ------------------------------------------------------------------
st.title("❄️ 냉각장치 수명과 기체의 비열비 시뮬레이터")
st.caption("단열 압축 공식 T₂ = T₁ · (P₂/P₁)^((γ-1)/γ) 와 γ = C_p / C_v = (f+2)/f 를 이용한 교육용 시뮬레이터")

c1, c2, c3, c4 = st.columns(4)
c1.metric("비열비 γ", f"{gamma:.3f}")
c2.metric("압력비 P₂/P₁", f"{ratio:.2f}")
c3.metric("토출 온도 T₂", f"{T2_C:.1f} °C", f"{T2_C - T1_C:+.1f} °C (T₁ 대비)")
c4.metric("추정 압축기 수명", f"{life:.1f} 년")

if T2_C > oil_limit:
    st.error(f"⚠️ 토출 온도({T2_C:.0f}°C)가 윤활유 허용 한계({oil_limit:.0f}°C)를 넘습니다. "
             "윤활유 열화·부품 손상 위험이 큽니다.")
else:
    st.success(f"✅ 토출 온도({T2_C:.0f}°C)가 윤활유 허용 한계({oil_limit:.0f}°C) 이내입니다.")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["① 온도 계산", "② 압력비-온도 그래프", "③ 기체별 수명 비교", "④ 자유도와 비열비", "⑤ 참고: 이상기체 COP"]
)

# ---------------- 탭 1 ----------------
with tab1:
    st.subheader("선택한 조건의 계산 과정")
    st.latex(r"\gamma=\frac{C_P}{C_V}=\frac{f+2}{f}")
    st.markdown(f"- 자유도 f = **{f:.2f}**  →  γ = (f+2)/f = **{gamma:.3f}**")
    st.markdown(f"- C_v = (f/2)R = **{Cv:.2f} J/(mol·K)**,  C_p = ((f+2)/2)R = **{Cp:.2f} J/(mol·K)**")
    st.latex(r"T_2 = T_1\left(\frac{P_2}{P_1}\right)^{\frac{\gamma-1}{\gamma}}")
    exponent = (gamma - 1) / gamma
    st.markdown(
        f"- T₁ = {T1_K:.2f} K,  P₂/P₁ = {ratio:.2f},  지수 (γ-1)/γ = {exponent:.4f}\n"
        f"- T₂ = {T1_K:.2f} × {ratio:.2f}^{exponent:.4f} = **{T2_K:.2f} K = {T2_C:.1f} °C**"
    )
    st.info(
        "비열비 γ가 클수록 지수 (γ-1)/γ가 커져 같은 압력비에서도 압축 후 온도가 더 많이 오릅니다. "
        "그래서 토출구 온도를 낮게 유지하려면 비열비가 작은 기체가 유리합니다."
    )
    st.caption("※ 실제 냉매는 응축기에서 상변화(기체→액체)를 하고, 압축 중에도 이상기체와 차이가 있어 "
               "실제 토출 온도는 이 값과 다를 수 있습니다. 이 앱은 비열비 효과를 보기 위한 단순 모델입니다.")

# ---------------- 탭 2 ----------------
with tab2:
    st.subheader("압력비에 따른 토출 온도")
    r_arr = np.linspace(1, 15, 200)
    fig = go.Figure()
    for name, g in GASES.items():
        fig.add_trace(go.Scatter(
            x=r_arr, y=adiabatic_T2(T1_K, r_arr, g) - 273.15, mode="lines", name=name))
    if choice == CUSTOM:
        fig.add_trace(go.Scatter(
            x=r_arr, y=adiabatic_T2(T1_K, r_arr, gamma) - 273.15,
            mode="lines", name=f"직접 입력 (f={f:.1f})", line=dict(color="black", dash="dash", width=3)))
    fig.add_hline(y=oil_limit, line_dash="dot", line_color="red",
                  annotation_text="윤활유 허용 한계", annotation_position="top left")
    fig.add_trace(go.Scatter(x=[ratio], y=[T2_C], mode="markers", name="현재 조건",
                             marker=dict(size=13, color="black", symbol="x")))
    fig.update_layout(xaxis_title="압력비 P₂/P₁", yaxis_title="토출 온도 T₂ (°C)",
                      height=520, legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fig, use_container_width=True)

# ---------------- 탭 3 ----------------
with tab3:
    st.subheader("같은 조건에서 기체별 토출 온도와 추정 수명")
    rows = []
    for name, g in GASES.items():
        t2 = adiabatic_T2(T1_K, ratio, g) - 273.15
        rows.append({
            "기체": name, "비열비 γ": round(g, 3), "토출 온도 (°C)": round(t2, 1),
            "한계 초과": "초과 ⚠️" if t2 > oil_limit else "정상",
            "추정 수명 (년)": round(life_years(t2, L0, T_ref, dT_half), 2),
        })
    df = pd.DataFrame(rows).sort_values("비열비 γ")
    st.dataframe(df, use_container_width=True, hide_index=True)

    colA, colB = st.columns(2)
    with colA:
        fig_t = go.Figure(go.Bar(x=df["기체"], y=df["토출 온도 (°C)"], marker_color="#e4572e"))
        fig_t.add_hline(y=oil_limit, line_dash="dot", line_color="red")
        fig_t.update_layout(title="토출 온도", yaxis_title="°C", height=420)
        st.plotly_chart(fig_t, use_container_width=True)
    with colB:
        fig_l = go.Figure(go.Bar(x=df["기체"], y=df["추정 수명 (년)"], marker_color="#2e86ab"))
        fig_l.update_layout(title="추정 압축기 수명", yaxis_title="년", height=420)
        st.plotly_chart(fig_l, use_container_width=True)

    st.caption(
        "수명 모델: L = L₀ × 2^(-(T₂ - T_ref)/ΔT). 전기 절연체 등에서 쓰이는 '온도가 약 10°C 오르면 수명이 "
        "절반' 경험칙을 단순화한 가정이며, 실제 수명 예측값이 아닙니다. 사이드바에서 가정값을 바꿔보세요."
    )

# ---------------- 탭 4 ----------------
with tab4:
    st.subheader("자유도 f에 따른 C_v, C_p, γ")
    f_arr = np.arange(3, 31, 1)
    tbl = pd.DataFrame({
        "자유도 f": f_arr,
        "C_v = (f/2)R": np.round(f_arr / 2 * R, 2),
        "C_p = ((f+2)/2)R": np.round((f_arr + 2) / 2 * R, 2),
        "γ = (f+2)/f": np.round(gamma_from_f(f_arr), 4),
    })
    fg = go.Figure()
    f_line = np.linspace(2.5, 30, 200)
    fg.add_trace(go.Scatter(x=f_line, y=gamma_from_f(f_line), mode="lines", name="γ = (f+2)/f"))
    fg.add_hline(y=1.0, line_dash="dot", line_color="gray",
                 annotation_text="γ = 1 (극한, 도달하지 않음)")
    fg.add_trace(go.Scatter(x=[f], y=[gamma], mode="markers", name="선택한 기체",
                            marker=dict(size=13, color="red")))
    fg.update_layout(xaxis_title="자유도 f", yaxis_title="비열비 γ", height=450)
    st.plotly_chart(fg, use_container_width=True)
    st.markdown("자유도가 클수록 γ는 1에 가까워지지만 **1보다 작아지지는 않습니다.** (C_p = C_v + R > C_v)")
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ---------------- 탭 5 ----------------
with tab5:
    st.subheader("참고: 이상기체 역브레이턴 사이클의 성능계수(COP)")
    st.latex(r"COP = \frac{1}{\left(P_2/P_1\right)^{\frac{\gamma-1}{\gamma}}-1}")
    r2 = np.linspace(1.2, 15, 200)
    fc = go.Figure()
    for name, g in GASES.items():
        fc.add_trace(go.Scatter(x=r2, y=1 / (r2 ** ((g - 1) / g) - 1), mode="lines", name=name))
    fc.update_layout(xaxis_title="압력비 P₂/P₁", yaxis_title="COP", yaxis_range=[0, 30],
                     height=480, legend=dict(orientation="h", y=-0.25))
    st.plotly_chart(fc, use_container_width=True)
    cop_now = 1 / (ratio ** ((gamma - 1) / gamma) - 1)
    st.markdown(f"현재 조건의 이상기체 COP ≈ **{cop_now:.2f}**")
    st.warning(
        "이 COP는 상변화 없이 기체만 압축·팽창시키는 이상 사이클의 값입니다. 비열비가 작을수록 같은 압력비에서 "
        "COP가 크게 나오는 경향은 보여주지만, 증기압축식 냉장고의 실제 COP와는 다릅니다. "
        "'온도를 낮게 유지(수명)'와 '효율'을 함께 보는 참고 자료로 활용하세요."
    )
