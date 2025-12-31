import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta

# --- 1. 설정 및 인증키 ---
st.set_page_config(page_title="서울 지하철 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("⏰ 서울 지하철 이용 분석 대시보드")

# --- 2. 날짜 설정 (데이터가 확실히 있는 달로 초기화) ---
# 2025년 데이터는 아직 포털에 업데이트되지 않았을 확률이 매우 높습니다.
# 안전하게 2024년 10월을 기본값으로 설정합니다.
default_month = "202410"

st.sidebar.header("📡 데이터 조회 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value=default_month)
st.sidebar.info("💡 최신 달(예: 202412)은 아직 집계 중일 수 있습니다. 데이터가 안 나오면 202410으로 바꿔보세요.")

# --- 3. 데이터 로딩 함수 (에러 핸들링 강화) ---
@st.cache_data(ttl=3600)
def load_subway_data(api_key, month):
    # API 요청 주소 (1~1000번 데이터)
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    
    try:
        res = requests.get(url)
        data = res.json()
        
        # 정상적으로 데이터를 받은 경우
        if "CardSubwayTime" in data:
            return pd.DataFrame(data["CardSubwayTime"]["row"]), "SUCCESS"
        
        # API 서버에서 에러 메시지를 보낸 경우 (인증키 오류, 데이터 없음 등)
        elif "RESULT" in data:
            return None, data["RESULT"]["MESSAGE"]
        
        # 기타 알 수 없는 에러
        return None, "알 수 없는 API 응답 형식입니다."
        
    except Exception as e:
        return None, f"네트워크 연결 오류: {str(e)}"

# --- 4. 메인 분석 로직 ---
df, msg = load_subway_data(API_KEY, target_month)

if df is not None:
    # 🔍 데이터가 정상일 때만 실행
    st.success(f"✅ {target_month} 데이터 로드 완료!")
    
    # 숫자형 변환 (에러 방지용)
    num_cols = [col for col in df.columns if "_NUM" in col]
    df[num_cols] = df[num_cols].apply(pd.to_numeric)

    # 호선 선택 (KeyError 방지를 위해 컬럼 존재 확인)
    if "LINE_NUM" in df.columns:
        lines = sorted(df["LINE_NUM"].unique())
        selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
        
        line_df = df[df["LINE_NUM"] == selected_line]
        
        # 간단 시각화
        ride_cols = [col for col in df.columns if "_RIDE_NUM" in col]
        avg_data = line_df[ride_cols].mean().reset_index()
        avg_data.columns = ['시간대', '인원']
        
        st.subheader(f"📈 {selected_line} 시간대별 평균 승차")
        fig = px.bar(avg_data, x='시간대', y='인원', color='인원', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(line_df.head())
    else:
        st.error("데이터 구조에 'LINE_NUM'이 없습니다. API 응답을 확인해야 합니다.")
else:
    # ❌ 에러 발생 시 안내문 출력
    st.error(f"❌ 데이터를 가져올 수 없습니다: {msg}")
    st.warning("팁: 사이드바에서 날짜를 202410 또는 202409로 변경해 보세요.")
    
    # 디버깅을 위해 원본 응답 확인 버튼
    if st.button("실제 API 응답 내용 확인"):
        url_test = f"http://openAPI.seoul.go.kr:8088/{API_KEY}/json/CardSubwayTime/1/5/{target_month}"
        test_res = requests.get(url_test).json()
        st.json(test_res)
