import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# --- 설정 ---
st.set_page_config(page_title="서울 지하철 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

# 날짜 계산 (기본값을 2024년 10월이나 11월로 설정해보세요 - 확실히 데이터가 있는 달)
today = datetime.now()
# 안전하게 2개월 전 데이터를 기본값으로 설정 (데이터 누락 방지)
safe_month = (today.replace(day=1) - timedelta(days=60)).strftime("%Y%m")

st.title("⏰ 서울 지하철 이용 분석 대시보드")

st.sidebar.header("📡 데이터 조회")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value=safe_month)
st.sidebar.info("💡 데이터가 안 나오면 한 달 전(예: 202410)으로 입력해보세요.")

@st.cache_data(ttl=3600)
def load_subway_api(api_key, month):
    # 한 번에 1000건 호출
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        
        # 1. 정상 데이터인 경우
        if "CardSubwayTime" in data:
            return pd.DataFrame(data["CardSubwayTime"]["row"]), None
        
        # 2. API 자체 에러인 경우 (인증키 오류, 데이터 없음 등)
        elif "RESULT" in data:
            return None, data["RESULT"]["MESSAGE"]
        
        # 3. 기타 에러
        elif "INFO-200" in str(data): # 데이터 없음 코드
            return None, "해당 월의 데이터가 아직 등록되지 않았습니다."
            
        return None, "알 수 없는 응답 구조입니다."
    except Exception as e:
        return None, f"네트워크 오류: {str(e)}"

# 데이터 로드 시도
df, error_msg = load_subway_api(API_KEY, target_month)

if df is not None:
    # 데이터가 정상적으로 왔을 때만 실행
    st.success(f"✅ {target_month} 데이터를 성공적으로 불러왔습니다.")
    
    # 숫자 변환
    num_cols = [col for col in df.columns if "_NUM" in col]
    df[num_cols] = df[num_cols].apply(pd.to_numeric)

    # 호선 선택
    lines = sorted(df["LINE_NUM"].unique())
    selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
    line_df = df[df["LINE_NUM"] == selected_line]

    # 시각화 데이터 가공 (단순화 버전)
    ride_cols = [col for col in df.columns if "_RIDE_NUM" in col]
    # 시간대 추출 (예: SEVEN_RIDE_NUM -> 07시)
    avg_data = line_df[ride_cols].mean().reset_index()
    avg_data.columns = ['시간대', '평균 승차인원']
    
    # 그래프
    fig = px.bar(avg_data, x='시간대', y='평균 승차인원', 
                 title=f"{selected_line} 시간대별 승차 현황",
                 color='평균 승차인원', color_continuous_scale='Blues')
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("📋 데이터 미리보기")
    st.dataframe(line_df.head())

else:
    # 에러 메시지 출력
    st.error(f"❌ 데이터를 불러올 수 없습니다: {error_msg}")
    st.warning("팁: 조회 월을 202410 또는 202409로 변경해서 테스트해보세요.")
