import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="서울 지하철 끝장 대시보드", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 이번엔 진짜 나옵니다! 지하철 API 분석")

# 1. 사이드바 설정 (무조건 데이터가 있는 2024년 05월로 고정해서 테스트해봅시다)
st.sidebar.header("📡 데이터 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202405")

# 2. 데이터 로드 함수
@st.cache_data(ttl=3600)
def load_emergency_data(api_key, month):
    # API 주소 형식을 가장 기본형으로 바꿨습니다.
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/500/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        return data
    except Exception as e:
        return {"error": str(e)}

# 실행
result = load_emergency_data(API_KEY, target_month)

# 3. 데이터 구조 강제 분석
if "CardSubwayTime" in result:
    df = pd.DataFrame(result["CardSubwayTime"]["row"])
    st.success(f"✅ {target_month} 데이터 수신 성공!")
    
    # [핵심] 컬럼명을 가리지 않고 무조건 보여줍니다.
    st.write("### 🔍 현재 데이터에 들어있는 컬럼들:")
    st.code(list(df.columns))

    # 호선 컬럼 찾기 (대소문자 무시)
    line_col = None
    for c in df.columns:
        if "LINE" in c.upper() or "호선" in c:
            line_col = c
            break

    if line_col:
        lines = sorted(df[line_col].unique())
        selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
        line_df = df[df[line_col] == selected_line]

        # 숫자 변환
        num_cols = [c for c in df.columns if "NUM" in c.upper() or "CNT" in c.upper()]
        line_df[num_cols] = line_df[num_cols].apply(pd.to_numeric, errors='coerce')

        # 승차 그래프
        ride_cols = [c for c in num_cols if "RIDE" in c.upper() or "승차" in c]
        if ride_cols:
            avg_ride = line_df[ride_cols].mean()
            st.subheader(f"📊 {selected_line} 시간대별 평균 승차")
            st.line_chart(avg_ride)
        
        st.write("### 📋 상세 데이터 (일부)")
        st.dataframe(line_df.head())
    else:
        st.error("⚠️ 호선(LINE) 컬럼을 여전히 찾을 수 없습니다. 아래 전체 데이터를 확인하세요.")
        st.dataframe(df)

elif "RESULT" in result:
    st.error(f"❌ API 서버 에러 메시지: {result['RESULT']['MESSAGE']}")
    st.info("💡 날짜를 '202405'로 입력하고 다시 해보세요. 최신 달은 데이터가 없습니다.")
else:
    st.error("알 수 없는 응답입니다.")
    st.json(result)
