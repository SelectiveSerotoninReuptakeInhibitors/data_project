import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# --- 0. 최신 월 자동 계산 ---
# 데이터는 보통 전달(1개월 전)에 확정되므로 안전하게 전달 날짜를 기본값으로 설정합니다.
today = datetime.now()
first_day_of_this_month = today.replace(day=1)
last_month_date = first_day_of_this_month - timedelta(days=1)
default_month = last_month_date.strftime("%Y%m") # 예: 202411

st.set_page_config(page_title="서울 지하철 실시간 분석", layout="wide")
st.title("⏰ 서울 지하철 최신 이용 분석 대시보드")

# --- 1. API 설정 및 데이터 로드 ---
API_KEY = "인증키번호" 

st.sidebar.header("📡 데이터 설정")
# 최신 월이 자동으로 입력되도록 변경
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value=default_month)

# 페이지가 열리자마자 바로 데이터를 불러오고 싶다면 button 없이 바로 실행 가능하지만, 
# API 트래픽 관리를 위해 버튼 클릭 방식을 유지하거나 '자동 로드' 옵션을 추가할 수 있습니다.
if st.sidebar.button("최신 데이터 새로고침"):
    st.cache_data.clear() # 캐시 삭제 후 새로고침

# 데이터 로딩 함수 (캐싱 적용으로 속도 향상)
@st.cache_data
def fetch_subway_data(api_key, month):
    # 1번부터 1000번까지 데이터 호출
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        if "CardSubwayTime" in data:
            return pd.DataFrame(data["CardSubwayTime"]["row"])
        else:
            return None
    except:
        return None

df = fetch_subway_data(API_KEY, target_month)

# --- 2. 데이터 시각화 (기존 로직 동일) ---
if df is not None:
    st.success(f"✅ {target_month} 데이터 기준 분석 중입니다.")
    
    # 숫자형 변환
    time_cols = [col for col in df.columns if "_NUM" in col]
    df[time_cols] = df[time_cols].apply(pd.to_numeric)
    
    # 호선 선택
    lines = sorted(df["LINE_NUM"].unique())
    selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
    line_df = df[df["LINE_NUM"] == selected_line]

    # 그래프 데이터 가공 및 출력
    # (이후 시각화 코드는 동일하게 유지...)
    # ...
else:
    st.info(f"📅 {target_month} 데이터를 불러오는 중이거나 아직 공공데이터 포털에 업로드되지 않았습니다. 월을 조정해 보세요.")
