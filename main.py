import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- 1. 설정 및 인증키 ---
st.set_page_config(page_title="서울 지하철 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 서울 지하철 API 분석 (에러 방지 버전)")

# 사이드바 설정 - 안전하게 2024년 10월을 기본값으로 사용
st.sidebar.header("📡 데이터 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202410")

# --- 2. 데이터 로딩 함수 (안전장치 추가) ---
@st.cache_data(ttl=3600)
def load_subway_data(api_key, month):
    # 1~1000번 데이터 호출
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        
        # 🟢 정상 데이터인 경우
        if "CardSubwayTime" in data:
            return pd.DataFrame(data["CardSubwayTime"]["row"]), "SUCCESS"
        
        # 🟡 API 서버에서 보낸 에러 메시지인 경우
        elif "RESULT" in data:
            return None, data["RESULT"]["MESSAGE"]
        
        return None, "알 수 없는 응답 구조"
    except Exception as e:
        return None, str(e)

# 데이터 실행
df_raw, status = load_subway_data(API_KEY, target_month)

# --- 3. 에러 방지 체크 ---
if df_raw is not None:
    # 🔍 컬럼명이 있는지 확인하고 진행
    if "LINE_NUM" in df_raw.columns:
        st.success(f"✅ {target_month} 데이터를 불러왔습니다.")
        
        # 숫자 변환
        num_cols = [col for col in df_raw.columns if "_NUM" in col]
        df_raw[num_cols] = df_raw[num_cols].apply(pd.to_numeric)

        # 호선 선택
        lines = sorted(df_raw["LINE_NUM"].unique())
        selected_line = st.sidebar.selectbox("호선 선택", lines)
        line_df = df_raw[df_raw["LINE_NUM"] == selected_line]

        # --- 4. 시각화 (간략화) ---
        ride_cols = [col for col in df_raw.columns if "_RIDE_NUM" in col]
        avg_data = line_df[ride_cols].mean().reset_index()
        avg_data.columns = ['시간대', '인원']
        
        fig = px.bar(avg_data, x='시간대', y='인원', title=f"{selected_line} 평균 승차")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("데이터 구조에 'LINE_NUM'이 없습니다. 관리자에게 문의하세요.")
else:
    # ❌ 데이터가 없을 때 메시지 출력
    st.error(f"❌ 데이터를 가져오지 못했습니다: {status}")
    st.warning("💡 원인: 조회하신 월의 데이터가 아직 서울시 서버에 업로드되지 않았을 가능성이 큽니다.")
    st.info("해결책: 왼쪽 사이드바에서 날짜를 **202410**으로 입력해 보세요.")
