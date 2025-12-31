import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import re

# --- 0. 기본 설정 및 최신 월 계산 ---
st.set_page_config(page_title="서울 지하철 실시간 분석", layout="wide")

# 오늘 날짜 기준으로 전월(Last Month)을 기본값으로 설정
today = datetime.now()
first_day_of_this_month = today.replace(day=1)
last_month_date = first_day_of_this_month - timedelta(days=1)
default_month = last_month_date.strftime("%Y%m")

st.title("⏰ 서울 지하철 시간대별 이용 분석 대시보드")

# --- 1. API 설정 (인증키 포함) ---
API_KEY = "58717a597473616e38347858797067"

st.sidebar.header("📡 데이터 조회 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value=default_month)

# --- 2. 데이터 로딩 함수 ---
@st.cache_data(ttl=3600) # 1시간 동안 캐시 유지
def load_subway_api(api_key, month):
    # 한 번에 최대 1000개 행을 가져옵니다.
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}"
    try:
        res = requests.get(url)
        data = res.json()
        if "CardSubwayTime" in data:
            df_api = pd.DataFrame(data["CardSubwayTime"]["row"])
            return df_api
        else:
            return None
    except Exception as e:
        st.error(f"연결 중 오류 발생: {e}")
        return None

# 데이터 불러오기 실행
df = load_subway_api(API_KEY, target_month)

# --- 3. 데이터 전처리 및 시각화 ---
if df is not None:
    # API 데이터 컬럼명 정리 및 숫자 변환
    # RIDE_NUM(승차), ALIGHT_NUM(하차)이 포함된 컬럼들을 숫자로 변환
    num_cols = [col for col in df.columns if "_NUM" in col]
    df[num_cols] = df[num_cols].apply(pd.to_numeric)

    st.sidebar.markdown(f"**현재 데이터:** {target_month}")
    
    # 3-1. 전처리 옵션 (사이드바)
    st.sidebar.header("🧹 전처리 옵션")
    normalize_flag = st.sidebar.checkbox("시간대 값 정규화 (0~1)", value=False)

    # 3-2. 호선 선택
    lines = sorted(df["LINE_NUM"].unique())
    selected_line = st.sidebar.selectbox("🚇 호선 선택", lines)
    line_df = df[df["LINE_NUM"] == selected_line]

    # 3-3. 시간대별 데이터 가공 (승차 인원 기준)
    # API 컬럼명에서 'FOUR_RIDE_NUM' 등의 승차 데이터만 추출
    ride_cols = [col for col in df.columns if "_RIDE_NUM" in col]
    avg_ride = line_df[ride_cols].mean()

    # 영문 컬럼명을 시간(숫자)으로 매핑
    time_mapping = {
        'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13, 'FOURTEEN': 14, 'FIFTEEN': 15,
        'SIXTEEN': 16, 'SEVENTEEN': 17, 'EIGHTEEN': 18, 'NINETEEN': 19, 'TWENTY': 20,
        'TWENTY_ONE': 21, 'TWENTY_TWO': 22, 'TWENTY_THREE': 23, 'MIDNIGHT': 0,
        'ONE': 1, 'TWO': 2, 'THREE': 3
    }

    plot_data = []
    for col in ride_cols:
        # 컬럼명에서 시간 키워드 추출 (예: FOUR_RIDE_NUM -> FOUR)
        prefix = col.split('_RIDE')[0]
        hour = time_mapping.get(prefix, 0)
        plot_data.append({"시간": hour, "승차인원": avg_ride[col]})

    hourly_df = pd.DataFrame(plot_data).sort_values("시간")

    # 정규화 적용 시
    if normalize_flag:
        v_min, v_max = hourly_df["승차인원"].min(), hourly_df["승차인원"].max()
        hourly_df["승차인원"] = (hourly_df["승차인원"] - v_min) / (v_max - v_min + 1e-9)
        y_label = "정규화된 값 (0~1)"
    else:
        y_label = "평균 승차인원 (명)"

    # --- 4. 시각화 출력 ---
    st.subheader(f"📈 {selected_line} 시간대별 승차 패턴 ({target_month})")
    
    fig = px.line(hourly_df, x="시간", y="승차인원", markers=True,
                  title=f"{selected_line} 시간대별 이용객 추이",
                  labels={"승차인원": y_label})
    
    fig.update_layout(xaxis=dict(tickmode="linear", dtick=1))
    st.plotly_chart(fig, use_container_width=True)

    # 주요 지표 (Metrics)
    peak_row = hourly_df.loc[hourly_df["승차인원"].idxmax()]
    c1, c2, c3 = st.columns(3)
    c1.metric("🏆 피크 시간대", f"{int(peak_row['시간'])}시")
    c2.metric("👥 평균 승차인원", f"{hourly_df['승차인원'].mean():.1f}")
    c3.metric("📊 총 분석 역 개수", f"{len(line_df)}개")

    # 상세 데이터 미리보기
    with st.expander("📋 데이터 원본 보기"):
        st.dataframe(line_df)

else:
    st.info(f"📅 {target_month} 데이터를 불러올 수 없습니다. 아직 데이터가 업데이트되지 않았을 수 있으니 지난달을 조회해 보세요.")
