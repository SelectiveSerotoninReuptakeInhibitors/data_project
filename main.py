import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# --- 설정 ---
st.set_page_config(page_title="서울 지하철 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

# 기본 날짜를 안전하게 3개월 전으로 설정 (최신 데이터 부재 대비)
today = datetime.now()
default_month = (today.replace(day=1) - timedelta(days=90)).strftime("%Y%m")

st.title("⏰ 서울 지하철 이용 분석 대시보드")

st.sidebar.header("📡 데이터 조회 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value=default_month)
st.sidebar.info("💡 데이터가 안 나오면 202410이나 202409로 테스트해보세요.")

@st.cache_data(ttl=3600)
def load_subway_api(api_key, month):
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        
        # 1.정상 데이터가 온 경우
        if "CardSubwayTime" in data:
            return pd.DataFrame(data["CardSubwayTime"]["row"]), None
        
        # 2. API는 성공했지만 결과가 없는 경우 (RESULT 키 확인)
        elif "RESULT" in data:
            return None, f"API 메시지: {data['RESULT']['MESSAGE']} ({data['RESULT']['CODE']})"
        
        # 3. 기타 에러
        return None, "알 수 없는 응답 형식입니다."
    except Exception as e:
        return None, f"연결 오류: {str(e)}"

# 데이터 로드
df, error_msg = load_subway_api(API_KEY, target_month)

# --- 메인 로직 ---
if df is not None:
    # 1. 컬럼명 확인 후 데이터 타입 변환
    if "LINE_NUM" in df.columns:
        num_cols = [col for col in df.columns if "_NUM" in col]
        df[num_cols] = df[num_cols].apply(pd.to_numeric)

        # 2. 호선 선택
        lines = sorted(df["LINE_NUM"].unique())
        selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
        line_df = df[df["LINE_NUM"] == selected_line]

        # 3. 그래프 그리기 (간단 버전)
        ride_cols = [col for col in df.columns if "_RIDE_NUM" in col]
        avg_data = line_df[ride_cols].mean().reset_index()
        avg_data.columns = ['시간대', '인원']
        
        st.subheader(f"📈 {selected_line} 시간대별 평균 이용객")
        fig = px.bar(avg_data, x='시간대', y='인원', color='인원',
                     color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(line_df.head())
    else:
        st.error("불러온 데이터에 'LINE_NUM' 컬럼이 없습니다.")
        st.write("실제 데이터 구조:", df)
else:
    # 에러 메시지 상세 출력
    st.error(f"❌ 데이터를 불러올 수 없습니다.")
    st.warning(error_msg)
    st.info("Tip: 보통 최신 달은 집계 중이라 안 나올 수 있습니다. 날짜를 한두 달 전으로 바꿔보세요.")
