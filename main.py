import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 지하철 분석기", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 최신 데이터 무한 추적 분석기")

# --- 1. 데이터가 나올 때까지 과거로 거슬러 올라가는 함수 ---
@st.cache_data(ttl=3600)
def find_latest_data(api_key):
    # 오늘부터 최대 12개월 전까지 뒤집니다.
    for i in range(1, 13):
        target_date = datetime.now() - timedelta(days=30 * i)
        month_str = target_date.strftime("%Y%m")
        
        # API 주소 (가장 표준적인 형식)
        url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month_str}"
        
        try:
            res = requests.get(url)
            data = res.json()
            
            # 성공적으로 데이터를 찾았을 때만 리턴
            if "CardSubwayTime" in data:
                return pd.DataFrame(data["CardSubwayTime"]["row"]), month_str
        except:
            continue
    return None, None

with st.spinner('서버에서 가장 최신 데이터를 찾는 중...'):
    df, found_month = find_latest_data(API_KEY)

# --- 2. 데이터 분석 ---
if df is not None:
    st.success(f"🎊 드디어 찾았습니다! 현재 조회 가능한 최신 달: **{found_month}**")
    
    # 모든 컬럼명에서 공백을 제거하고 대문자로 변환 (철저하게!)
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    # LINE_NUM이 없으면 '호선명' 또는 첫 번째 컬럼을 강제로 사용
    line_col = "LINE_NUM" if "LINE_NUM" in df.columns else df.columns[1]
    
    if line_col in df.columns:
        lines = sorted(df[line_col].unique())
        selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
        line_df = df[df[line_col] == selected_line]

        # 숫자 변환
        num_cols = [c for c in df.columns if "NUM" in c]
        line_df[num_cols] = line_df[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # 시간대별 승차 차트 가공
        ride_cols = [c for c in num_cols if "RIDE" in c]
        avg_ride = line_df[ride_cols].mean().reset_index()
        avg_ride.columns = ['시간대', '인원']
        
        # 차트 출력
        st.subheader(f"📊 {selected_line} 시간대별 이용객 (평균)")
        fig = px.line(avg_ride, x='시간대', y='인원', markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(line_df.head())
    else:
        st.error("데이터 형태가 평소와 다릅니다. 아래 원본을 확인해주세요.")
        st.write(df)
else:
    st.error("❌ 모든 시도 실패: 데이터가 하나도 없습니다. API 키를 다시 확인해주세요.")
    st.write(f"현재 시도한 키: {API_KEY}")
