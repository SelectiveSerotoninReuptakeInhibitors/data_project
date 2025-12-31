import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 설정 ---
st.set_page_config(page_title="서울 지하철 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

# 데이터가 확실히 존재하는 2024년 10월을 기본값으로 설정해봅니다.
default_month = "202410"

st.title("⏰ 서울 지하철 이용 분석 대시보드")

st.sidebar.header("📡 데이터 조회 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value=default_month)

@st.cache_data(ttl=3600)
def load_subway_api(api_key, month):
    # 테스트를 위해 10건만 먼저 가져와봅니다.
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/10/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        return data
    except Exception as e:
        return {"error": str(e)}

# API 호출
result = load_subway_api(API_KEY, target_month)

# --- 결과 분석 및 출력 ---
if "CardSubwayTime" in result:
    # 정상 데이터인 경우
    df = pd.DataFrame(result["CardSubwayTime"]["row"])
    st.success(f"✅ {target_month} 데이터 로드 성공!")
    
    # 여기서부터 기존 분석 로직 시작
    lines = sorted(df["LINE_NUM"].unique())
    selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
    st.dataframe(df[df["LINE_NUM"] == selected_line])

elif "RESULT" in result:
    # API 서버에서 보내는 에러 메시지 (데이터 없음, 키 오류 등)
    st.error(f"❌ API 서버 메시지: {result['RESULT']['MESSAGE']}")
    st.info(f"에러 코드: {result['RESULT']['CODE']}")
    
    if result['RESULT']['CODE'] == "INFO-200":
        st.warning("💡 아직 해당 월의 데이터가 집계되지 않았습니다. 사이드바에서 '202410'으로 바꿔보세요.")
    elif result['RESULT']['CODE'] == "INFO-300":
        st.warning("💡 인증키가 틀렸거나 활성화되지 않았습니다.")

else:
    # 예상치 못한 응답
    st.error("알 수 없는 오류가 발생했습니다.")
    st.write("서버 응답 내용:", result)
