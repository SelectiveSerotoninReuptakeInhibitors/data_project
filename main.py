import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np
import requests

st.set_page_config(page_title="서울 지하철 API 대시보드", layout="wide")
st.title("⏰ 서울 지하철 시간대별 이용 분석 대시보드")

# --- 1. API 설정 및 데이터 로드 ---
# 본인의 API 인증키를 입력하세요
API_KEY = "인증키번호" 

st.sidebar.header("📡 데이터 소스 설정")
data_source = st.sidebar.radio("데이터 불러오기 방식", ["API 실시간 로드", "CSV 파일 업로드"])

df = None

if data_source == "API 실시간 로드":
    target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202401")
    if st.sidebar.button("데이터 불러오기"):
        # 서울시 지하철 시간대별 승하차 API URL
        url = f"http://openAPI.seoul.go.kr:8088/{API_KEY}/json/CardSubwayTime/1/1000/{target_month}"
        
        try:
            res = requests.get(url)
            data = res.json()
            
            if "CardSubwayTime" in data:
                df = pd.DataFrame(data["CardSubwayTime"]["row"])
                st.success(f"✅ {target_month} API 데이터 로드 완료!")
            else:
                st.error("❌ API 데이터를 가져오지 못했습니다. 인증키와 날짜를 확인하세요.")
        except Exception as e:
            st.error(f"연결 오류: {e}")

else:
    uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드", type="csv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file, encoding="cp949")

# --- 2. 데이터 처리 및 시각화 ---
if df is not None:
    # API 데이터인 경우 컬럼명 매핑 및 타입 변환 필요
    if "LINE_NUM" in df.columns:
        # API 영문 컬럼명을 한글/숫자형태로 변환하는 작업
        time_cols = [col for col in df.columns if "_NUM" in col]
        df[time_cols] = df[time_cols].apply(pd.to_numeric)
        line_col = "LINE_NUM"
        station_col = "SUB_STA_NM"
    else:
        # CSV 데이터인 경우 기존 로직 유지
        line_col = next((col for col in df.columns if "호선" in str(col)), None)
        time_cols = [col for col in df.columns if re.search(r"\d{2}시-\d{2}시", str(col))]
        station_col = next((col for col in df.columns if "역명" in str(col)), "역명")

    # 전처리 옵션
    st.sidebar.header("🧹 전처리 옵션")
    na_method = st.sidebar.selectbox("결측치 처리", ["0으로 채우기", "평균으로 채우기"])
    normalize_flag = st.sidebar.checkbox("Min-Max 정규화 적용", value=False)

    work_df = df.copy()
    # 결측치 처리
    if na_method == "0으로 채우기":
        work_df[time_cols] = work_df[time_cols].fillna(0)
    else:
        work_df[time_cols] = work_df[time_cols].apply(lambda s: s.fillna(s.mean()))

    # 정규화
    if normalize_flag:
        work_df[time_cols] = (work_df[time_cols] - work_df[time_cols].min()) / (work_df[time_cols].max() - work_df[time_cols].min() + 1e-9)

    # 호선 선택 및 필터링
    lines = sorted(work_df[line_col].unique())
    selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
    line_df = work_df[work_df[line_col] == selected_line]

    # --- 3. 시각화 데이터 가공 ---
    avg_series = line_df[time_cols].mean()
    hourly_data = []

    for col in time_cols:
        # API 컬럼(FOUR_RIDE_NUM) 또는 CSV 컬럼(04시-05시)에서 시간 추출
        hour_search = re.search(r"(\d{2})", col)
        if hour_search:
            h = int(hour_search.group(1))
        else:
            # API 영문 컬럼명 처리 (예: FOUR -> 4)
            mapping = {"FOUR":4,"FIVE":5,"SIX":6,"SEVEN":7,"EIGHT":8,"NINE":9,"TEN":10,"ELEVEN":11,"TWELVE":12,"THIR":13,"FOURT":14,"FIFT":15,"SIXT":16,"SEVENT":17,"EIGHTE":18,"NINETE":19,"TWENTY":20}
            h = next((v for k, v in mapping.items() if k in col), 0)
        
        hourly_data.append({"시간": h, "값": avg_series[col], "유형": "승차" if "RIDE" in col or "승차" in col else "하차"})

    hourly_df = pd.DataFrame(hourly_data).sort_values("시간")

    # --- 4. 그래프 출력 ---
    st.subheader(f"📈 {selected_line} 이용 패턴 분석")
    fig = px.line(hourly_df, x="시간", y="값", color="유형", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # 메트릭 표시
    peak_val = hourly_df["값"].max()
    peak_hour = hourly_df.loc[hourly_df["값"].idxmax(), "시간"]
    
    c1, c2 = st.columns(2)
    c1.metric("🏆 피크 시간대", f"{peak_hour}시")
    c2.metric("📊 평균 이용객", f"{hourly_df['값'].mean():.2f}")

    st.subheader("📋 데이터 상세")
    st.dataframe(line_df.head())

else:
    st.info("왼쪽 사이드바에서 API 데이터를 불러오거나 CSV 파일을 업로드해주세요.")
