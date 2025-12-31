import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="서울 지하철 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 서울 지하철 API 분석 (최종 수정본)")

# 1. 사이드바 설정 (데이터가 확실히 있는 2024년 10월을 기본값으로!)
st.sidebar.header("📡 데이터 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202410")
st.sidebar.warning("⚠️ 최신 월은 데이터가 없을 수 있습니다. '202410'으로 먼저 테스트하세요.")

# 2. 데이터 로드 함수
@st.cache_data(ttl=3600)
def load_subway_data(api_key, month):
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}/"
    try:
        res = requests.get(url)
        data = res.json()
        
        # [중요] 'CardSubwayTime' 키가 있는지 확인
        if "CardSubwayTime" in data:
            df = pd.DataFrame(data["CardSubwayTime"]["row"])
            return df, "SUCCESS"
        elif "RESULT" in data:
            return None, f"API 메시지: {data['RESULT']['MESSAGE']} ({data['RESULT']['CODE']})"
        else:
            return None, "알 수 없는 응답 형식입니다."
    except Exception as e:
        return None, f"연결 오류: {str(e)}"

# 실행
df, status = load_subway_data(API_KEY, target_month)

# 3. 데이터 처리 및 시각화
if df is not None:
    # 🔴 여기서 LINE_NUM 존재 여부를 다시 한번 체크합니다.
    if "LINE_NUM" in df.columns:
        st.success(f"✅ {target_month} 데이터를 불러왔습니다.")
        
        # 숫자 변환
        num_cols = [col for col in df.columns if "_NUM" in col]
        df[num_cols] = df[num_cols].apply(pd.to_numeric)

        # 호선 선택
        lines = sorted(df["LINE_NUM"].unique())
        selected_line = st.sidebar.selectbox("호선 선택", lines)
        line_df = df[df["LINE_NUM"] == selected_line]

        # 간단한 그래프 시각화
        ride_cols = [col for col in df.columns if "_RIDE_NUM" in col]
        avg_data = line_df[ride_cols].mean().reset_index()
        avg_data.columns = ['시간대', '인원']
        
        fig = px.bar(avg_data, x='시간대', y='인원', title=f"{selected_line} 시간대별 평균 승차")
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(line_df.head())
    else:
        # 데이터가 왔지만 LINE_NUM이 없는 특수 상황
        st.error("데이터 수신은 성공했으나 형식이 올바르지 않습니다.")
        st.write("불러온 데이터 실제 모습:", df) 
else:
    # ❌ 에러 발생 시 안내
    st.error(f"❌ 데이터를 가져오지 못했습니다.")
    st.info(f"이유: {status}")
    st.markdown("---")
    st.write("### 💡 해결 방법")
    st.write("1. 왼쪽 사이드바 날짜를 **202410**으로 입력해 보세요.")
    st.write("2. 만약 '인증키가 유효하지 않습니다'라고 뜨면 30분 뒤에 시도해 보세요.")
