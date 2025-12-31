import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="서울 지하철 API 진단", layout="wide")

# 1. 사용자가 제공한 인증키
API_KEY = "58717a597473616e38347858797067"

st.title("⚙️ 지하철 API 연결 상태 진단")

# 2. 날짜 설정 (가장 안정적인 과거 날짜 202410을 기본값으로 사용)
st.sidebar.header("조회 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202410")

# 3. API 호출 함수
def check_api_status(key, month):
    # 테스트용으로 1건만 호출
    url = f"http://openAPI.seoul.go.kr:8088/{key}/json/CardSubwayTime/1/1/{month}"
    try:
        res = requests.get(url)
        return res.json()
    except Exception as e:
        return {"error": str(e)}

# 진단 실행
st.write(f"### 📡 API 서버 응답 결과 ({target_month})")
result = check_api_status(API_KEY, target_month)

# 4. 결과 분석
if "CardSubwayTime" in result:
    st.success("✅ 인증키와 데이터 호출에 모두 성공했습니다!")
    st.write("불러온 데이터 예시:")
    df = pd.DataFrame(result["CardSubwayTime"]["row"])
    st.dataframe(df)
    
    st.info("이제 이 날짜로 기존 분석 코드를 실행하면 정상 작동합니다.")

elif "RESULT" in result:
    code = result["RESULT"]["CODE"]
    msg = result["RESULT"]["MESSAGE"]
    
    st.error(f"❌ API 서버에서 에러를 반환했습니다.")
    st.metric("에러 코드", code)
    st.metric("메시지", msg)
    
    if code == "INFO-200":
        st.warning("👉 원인: 해당 월의 데이터가 아직 없습니다. 날짜를 더 과거(예: 202409)로 바꿔보세요.")
    elif code == "INFO-300" or "인증키" in msg:
        st.warning("👉 원인: 인증키가 틀렸거나 아직 활성화되지 않았습니다. 30분 뒤에 다시 시도해보세요.")
else:
    st.error("알 수 없는 응답입니다.")
    st.json(result)
