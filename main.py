import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# --- 설정 ---
st.set_page_config(page_title="서울 지하철 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

# 날짜 계산 (전월 기준)
today = datetime.now()
default_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y%m")

st.title("⏰ 서울 지하철 이용 분석 대시보드")

target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value=default_month)

@st.cache_data(ttl=3600)
def load_subway_api(api_key, month):
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        
        # API 응답 성공 여부 확인
        if "CardSubwayTime" in data:
            return pd.DataFrame(data["CardSubwayTime"]["row"])
        elif "RESULT" in data:
            st.error(f"API 에러 발생: {data['RESULT']['MESSAGE']}")
            return None
        else:
            st.warning("예상치 못한 데이터 구조입니다.")
            st.write(data) # 디버깅용 출력
            return None
    except Exception as e:
        st.error(f"네트워크 오류: {e}")
        return None

df = load_subway_api(API_KEY, target_month)

# --- 에러 방지 체크 ---
if df is not None:
    # 컬럼 존재 여부 확인
    if "LINE_NUM" in df.columns:
        # 데이터 타입 변환
        num_cols = [col for col in df.columns if "_NUM" in col]
        df[num_cols] = df[num_cols].apply(pd.to_numeric)

        # 분석 로직 시작
        lines = sorted(df["LINE_NUM"].unique())
        selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
        
        line_df = df[df["LINE_NUM"] == selected_line]
        
        # (시각화 로직...)
        st.success(f"✅ {selected_line} 데이터를 성공적으로 불러왔습니다.")
        st.dataframe(line_df.head())
        
        # 간단한 그래프 예시
        ride_cols = [col for col in df.columns if "_RIDE_NUM" in col]
        avg_data = line_df[ride_cols].mean().reset_index()
        avg_data.columns = ['시간대', '인원']
        fig = px.bar(avg_data, x='시간대', y='인원', title="시간대별 평균 승차")
        st.plotly_chart(fig)
        
    else:
        st.error("데이터에 'LINE_NUM' 컬럼이 없습니다. API 응답 결과를 확인하세요.")
        st.write("불러온 컬럼명 목록:", df.columns.tolist())
else:
    st.info("데이터를 불러오는 중입니다. 잠시만 기다려주세요.")
