import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="냉각장치와 비열비", page_icon="❄️", layout="wide")

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


# ------------------------------------------------------------------
# 냉각장치 애니메이션 (HTML + SVG + JavaScript)
# ------------------------------------------------------------------
ANIM_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 8px; background: #fff; color: #212529;
         font-family: "Noto Sans KR", "Malgun Gothic", "Apple SD Gothic Neo", sans-serif; }
  .wrap { max-width: 960px; margin: 0 auto; }
  .controls { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 8px; }
  .controls button, .controls select {
    font: inherit; font-size: 14px; padding: 6px 12px; border: 1px solid #ced4da;
    background: #fff; color: #212529; border-radius: 999px; cursor: pointer; }
  .controls button.on { background: #228be6; border-color: #228be6; color: #fff; }
  .sp { flex: 1; }
  svg { width: 100%; height: auto; display: block; background: #fff;
        border: 1px solid #e9ecef; border-radius: 14px; }
  svg text { font-family: inherit; }

  /* 단계 선택 시 나머지 부분을 흐리게, 선택 부분은 빛나게 */
  .dev { transition: opacity .4s; }
  svg[data-active="comp"] .dev:not(.dev-comp),
  svg[data-active="cond"] .dev:not(.dev-cond),
  svg[data-active="cap"]  .dev:not(.dev-cap),
  svg[data-active="evap"] .dev:not(.dev-evap) { opacity: .22; }
  svg[data-active="comp"] .dev-comp,
  svg[data-active="cond"] .dev-cond,
  svg[data-active="cap"]  .dev-cap,
  svg[data-active="evap"] .dev-evap { filter: drop-shadow(0 0 7px rgba(252,196,25,.95)); }

  /* 움직임 */
  .spin { animation: spin 1.1s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .vib { animation: vib .14s linear infinite; }
  @keyframes vib { 0%,100% { transform: translate(0,0); } 50% { transform: translate(.8px,.8px); } }
  .arw { fill: #fa5252; opacity: 0; }
  .arw.up    { animation: aup 1.6s ease-in-out infinite; }
  .arw.down  { animation: adn 1.6s ease-in-out infinite; }
  .arw.right { animation: arg 1.6s ease-in-out infinite; }
  @keyframes aup { 0% { transform: translateY(10px); opacity: 0; } 40% { opacity: 1; } 100% { transform: translateY(-8px); opacity: 0; } }
  @keyframes adn { 0% { transform: translateY(-10px); opacity: 0; } 40% { opacity: 1; } 100% { transform: translateY(8px); opacity: 0; } }
  @keyframes arg { 0% { transform: translateX(-8px); opacity: 0; } 40% { opacity: 1; } 100% { transform: translateX(14px); opacity: 0; } }
  .snow { fill: #74c0fc; animation: snow 3s ease-in-out infinite; }
  @keyframes snow { 0%,100% { transform: translateY(0); opacity: .25; } 50% { transform: translateY(10px); opacity: .9; } }
  .ring { fill: none; stroke: #fcc419; stroke-width: 4; opacity: 0; }
  .fire { opacity: 0; }
  svg[data-step="1"] .r1 { opacity: 1; animation: ringp 1s ease-in-out infinite; }
  svg[data-step="2"] .r2 { opacity: 1; animation: ringp 1s ease-in-out infinite; }
  svg[data-step="2"] .fire { opacity: 1; animation: flame .45s ease-in-out infinite alternate; }
  @keyframes ringp { 0%,100% { transform: scale(.8); } 50% { transform: scale(1.25); } }
  @keyframes flame { from { transform: translateY(0); } to { transform: translateY(-5px); } }
  svg.paused * { animation-play-state: paused !important; }

  /* 설명 패널 */
  #info { margin-top: 10px; padding: 12px 16px; border: 1px solid #e9ecef; border-radius: 12px; background: #f8f9fa; min-height: 96px; }
  #info .ttl { font-weight: 700; font-size: 17px; margin-bottom: 4px; }
  #info .txt { font-size: 15px; line-height: 1.55; }
  .chips { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { color: #fff; font-size: 13px; padding: 2px 10px; border-radius: 999px; }
  .legend { display: flex; flex-wrap: wrap; gap: 14px; margin-top: 8px; font-size: 13px; color: #495057; }
  .legend i { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 5px; vertical-align: -1px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="controls">
    <button data-s="0" class="on">전체 보기</button>
    <button data-s="1">① 흡입</button>
    <button data-s="2">② 토출</button>
    <button data-s="3">③ 응축기</button>
    <button data-s="4">④ 모세관</button>
    <button data-s="5">⑤ 증발기</button>
    <span class="sp"></span>
    <button id="bTour">▶ 자동 안내</button>
    <button id="bPause">⏸ 일시정지</button>
    <select id="spd">
      <option value="0.5">느리게</option>
      <option value="1" selected>보통</option>
      <option value="2">빠르게</option>
    </select>
  </div>

  <svg id="sv" viewBox="0 0 900 540" data-active="all" data-step="0">
    <!-- 배경: 냉장고, 응축기 -->
    <g class="dev dev-evap">
      <rect x="30" y="40" width="250" height="380" rx="18" fill="#e7f5ff" stroke="#74c0fc" stroke-width="3"/>
      <text class="snow" x="52" y="190" font-size="16" style="animation-delay:0s">❄</text>
      <text class="snow" x="58" y="300" font-size="14" style="animation-delay:1s">❄</text>
      <text class="snow" x="262" y="150" font-size="16" style="animation-delay:.5s">❄</text>
      <text class="snow" x="262" y="290" font-size="14" style="animation-delay:1.6s">❄</text>
    </g>
    <g class="dev dev-cond">
      <rect x="620" y="95" width="240" height="250" rx="10" fill="#fff5f5" stroke="#ffc9c9" stroke-width="2"/>
      <g id="fins"></g>
    </g>

    <!-- 배관 -->
    <g id="tubes"></g>

    <!-- 전경: 장치와 라벨 -->
    <g class="dev dev-evap">
      <text x="170" y="378" text-anchor="middle" font-size="16" font-weight="700" fill="#1971c2">증발기 (열 흡수)</text>
      <g id="evapArrows"></g>
    </g>
    <text x="48" y="66" font-size="14" font-weight="700" fill="#1971c2">냉장고 내부</text>
    <text id="temp" x="48" y="94" font-size="24" font-weight="700" fill="#1864ab">25°C</text>

    <g class="dev dev-cond">
      <text x="740" y="376" text-anchor="middle" font-size="16" font-weight="700" fill="#c92a2a">응축기 (열 방출)</text>
      <g id="condArrows"></g>
    </g>

    <g class="dev dev-cap">
      <text x="460" y="42" text-anchor="middle" font-size="16" font-weight="700" fill="#495057">모세관</text>
      <polyline id="spring" fill="none" stroke="#495057" stroke-width="1.6"/>
    </g>

    <g class="dev dev-comp">
      <g class="vib">
        <rect x="330" y="415" width="240" height="90" rx="14" fill="#adb5bd" stroke="#495057" stroke-width="3"/>
        <polygon points="340,440 560,452 560,468 340,480" fill="#343a40"/>
      </g>
      <rect x="360" y="380" width="60" height="36" rx="8" fill="#69db7c" stroke="#2b8a3e" stroke-width="2.5"/>
      <line x1="420" y1="398" x2="448" y2="398" stroke="#2b8a3e" stroke-width="4"/>
      <g transform="translate(470,398)">
        <g class="spin">
          <circle r="22" fill="#d3f9d8" stroke="#2b8a3e" stroke-width="2.5"/>
          <line x1="-16" y1="0" x2="16" y2="0" stroke="#2b8a3e" stroke-width="3"/>
          <line x1="0" y1="-16" x2="0" y2="16" stroke="#2b8a3e" stroke-width="3"/>
          <circle r="4" fill="#2b8a3e"/>
        </g>
      </g>
      <line x1="470" y1="420" x2="470" y2="432" stroke="#495057" stroke-width="4"/>
      <text x="450" y="528" text-anchor="middle" font-size="16" font-weight="700" fill="#343a40">압축기</text>
      <text x="322" y="436" text-anchor="end" font-size="12" fill="#495057">흡입구</text>
      <text x="578" y="436" text-anchor="start" font-size="12" fill="#495057">토출구</text>
    </g>

    <!-- 냉매 입자 -->
    <g id="parts"></g>

    <!-- 강조 표시 -->
    <g transform="translate(330,460)"><circle class="ring r1" r="18"/></g>
    <g transform="translate(570,460)"><circle class="ring r2" r="18"/></g>
    <text class="fire" x="586" y="424" font-size="24">🔥</text>
  </svg>

  <div id="info">
    <div class="ttl"></div>
    <div class="txt"></div>
    <div class="chips"></div>
  </div>

  <div class="legend">
    <span><i style="background:#e03131"></i>고온·고압 기체</span>
    <span><i style="background:#ff922b"></i>고압 액체</span>
    <span><i style="background:#1c7ed6"></i>저온·저압 액체</span>
    <span><i style="background:#66d9e8"></i>저온·저압 기체</span>
    <span style="color:#868e96">작은 점 = 기체, 큰 점 = 액체</span>
  </div>
</div>

<script>
const NS = "http://www.w3.org/2000/svg";
function el(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
const clamp01 = x => Math.max(0, Math.min(1, x));
const lerp = (a, b, t) => a.map((v, i) => v + (b[i] - v) * t);
function smooth(a, b, x) { const t = clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); }

/* ---------- 냉매가 흐르는 경로 (닫힌 고리) ---------- */
const P = [
  [330,460],[570,460],[610,460],[610,320],                 // 0~3  압축기 → 응축기 입구
  [640,320],[840,320],[840,270],[640,270],[640,220],[840,220],[840,170],[640,170],[640,120],[840,120], // 4~13 응축기
  [840,70],[520,70],[400,70],[250,70],                     // 14~17 모세관
  [250,120],[90,120],[90,170],[250,170],[250,220],[90,220],[90,270],[250,270],[250,320],[90,320], // 18~27 증발기
  [90,460],[330,460]                                       // 28~29 흡입관
];
const cum = [0];
for (let i = 1; i < P.length; i++) cum.push(cum[i-1] + Math.hypot(P[i][0]-P[i-1][0], P[i][1]-P[i-1][1]));
const L = cum[cum.length - 1];

function posAt(d) {
  let i = 1;
  while (i < cum.length - 1 && cum[i] < d) i++;
  const a = P[i-1], b = P[i], sl = cum[i] - cum[i-1], t = (d - cum[i-1]) / sl;
  const dx = (b[0]-a[0]) / sl, dy = (b[1]-a[1]) / sl;
  return { x: a[0] + (b[0]-a[0]) * t, y: a[1] + (b[1]-a[1]) * t, nx: -dy, ny: dx };
}

/* 구간별 속도: 압축되어 밀도가 높아지면 느리게, 증발하면 빠르게 */
const SK = [[0,1.0],[1,0.6],[4,0.6],[9,0.45],[17,0.45],[27,1.0],[29,1.0]];
function speedAt(d) {
  for (let i = 1; i < SK.length; i++) {
    const a = cum[SK[i-1][0]], b = cum[SK[i][0]];
    if (d <= b) { const t = b === a ? 0 : (d - a) / (b - a); return SK[i-1][1] + (SK[i][1] - SK[i-1][1]) * clamp01(t); }
  }
  return 1;
}
function zoneAt(d) {
  if (d >= cum[27]) return 'suction';
  if (d < cum[1])  return 'comp';
  if (d < cum[4])  return 'hot';
  if (d < cum[13]) return 'cond';
  if (d < cum[15]) return 'liq';
  if (d < cum[16]) return 'cap';
  return 'evap';
}
const DEV = { suction:'comp', comp:'comp', hot:'comp', cond:'cond', liq:'cap', cap:'cap', evap:'evap' };

const C = { cyan:[102,217,232], blue:[28,126,214], red:[224,49,49], orange:[255,146,43] };
const GAS_R = 3.2, LIQ_R = 5;
function props(d) {
  const z = zoneAt(d);
  if (z === 'suction') return { col: C.cyan, r: GAS_R, amp: 5 };
  if (z === 'comp') {
    const t = (d - cum[0]) / (cum[1] - cum[0]);
    return { col: lerp(C.cyan, C.red, t), r: GAS_R, amp: Math.max(1, (20 - 12*t) - GAS_R - 2) };
  }
  if (z === 'hot') return { col: C.red, r: GAS_R, amp: 5 };
  if (z === 'cond') {
    const t = (d - cum[4]) / (cum[13] - cum[4]);
    const k = smooth(.4, .6, t);
    return { col: lerp(C.red, C.orange, smooth(0, .5, t)), r: GAS_R + (LIQ_R - GAS_R) * k, amp: 5 * (1 - k) + 1.5 * k };
  }
  if (z === 'liq') return { col: C.orange, r: LIQ_R, amp: 1.5 };
  if (z === 'cap') {
    const t = (d - cum[15]) / (cum[16] - cum[15]);
    return { col: lerp(C.orange, C.blue, t), r: LIQ_R, amp: 1 };
  }
  const t = (d - cum[16]) / (cum[27] - cum[16]);
  const g = smooth(.3, .8, t);
  return { col: lerp(C.blue, C.cyan, g), r: LIQ_R + (GAS_R - LIQ_R) * g, amp: 1.5 + 3.5 * g };
}

/* ---------- 배관 그리기 ---------- */
const tubesG = document.getElementById('tubes');
const TUBES = [
  { a:27, b:29, col:'#a5d8ff', w:14, dev:'comp' },
  { a:1,  b:4,  col:'#ff8787', w:14, dev:'comp' },
  { a:4,  b:9,  col:'#ffa8a8', w:14, dev:'cond' },
  { a:9,  b:13, col:'#ffd8a8', w:14, dev:'cond' },
  { a:13, b:15, col:'#ffd8a8', w:14, dev:'cap'  },
  { a:15, b:16, col:'#dee2e6', w:7,  dev:'cap'  },
  { a:16, b:22, col:'#a5d8ff', w:14, dev:'evap' },
  { a:22, b:27, col:'#c5f6fa', w:14, dev:'evap' },
];
const ptsStr = (a, b) => P.slice(a, b + 1).map(p => p.join(',')).join(' ');
TUBES.forEach(t => el('polyline', { points: ptsStr(t.a, t.b), fill: 'none', stroke: '#868e96',
  'stroke-width': t.w + 4, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', class: 'dev dev-' + t.dev }, tubesG));
TUBES.forEach(t => el('polyline', { points: ptsStr(t.a, t.b), fill: 'none', stroke: t.col,
  'stroke-width': t.w, 'stroke-linecap': 'round', 'stroke-linejoin': 'round', class: 'dev dev-' + t.dev }, tubesG));

/* 모세관 스프링 모양 */
(function () {
  const s = [];
  for (let x = 520, k = 0; x >= 400; x -= 8, k++) s.push(x + ',' + (70 + (k % 2 ? 7 : -7)));
  document.getElementById('spring').setAttribute('points', s.join(' '));
})();

/* 응축기 냉각핀 */
(function () {
  const g = document.getElementById('fins');
  for (let x = 650; x <= 830; x += 20) el('line', { x1: x, y1: 100, x2: x, y2: 340, stroke: '#ffe3e3', 'stroke-width': 3 }, g);
})();

/* 열 흡수/방출 화살표 */
function arrow(parent, x, y, dir, delay) {
  const g = el('g', { transform: `translate(${x},${y})` }, parent);
  const pts = { up: '0,-7 7,5 -7,5', down: '0,7 7,-5 -7,-5', right: '7,0 -5,-7 -5,7' }[dir];
  const p = el('polygon', { points: pts, class: 'arw ' + dir }, g);
  p.style.animationDelay = delay + 's';
}
(function () {
  const eg = document.getElementById('evapArrows');
  [145, 195, 245, 295].forEach((y, i) => {
    arrow(eg, 130, y, 'up', i * 0.25);
    arrow(eg, 210, y, 'down', i * 0.25 + 0.4);
  });
  arrow(eg, 170, 96, 'down', 0.2);
  arrow(eg, 170, 346, 'up', 0.6);
  const cg = document.getElementById('condArrows');
  [120, 170, 220, 270, 320].forEach((y, i) => arrow(cg, 862, y, 'right', i * 0.3));
})();

/* ---------- 냉매 입자 만들기 ---------- */
const partsG = document.getElementById('parts');
const S0 = 27, BASE = 95;
const parts = [];
for (let d = 0; d < L - 10; d += S0 * speedAt(d)) {
  parts.push({
    d: d, ph: Math.random() * 6.28, fr: 2 + Math.random() * 3,
    el: el('circle', { r: 3, cx: -20, cy: -20, stroke: 'rgba(0,0,0,.35)', 'stroke-width': .6 }, partsG)
  });
}

/* ---------- 상태 ---------- */
const svg = document.getElementById('sv');
let running = true, mult = 1, tsec = 0, temp = 25, step = 0;
const STEPS = {
  0: { dev: 'all', ttl: '냉매가 열을 옮기는 순환',
       txt: '냉매는 <b>압축기 → 응축기 → 모세관 → 증발기 → 압축기</b>를 계속 돌면서, 냉장고 안의 열을 밖으로 옮깁니다. 위의 단계 버튼을 눌러 하나씩 살펴보세요.',
       chips: [['열을 안에서 밖으로 운반', '#495057']] },
  1: { dev: 'comp', ttl: '① 압축기 흡입구',
       txt: '증발기에서 나온 <b>저압의 차가운 기체</b> 냉매가 압축기로 들어옵니다.',
       chips: [['저압', '#1c7ed6'], ['저온', '#1c7ed6'], ['기체', '#0c8599']] },
  2: { dev: 'comp', ttl: '② 압축기 토출구',
       txt: '냉매가 압축되어 <b>압력과 온도가 크게 높아진 채</b>로 나옵니다. 이 토출 온도가 너무 높으면 윤활유와 부품이 상하므로, 압축해도 덜 뜨거워지는 <b>비열비가 작은 기체</b>가 유리합니다.',
       chips: [['고압', '#e03131'], ['고온 🔥', '#e03131'], ['기체', '#0c8599']] },
  3: { dev: 'cond', ttl: '③ 응축기',
       txt: '냉매가 <b>바깥으로 열을 방출</b>하면서 기체에서 액체로 변합니다.',
       chips: [['고압', '#e03131'], ['열 방출 →', '#f76707'], ['기체 → 액체', '#f76707']] },
  4: { dev: 'cap', ttl: '④ 모세관',
       txt: '좁고 긴 관을 지나면서 냉매의 <b>압력이 뚝 떨어지고</b> 온도도 내려갑니다.',
       chips: [['압력 감소', '#1c7ed6'], ['저온', '#1c7ed6'], ['액체', '#1c7ed6']] },
  5: { dev: 'evap', ttl: '⑤ 증발기',
       txt: '차가운 냉매가 <b>냉장고 안의 열을 흡수</b>하며 다시 기체로 변합니다. 그래서 냉장고 안이 시원해집니다. (내부 온도 숫자도 내려갑니다)',
       chips: [['저압', '#1c7ed6'], ['열 흡수', '#f76707'], ['액체 → 기체', '#0c8599']] },
};

const info = document.getElementById('info');
function setStep(k) {
  step = k;
  const s = STEPS[k];
  svg.dataset.active = s.dev;
  svg.dataset.step = k;
  document.querySelectorAll('button[data-s]').forEach(b => b.classList.toggle('on', +b.dataset.s === k));
  info.querySelector('.ttl').textContent = s.ttl;
  info.querySelector('.txt').innerHTML = s.txt;
  info.querySelector('.chips').innerHTML = s.chips.map(c => `<span class="chip" style="background:${c[1]}">${c[0]}</span>`).join('');
  render();
}

function render() {
  const act = STEPS[step].dev;
  for (const p of parts) {
    const pos = posAt(p.d), pr = props(p.d);
    const off = pr.amp * Math.sin(tsec * p.fr + p.ph);
    p.el.setAttribute('cx', (pos.x + pos.nx * off).toFixed(1));
    p.el.setAttribute('cy', (pos.y + pos.ny * off).toFixed(1));
    p.el.setAttribute('r', pr.r.toFixed(2));
    p.el.setAttribute('fill', `rgb(${pr.col[0] | 0},${pr.col[1] | 0},${pr.col[2] | 0})`);
    p.el.setAttribute('opacity', (act === 'all' || DEV[zoneAt(p.d)] === act) ? 0.95 : 0.18);
  }
  document.getElementById('temp').textContent = Math.round(temp) + '°C';
}

let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  if (running) {
    tsec += dt;
    for (const p of parts) {
      p.d += speedAt(p.d) * BASE * mult * dt;
      if (p.d >= L) p.d -= L;
    }
    temp += (4 - temp) * (1 - Math.exp(-dt * 0.12 * mult));
    render();
  }
  requestAnimationFrame(frame);
}

/* ---------- 버튼 ---------- */
const bTour = document.getElementById('bTour');
let tour = null;
function stopTour() {
  if (tour) { clearInterval(tour); tour = null; }
  bTour.textContent = '▶ 자동 안내';
  bTour.classList.remove('on');
}
document.querySelectorAll('button[data-s]').forEach(b => {
  b.onclick = () => { stopTour(); setStep(+b.dataset.s); };
});
bTour.onclick = () => {
  if (tour) { stopTour(); return; }
  let k = 1;
  setStep(1);
  bTour.textContent = '⏹ 안내 멈춤';
  bTour.classList.add('on');
  tour = setInterval(() => { k = k % 5 + 1; setStep(k); }, 5000);
};
document.getElementById('bPause').onclick = function () {
  running = !running;
  svg.classList.toggle('paused', !running);
  this.textContent = running ? '⏸ 일시정지' : '▶ 재생';
};
document.getElementById('spd').onchange = function () { mult = +this.value; };

setStep(0);
requestAnimationFrame(frame);
</script>
</body>
</html>
"""

st.title("❄️ 냉각장치에는 왜 비열비가 작은 기체를 쓸까?")

tab1, tab2, tab3 = st.tabs(["1️⃣ 냉각장치 원리", "2️⃣ 기체 비교", "3️⃣ 결론"])

# ------------------------------------------------------------------
# 탭 1: 작동 원리 (움직이는 냉각장치)
# ------------------------------------------------------------------
with tab1:
    st.subheader("냉매는 이렇게 돌면서 열을 옮깁니다")
    st.caption("점 하나하나가 냉매입니다. 색은 온도(빨강=뜨거움, 파랑=차가움), 크기는 상태(작은 점=기체, 큰 점=액체)를 뜻합니다. "
               "단계 버튼을 누르거나 '자동 안내'를 눌러보세요.")
    components.html(ANIM_HTML, height=830, scrolling=False)

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
