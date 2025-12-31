import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 지하철 실시간 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 서울 지하철 최신 데이터 자동 분석기")

# --- 1. 최신 데이터가 있는 달 자동 찾기 (지능형 로직) ---
@st.cache_data(ttl=3600)
def fetch_latest_valid_data(api_key):
    current_date = datetime.now()
    # 최근 6개월간 역순으로 뒤져보며 데이터가 있는 달을 찾습니다.
    for i in range(1, 7):
        target_month = (current_date.replace(day=1) - timedelta(days=i*28)).strftime("%Y%m")
        url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{target_month}"
        
        try:
            res = requests.get(url)
            data = res.json()
            if "CardSubwayTime" in data:
                df = pd.DataFrame(data["CardSubwayTime"]["row"])
                return df, target_month
        except:
            continue
    return None, None

with st.spinner('가장 최신 지하철 데이터를 찾는 중입니다...'):
    df, found_month = fetch_latest_valid_data(API_KEY)

# --- 2. 데이터 분석 및 시각화 ---
if df is not None:
    # 모든 컬럼명을 대문자로 통일
    df.columns = [c.upper() for c in df.columns]
    
    st.success(f"✨ 현재 조회 가능한 가장 최신 달: **{found_month}**")

    # [지능형] 호선 정보를 담은 컬럼 찾기 (LINE_NUM이 없어도 됨)
    line_col = next((c for c in df.columns if "LINE" in c or "호선" in c), None)
    
    if line_col:
        lines = sorted(df[line_col].unique())
        selected_line = st.sidebar.selectbox("🚇 분석할 호선 선택", lines)
        line_df = df[df[line_col] == selected_line].copy()

        # 숫자 데이터로 변환
        num_cols = [c for c in df.columns if "NUM" in c or "CNT" in c]
        line_df[num_cols] = line_df[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # 시간대별 승차 데이터 추출
        ride_cols = [c for c in num_cols if "RIDE" in c]
        avg_ride = line_df[ride_cols].mean().reset_index()
        avg_ride.columns = ['시간대', '평균승차']

        # 그래프 시각화
        st.subheader(f"📊 {selected_line} 시간대별 이용객 현황")
        fig = px.bar(avg_ride, x='시간대', y='평균승차', 
                     color='평균승차', color_continuous_scale='Sunsetdark',
                     labels={'평균승차': '평균 이용객 (명)'})
        st.plotly_chart(fig, use_container_width=True)

        # 핵심 지표
        c1, c2 = st.columns(2)
        c1.metric("🚉 분석된 역 개수", f"{len(line_df)}개")
        peak_time = avg_ride.loc[avg_ride['평균승차'].idxmax(), '시간대']
        c2.metric("⏰ 가장 붐비는 시간", peak_time.split('_')[0] + "시")

    else:
        st.warning("호선 정보를 찾을 수 없어 전체 데이터를 보여드립니다.")
        st.dataframe(df)
else:
    st.error("최근 6개월 내에 조회 가능한 지하철 데이터가 없습니다. API 키나 서버 상태를 확인해주세요.")

# 하단 데이터 미리보기
if df is not None:
    with st.expander("📄 전체 데이터 원본 확인"):
        st.dataframe(df)
