import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import datetime

# 🎨 1. 앱 디자인 설정 (하얀 배경, 핑크 톤)
st.set_page_config(page_title="💖 2026 기온 요정의 일기장", page_icon="🌸", layout="wide")

# 귀여운 핑크색 CSS 스타일 주입
st.markdown("""
<style>
    .stApp { background-color: white; } /* 배경 하얗게 */
    h1, h2, h3 { color: #ff69b4 !important; font-family: 'Malgun Gothic', sans-serif; } /* 제목 분홍색 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem; /* 탭 글씨 크기 키우기 */
    }
    div.stButton > button { background-color: #ff69b4; color: white; border-radius: 20px; border: none; }
    div.stButton > button:hover { background-color: #ff1493; color: white; }
</style>
""", unsafe_allow_html=True)

# 📊 2. 데이터 생성 (2026년 1월 1일 ~ 3월 30일 서울 가상 데이터)
@st.cache_data # 데이터를 매번 다시 만들지 않게 저장해두는 마법!
def load_data():
    start_date = datetime.date(2026, 1, 1)
    end_date = datetime.date(2026, 3, 30)
    dates = pd.date_range(start_date, end_date)
    
    # 가상 기온 데이터 생성
    np.random.seed(42)
    temp_base = np.linspace(-5, 12, len(dates))
    temp_variation = np.random.normal(0, 3, len(dates))
    avg_temps = temp_base + temp_variation
    max_temps = avg_temps + np.random.uniform(3, 8, len(dates))
    min_temps = avg_temps - np.random.uniform(3, 8, len(dates))
    
    df = pd.DataFrame({
        '날짜': dates,
        '최고 기온 (°C)': max_temps.round(1),
        '최저 기온 (°C)': min_temps.round(1),
        '평균 기온 (°C)': avg_temps.round(1)
    })
    return df

df = load_data()

# 🎀 3. 메인 화면 인사말
st.title("💖 2026 기온 요정의 일기장 (서울) 🌸")
st.write("안녕! 폴더 없이 파일 하나로 아주 쉽게 만들었어! 아래 버튼을 눌러서 원하는 걸 확인해 봐! ✨🐰")
st.markdown("---")

# 🌈 4. 탭(Tab)으로 화면 나누기 (멀티 페이지 대신 사용!)
tab1, tab2 = st.tabs(["🌈 무지개 차트 보기", "📊 상세 데이터 보기"])

# --- 첫 번째 탭: 무지개 차트 ---
with tab1:
    st.subheader("🌈 1월 1일부터 오늘까지의 기온 변화야!")
    
    # Plotly 무지개 선 그래프 그리기
    fig = px.line(df, x='날짜', y=['최고 기온 (°C)', '최저 기온 (°C)', '평균 기온 (°C)'],
                 color_discrete_sequence=['#FF69B4', '#87CEFA', '#98FB98']) # 무지개색 설정
    
    fig.update_layout(
        plot_bgcolor='white', paper_bgcolor='white', # 차트 배경도 하얗게
        hovermode='x unified', title_font_color='#ff1493'
    )
    fig.update_traces(mode="lines+markers", marker_symbol="star", marker_size=5) # 귀여운 별 모양 마커
    
    st.plotly_chart(fig, use_container_width=True)

# --- 두 번째 탭: 데이터 표 ---
with tab2:
    st.subheader("📊 요정의 꼼꼼한 상세 기록 표")
    st.write("숫자로 정확하게 보고 싶다면 여기를 봐! 다운로드도 할 수 있어. ⬇️")
    
    # 표 보여주기
    st.dataframe(df, use_container_width=True)
    
    # 다운로드 버튼
    csv = df.to_csv(index=False).encode('utf-8-sig') # 한글 안 깨지게!
    st.download_button(
        label="💖 요정의 일기장 다운로드 ⬇️",
        data=csv,
        file_name='fairy_temperature_2026.csv',
        mime='text/csv'
    )
