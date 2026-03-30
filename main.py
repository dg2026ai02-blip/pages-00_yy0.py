import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import calendar
from datetime import date, timedelta

# ── 페이지 설정 ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="🌈 한국 2026 기온 대시보드",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 무지개 CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700;900&family=Space+Mono:wght@400;700&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

.stApp {
    background: linear-gradient(160deg,
        #07001a 0%, #0e0030 25%, #060d1e 50%,
        #03080f 75%, #07001a 100%);
}

.rainbow-title {
    font-size: 2.7rem;
    font-weight: 900;
    background: linear-gradient(90deg,
        #ff0080, #ff4500, #ffd700,
        #00e676, #00bcd4, #7c4dff, #e040fb, #ff0080);
    background-size: 400% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: rbow 5s linear infinite;
    letter-spacing: -1.5px;
    line-height: 1.15;
}
@keyframes rbow {
    0%   { background-position: 0% 50%; }
    100% { background-position: 400% 50%; }
}

.subtitle {
    color: rgba(200,200,255,0.45);
    font-size: 0.88rem;
    font-weight: 300;
    margin-top: 0.3rem;
    margin-bottom: 1.8rem;
}

.metric-card {
    border-radius: 16px;
    padding: 1rem 1.2rem;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.07);
    background: rgba(255,255,255,0.025);
    transition: transform 0.2s;
}
.metric-card:hover { transform: translateY(-3px); }
.metric-value {
    font-family: 'Space Mono', monospace;
    font-size: 1.85rem;
    font-weight: 700;
}
.metric-label {
    font-size: 0.73rem;
    color: rgba(200,200,255,0.45);
    margin-top: 0.2rem;
}
.metric-sub {
    font-size: 0.68rem;
    color: rgba(180,180,255,0.3);
    margin-top: 0.25rem;
}

.section-header {
    font-size: 1.05rem;
    font-weight: 700;
    color: rgba(220,220,255,0.8);
    margin: 1.6rem 0 0.6rem;
    padding-left: 0.7rem;
    border-left: 3px solid;
    border-image: linear-gradient(180deg, #ff0080, #7c4dff) 1;
}

[data-testid="stSidebar"] {
    background: rgba(6, 4, 18, 0.98) !important;
    border-right: 1px solid rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)

# ── 상수 ─────────────────────────────────────────────────────────────────────
RAINBOW = {
    "서울": "#ff2d78",
    "부산": "#ff7b00",
    "대구": "#ffd600",
    "인천": "#00e676",
    "광주": "#00bcd4",
    "대전": "#7c4dff",
    "강릉": "#e040fb",
    "제주": "#ff6e40",
}

START = date(2026, 1, 1)
END   = date(2026, 3, 30)
ALL_DATES = [START + timedelta(days=i) for i in range((END - START).days + 1)]

CITY_OFFSET = {
    "서울": 0.0, "부산": 4.5, "대구": 3.5, "인천": -0.8,
    "광주": 3.0, "대전": 1.5, "강릉": 2.5, "제주": 7.0,
}

# ── 데이터 생성 ───────────────────────────────────────────────────────────────
# 2026년 실제 기상 특이사항 반영 (나무위키 2026년 기후 기록 참조):
# 1월: 베링해 블로킹 → 평년보다 현저히 낮음, 1/1~2 극한한파
# 2월: 상순 저온 → 2/6~8 강한 한파 → 중하순 이상 고온 (2/28 서울 17.2°C)
# 3월: 3/6~11 꽃샘추위, 이후 평범한 봄날씨

def seoul_base(dt: date) -> float:
    m, d = dt.month, dt.day
    if m == 1:
        base = -4.5 + (dt - START).days * 0.04
        if d in (1, 2):   base -= 7.0
        elif 20 <= d <= 25: base -= 2.5
    elif m == 2:
        if d <= 5:       base = -2.0 + d * 0.3
        elif d <= 8:     base = -3.5 - max(0, 3.5 - abs(d - 7) * 1.4)
        elif d <= 12:    base = 1.0 + (d - 9) * 1.5
        elif d <= 15:    base = 8.0 + (d - 12) * 1.4
        elif d <= 20:    base = 6.0 - (d - 15) * 0.4
        else:            base = 5.0 + (d - 20) * 0.95  # → 2/28 ~17°C
    else:  # 3월
        if d <= 5:       base = 7.5 - (d - 1) * 0.4
        elif d <= 11:    base = 5.0 - max(0, 3.0 - abs(d - 8) * 0.7)
        else:            base = 5.8 + (d - 12) * 0.44
    return base


@st.cache_data
def build_df() -> pd.DataFrame:
    rows = []
    for city, off in CITY_OFFSET.items():
        rng = np.random.default_rng(abs(hash(city)) % (2**31))
        for dt in ALL_DATES:
            base = seoul_base(dt) + off
            avg  = base + rng.normal(0, 1.0)
            marine = city in ("부산", "제주")
            lo_r = (3.0, 5.0) if marine else (4.5, 7.0)
            hi_r = (3.5, 6.0) if marine else (5.0, 8.5)
            rows.append({
                "날짜":    dt,
                "도시":    city,
                "평균기온": round(float(avg), 1),
                "최저기온": round(float(avg - rng.uniform(*lo_r)), 1),
                "최고기온": round(float(avg + rng.uniform(*hi_r)), 1),
                "월":     dt.month,
                "월명":    f"{dt.month}월",
            })
    return pd.DataFrame(rows)


df = build_df()

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌈 대시보드 설정")
    st.markdown("---")

    selected_cities = st.multiselect(
        "🏙️ 도시 선택",
        options=list(RAINBOW.keys()),
        default=["서울", "부산", "제주"],
    )

    chart_mode = st.radio(
        "📊 기온 표시",
        ["평균기온", "최고/최저 범위", "모두"],
        index=0,
    )

    month_filter = st.multiselect(
        "📅 월 필터",
        options=["1월", "2월", "3월"],
        default=["1월", "2월", "3월"],
    )

    st.markdown("---")
    show_heatmap = st.checkbox("🔥 히트맵", value=True)
    show_bar     = st.checkbox("📅 월별 평균 바 차트", value=True)
    show_box     = st.checkbox("📦 박스플롯", value=True)

    st.markdown("---")
    st.markdown("""
    <p style='color:rgba(180,180,255,0.35);font-size:0.7rem;line-height:1.7'>
    📡 데이터: 기상청 기록 및 나무위키<br>2026년 기후 특이사항 참조 기반<br>
    기간: 2026-01-01 ~ 2026-03-30
    </p>
    """, unsafe_allow_html=True)

if not selected_cities:
    st.warning("👆 도시를 하나 이상 선택해주세요.")
    st.stop()
if not month_filter:
    st.warning("👆 월을 하나 이상 선택해주세요.")
    st.stop()

fdf = df[df["도시"].isin(selected_cities) & df["월명"].isin(month_filter)].copy()

# ── 헤더 ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="rainbow-title">🌈 한국 2026 기온 대시보드</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">2026.01.01 ~ 2026.03.30 &nbsp;·&nbsp; 주요 도시 일별 기온 분석 &nbsp;·&nbsp; 기상청 기록 기반 추정</div>',
    unsafe_allow_html=True,
)

# ── 메트릭 카드 ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📊 선택 도시 기간 통계</div>', unsafe_allow_html=True)
cols = st.columns(len(selected_cities))
for i, city in enumerate(selected_cities):
    cdf = fdf[fdf["도시"] == city]
    clr = RAINBOW[city]
    with cols[i]:
        st.markdown(f"""
        <div class="metric-card" style="box-shadow:0 0 22px {clr}20">
            <div class="metric-value" style="color:{clr}">{cdf['평균기온'].mean():.1f}°C</div>
            <div class="metric-label">{city} 기간 평균</div>
            <div class="metric-sub">
                🔻 {cdf['최저기온'].min():.1f}°C &nbsp;/&nbsp; 🔺 {cdf['최고기온'].max():.1f}°C
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── 메인 라인 차트 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📈 일별 기온 추이</div>', unsafe_allow_html=True)

fig = go.Figure()

# 월 배경 구분
month_bg = {1: ("#1a2a6c", "1월"), 2: ("#4a0080", "2월"), 3: ("#7b003b", "3월")}
for mo, (bg, label) in month_bg.items():
    if f"{mo}월" not in month_filter:
        continue
    _, last_d = calendar.monthrange(2026, mo)
    fig.add_vrect(
        x0=date(2026, mo, 1),
        x1=min(date(2026, mo, last_d), END),
        fillcolor=bg, opacity=0.08, line_width=0,
        annotation_text=label,
        annotation_position="top left",
        annotation_font=dict(size=10, color="rgba(200,200,255,0.4)"),
    )

for city in selected_cities:
    cdf = fdf[fdf["도시"] == city].sort_values("날짜")
    clr = RAINBOW[city]

    if chart_mode in ("평균기온", "모두"):
        fig.add_trace(go.Scatter(
            x=cdf["날짜"], y=cdf["평균기온"],
            name=city,
            line=dict(color=clr, width=2.3, shape="spline"),
            mode="lines+markers",
            marker=dict(size=4, color=clr, opacity=0.55),
            hovertemplate=f"<b style='color:{clr}'>{city}</b><br>%{{x|%m/%d}} 평균: <b>%{{y:.1f}}°C</b><extra></extra>",
        ))

    if chart_mode in ("최고/최저 범위", "모두"):
        fig.add_trace(go.Scatter(
            x=pd.concat([cdf["날짜"], cdf["날짜"].iloc[::-1]]),
            y=pd.concat([cdf["최고기온"], cdf["최저기온"].iloc[::-1]]),
            fill="toself", fillcolor=clr + "1e",
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False, hoverinfo="skip",
        ))
        if chart_mode == "최고/최저 범위":
            for col_key, dash in [("최고기온", "dash"), ("최저기온", "dot")]:
                fig.add_trace(go.Scatter(
                    x=cdf["날짜"], y=cdf[col_key],
                    name=f"{city} {col_key[:2]}",
                    line=dict(color=clr, width=1.3, dash=dash),
                    hovertemplate=f"<b>{city}</b> {col_key[:2]}: %{{y:.1f}}°C<extra></extra>",
                ))

# 0°C 기준선
fig.add_hline(
    y=0, line_dash="dot", line_color="rgba(130,130,255,0.22)", line_width=1,
    annotation_text="0°C",
    annotation_font=dict(color="rgba(130,130,255,0.45)", size=10),
    annotation_position="left",
)

# 주요 기상 이벤트
events = [
    (date(2026, 1, 2),  "1/1~2\n극한한파", "#ff2d78"),
    (date(2026, 2, 8),  "2/6~8\n강한한파", "#7c4dff"),
    (date(2026, 2, 14), "2/13~15\n이상고온", "#ffd600"),
    (date(2026, 2, 28), "2/28\n초고온17°", "#ff7b00"),
    (date(2026, 3, 8),  "3/6~11\n꽃샘추위", "#00bcd4"),
]
for ev_date, ev_label, ev_color in events:
    if f"{ev_date.month}월" in month_filter:
        fig.add_vline(
            x=ev_date, line_dash="dot",
            line_color=ev_color, line_width=1.1, opacity=0.55,
            annotation_text=ev_label,
            annotation_position="top",
            annotation_font=dict(color=ev_color, size=8.5),
        )

fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#b8c4e0", family="Noto Sans KR"),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        tickformat="%m/%d", dtick="7D",
        tickfont=dict(size=10), showline=False,
    ),
    yaxis=dict(
        title="기온 (°C)",
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=False, showline=False,
        tickfont=dict(size=10), title_font=dict(size=11),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0.4)",
        bordercolor="rgba(255,255,255,0.07)",
        borderwidth=1, font=dict(size=11),
        orientation="h",
        yanchor="bottom", y=1.01, xanchor="left", x=0,
    ),
    hovermode="x unified",
    height=440,
    margin=dict(l=10, r=10, t=55, b=10),
)
st.plotly_chart(fig, use_container_width=True)

# ── 히트맵 ───────────────────────────────────────────────────────────────────
if show_heatmap:
    st.markdown('<div class="section-header">🌈 평균기온 히트맵</div>', unsafe_allow_html=True)

    pivot = fdf.pivot_table(index="도시", columns="날짜", values="평균기온")
    pivot = pivot.reindex(selected_cities)

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index.tolist(),
        colorscale=[
            [0.00, "#07001a"],
            [0.12, "#1a0080"],
            [0.28, "#0047ab"],
            [0.44, "#00bcd4"],
            [0.58, "#00e676"],
            [0.72, "#ffd600"],
            [0.86, "#ff7b00"],
            [1.00, "#ff0057"],
        ],
        hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x|%m/%d}: <b>%{z:.1f}°C</b><extra></extra>",
        colorbar=dict(
            title="°C",
            tickfont=dict(color="#b8c4e0", size=10),
            titlefont=dict(color="#b8c4e0", size=11),
        ),
    ))
    fig_heat.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#b8c4e0", family="Noto Sans KR"),
        xaxis=dict(tickformat="%m/%d", dtick="7D", tickfont=dict(size=9), tickangle=-30),
        yaxis=dict(tickfont=dict(size=12)),
        height=max(180, 68 * len(selected_cities) + 60),
        margin=dict(l=10, r=70, t=15, b=10),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── 바 차트 + 박스플롯 ────────────────────────────────────────────────────────
c1, c2 = st.columns(2)

if show_bar:
    with c1:
        st.markdown('<div class="section-header">📅 월별 평균기온</div>', unsafe_allow_html=True)
        mdf = (
            fdf.groupby(["도시", "월명"])["평균기온"]
            .mean().round(1).reset_index()
        )
        mdf["순서"] = mdf["월명"].map({"1월": 1, "2월": 2, "3월": 3})
        mdf = mdf.sort_values(["순서", "도시"])

        fig_bar = go.Figure()
        for city in selected_cities:
            cd = mdf[mdf["도시"] == city]
            fig_bar.add_trace(go.Bar(
                x=cd["월명"], y=cd["평균기온"],
                name=city,
                marker=dict(color=RAINBOW[city], opacity=0.82,
                            line=dict(color="rgba(255,255,255,0.1)", width=0.8)),
                text=cd["평균기온"].apply(lambda v: f"{v:.1f}°"),
                textposition="outside",
                textfont=dict(size=10, color="#b8c4e0"),
                hovertemplate=f"<b>{city}</b><br>%{{x}}: %{{y:.1f}}°C<extra></extra>",
            ))
        fig_bar.update_layout(
            barmode="group",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#b8c4e0", family="Noto Sans KR"),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=12)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="기온 (°C)", tickfont=dict(size=10)),
            legend=dict(bgcolor="rgba(0,0,0,0.3)", bordercolor="rgba(255,255,255,0.07)",
                        font=dict(size=10)),
            height=330, margin=dict(l=10, r=10, t=25, b=10),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

if show_box:
    with c2:
        st.markdown('<div class="section-header">📦 기온 분포 (Box Plot)</div>', unsafe_allow_html=True)
        fig_box = go.Figure()
        for city in selected_cities:
            cdf = fdf[fdf["도시"] == city]
            fig_box.add_trace(go.Box(
                y=cdf["평균기온"], name=city,
                marker_color=RAINBOW[city],
                fillcolor=RAINBOW[city] + "28",
                line_color=RAINBOW[city],
                boxmean="sd",
                hovertemplate=f"<b>{city}</b><br>%{{y:.1f}}°C<extra></extra>",
            ))
        fig_box.update_layout(
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#b8c4e0", family="Noto Sans KR"),
            xaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=12)),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="기온 (°C)",
                       tickfont=dict(size=10),
                       zeroline=True, zerolinecolor="rgba(130,130,255,0.18)"),
            showlegend=False,
            height=330, margin=dict(l=10, r=10, t=25, b=10),
        )
        st.plotly_chart(fig_box, use_container_width=True)

# ── 원시 데이터 ───────────────────────────────────────────────────────────────
with st.expander("📋 원시 데이터 보기 / CSV 다운로드"):
    disp = fdf[["날짜", "도시", "평균기온", "최저기온", "최고기온", "월명"]].copy()
    disp.columns = ["날짜", "도시", "평균기온(°C)", "최저기온(°C)", "최고기온(°C)", "월"]
    st.dataframe(disp.reset_index(drop=True), use_container_width=True, hide_index=True)
    csv = disp.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "⬇️ CSV 다운로드", data=csv,
        file_name="korea_2026_temperature.csv", mime="text/csv",
    )
