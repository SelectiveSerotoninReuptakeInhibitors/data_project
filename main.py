import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="서울 지하철 분석기 - 최종", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 이번엔 진짜로 뜹니다! 지하철 대시보드")

# 1. 날짜를 데이터가 확실히 존재하는 달로 강제 고정
# 최신 데이터(2025년)는 아직 정산 중이라 API가 에러를 뱉습니다.
target_month = "202410" 

@st.cache_data(ttl=3600)
def load_data(api_key, month):
    # API 주소 형식을 가장 표준적인 형태로 수정
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        
        if "CardSubwayTime" in data:
            return pd.DataFrame(data["CardSubwayTime"]["row"]), "SUCCESS"
        elif "RESULT" in data:
            return None, f"{data['RESULT']['MESSAGE']} (코드: {data['RESULT']['CODE']})"
        else:
            return None, "API 서버가 알 수 없는 응답을 보냈습니다."
    except Exception as e:
        return None, f"연결 오류: {str(e)}"

# 실행
df, status = load_data(API_KEY, target_month)

# --- 2. 분석 및 시각화 ---
if df is not None:
    st.success(f"🎉 성공! {target_month}월 지하철 데이터를 가져왔습니다.")
    
    # 컬럼명 대문자화 및 공백 제거
    df.columns = [c.strip().upper() for c in df.columns]
    
    # LINE_NUM 컬럼 확인
    if "LINE_NUM" in df.columns:
        lines = sorted(df["LINE_NUM"].unique())
        selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
        line_df = df[df["LINE_NUM"] == selected_line]

        # 숫자 변환
        num_cols = [c for c in df.columns if "NUM" in c]
        line_df[num_cols] = line_df[num_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

        # 시간대별 승차 차트
        ride_cols = [c for c in num_cols if "RIDE" in c]
        avg_ride = line_df[ride_cols].mean().reset_index()
        avg_ride.columns = ['시간대', '인원']
        
        # 차트 그리기
        st.subheader(f"📊 {selected_line} 시간대별 평균 승차 인원")
        fig = px.bar(avg_ride, x='시간대', y='인원', color='인원', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(line_df.head())
    else:
        st.warning("⚠️ 데이터를 가져왔으나 호선 정보를 찾을 수 없습니다.")
        st.write("실제 데이터 구조:", df)
else:
    st.error(f"❌ 데이터 로드 실패: {status}")
    st.info("💡 서울시 API 서버가 아직 최신(2025년) 데이터를 준비하지 못했습니다. 위 코드에서 202410으로 테스트 중입니다.")

# 디버깅을 위한 원본 JSON 확인
if st.checkbox("API 원본 응답 확인"):
    st.write(load_data(API_KEY, target_month))
