import streamlit as st
import pandas as pd
import requests

# --- 1. 설정 ---
st.set_page_config(page_title="서울 지하철 API 진단", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 지하철 API 데이터 구조 확인")

# 날짜 설정 (가장 안정적인 2024년 5월로 테스트해보세요)
st.sidebar.header("📡 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202405")

# --- 2. 데이터 로드 ---
@st.cache_data
def load_debug_data(api_key, month):
    # 주소 형식을 아주 정확하게 다시 맞췄습니다.
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/100/{month}/"
    try:
        res = requests.get(url)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

result = load_debug_data(API_KEY, target_month)

# --- 3. 데이터 구조 검사 ---
if "CardSubwayTime" in result:
    df = pd.DataFrame(result["CardSubwayTime"]["row"])
    st.success(f"✅ {target_month} 데이터 수신 성공!")
    
    # 🔍 여기서 컬럼명을 강제로 한글화하거나 확인합니다.
    st.write("### 현재 데이터 컬럼 목록:", df.columns.tolist())
    
    # 만약 LINE_NUM이 대문자가 아니거나 다른 이름일 경우를 대비
    # 실제 API 표준은 'LINE_NUM'입니다.
    if "LINE_NUM" in df.columns:
        lines = sorted(df["LINE_NUM"].unique())
        selected_line = st.selectbox("호선 선택", lines)
        st.dataframe(df[df["LINE_NUM"] == selected_line])
    else:
        st.warning("⚠️ 'LINE_NUM' 컬럼이 보이지 않습니다. 아래 '전체 데이터'를 보고 실제 컬럼명을 확인하세요.")
        st.dataframe(df) # 어떤 컬럼이 들어왔는지 직접 확인

elif "RESULT" in result:
    st.error(f"❌ API 서버 메시지: {result['RESULT']['MESSAGE']}")
    st.write("코드:", result['RESULT']['CODE'])
    st.info("💡 팁: '해당 데이터가 없습니다'라고 나오면 날짜를 202405로 바꿔보세요.")

else:
    st.error("알 수 없는 응답입니다.")
    st.json(result)
