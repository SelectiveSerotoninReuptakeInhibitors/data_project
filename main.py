import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="서울 지하철 분석기", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 드디어 해결! 지하철 이용 패턴 분석")

# 1. 사이드바 - 무조건 데이터가 있는 달로 기본값 세팅!
st.sidebar.header("📡 데이터 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202410")
st.sidebar.info("💡 2025년 데이터는 아직 집계 중이라 안 나옵니다. 202410으로 테스트하세요!")

# 2. 데이터 로드 함수 (구조 분석 강화)
@st.cache_data(ttl=3600)
def load_fixed_data(api_key, month):
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        
        # [핵심] 진짜 데이터가 들어있는지 확인
        if "CardSubwayTime" in data:
            df = pd.DataFrame(data["CardSubwayTime"]["row"])
            return df, "SUCCESS"
        elif "RESULT" in data:
            return None, f"{data['RESULT']['MESSAGE']} ({data['RESULT']['CODE']})"
        else:
            return None, "알 수 없는 응답 구조"
    except:
        return None, "서버 연결 실패"

df, status = load_fixed_data(API_KEY, target_month)

# 3. 데이터가 있을 때만 분석 진행
if df is not None:
    # 컬럼명 대문자 통일 (에러 방지)
    df.columns = [c.upper() for c in df.columns]
    
    # LINE_NUM 컬럼이 있는지 확인
    if "LINE_NUM" in df.columns:
        st.success(f"✨ {target_month} 데이터 연결 완료!")
        
        # 호선 선택
        lines = sorted(df["LINE_NUM"].unique())
        sel_line = st.sidebar.selectbox("🚇 호선 선택", lines)
        line_df = df[df["LINE_NUM"] == sel_line]

        # 숫자 변환
        num_cols = [c for c in df.columns if "NUM" in c]
        line_df[num_cols] = line_df[num_cols].apply(pd.to_numeric)

        # 시간대 그래프 (승차 위주)
        ride_cols = [c for c in num_cols if "RIDE" in c]
        avg_ride = line_df[ride_cols].mean().reset_index()
        avg_ride.columns = ['시간대', '평균승차']

        # 그래프 그리기
        st.subheader(f"📈 {sel_line} 시간대별 이용객 (평균)")
        fig = px.bar(avg_ride, x='시간대', y='평균승차', color='평균승차', color_continuous_scale='Blues')
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(line_df.head())
    else:
        st.error("데이터 구조에 'LINE_NUM'이 없습니다. 현재 데이터 내용을 확인하세요.")
        st.write(df) # 여기에 CODE와 MESSAGE만 뜬다면 날짜 문제!
else:
    st.error(f"❌ 실패: {status}")
    st.warning("👉 해결방법: 왼쪽 사이드바 날짜를 '202410' 또는 '202409'로 입력하고 엔터를 치세요!")
