import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 지하철 비교 분석기", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 지하철 데이터 분석 & 호선별 비교")

# 1. 데이터 로드 (최신 달 자동 탐색)
@st.cache_data(ttl=3600)
def get_data():
    for i in range(1, 13):
        target_date = datetime.now() - timedelta(days=30 * i)
        month_str = target_date.strftime("%Y%m")
        url = f"http://openAPI.seoul.go.kr:8088/{API_KEY}/json/CardSubwayTime/1/1000/{month_str}"
        try:
            res = requests.get(url)
            data = res.json()
            if "CardSubwayTime" in data:
                return pd.DataFrame(data["CardSubwayTime"]["row"]), month_str
        except: continue
    return None, None

df_raw, found_month = get_data()

if df_raw is not None:
    # 컬럼 정리
    df_raw.columns = [c.strip().upper() for c in df_raw.columns]
    st.success(f"✅ {found_month} 데이터 분석 중")

    # 호선 컬럼 찾기
    line_col = "LINE_NUM" if "LINE_NUM" in df_raw.columns else df_raw.columns[1]
    
    # --- [수치 보정 로직] ---
    # 모든 숫자형 컬럼(RIDE, ALIGHT 포함)을 강제로 숫자로 변환
    num_cols = [c for c in df_raw.columns if "NUM" in c or "CNT" in c or "인원" in c]
    for col in num_cols:
        df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)

    # --- 기능 1: 개별 호선 상세 분석 ---
    lines = sorted(df_raw[line_col].unique())
    selected_line = st.sidebar.selectbox("🔍 상세 분석할 호선", lines, index=lines.index("2호선") if "2호선" in lines else 0)
    
    line_df = df_raw[df_raw[line_col] == selected_line]
    ride_cols = [c for c in num_cols if "RIDE" in c or "승차" in c]
    
    # 시간대별 평균 계산 (수치가 안 나올 수 없게 강제 계산)
    avg_ride = line_df[ride_cols].mean().reset_index()
    avg_ride.columns = ['시간대', '인원']
    # 시간대 이름 간소화 (04시_승차인원 -> 04시)
    avg_ride['시간'] = avg_ride['시간대'].apply(lambda x: x.split('_')[0] if '_' in x else x[:2])

    st.subheader(f"📊 {selected_line} 시간대별 이용객 현황")
    fig1 = px.bar(avg_ride, x='시간', y='인원', color='인원', color_continuous_scale='Blues')
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("---")

    # --- 기능 2: [요청하신] 호선 비교 (1호선 vs 2호선) ---
    st.subheader("⚔️ 호선별 승객 수 비교 (1호선 vs 2호선)")
    
    # 비교할 호선 선택 (기본값 1호선, 2호선)
    comp_lines = st.multiselect("비교할 호선들을 선택하세요", lines, default=[l for l in ["1호선", "2호선"] if l in lines])
    
    if comp_lines:
        compare_df = df_raw[df_raw[line_col].isin(comp_lines)]
        # 호선별 전체 승객 합계 계산
        comp_result = compare_df.groupby(line_col)[ride_cols].sum().sum(axis=1).reset_index()
        comp_result.columns = ['호선', '총 승객 수']
        
        fig2 = px.pie(comp_result, names='호선', values='총 승객 수', 
                      title="선택 호선별 전체 승객 비중",
                      hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.plotly_chart(fig2, use_container_width=True)
        with c2:
            st.write("#### 📈 수치 비교")
            for idx, row in comp_result.iterrows():
                st.metric(f"{row['호선']} 총 승객", f"{int(row['총 승객 수']):,} 명")
    
else:
    st.error("데이터를 가져오는 데 실패했습니다. API 키나 인터넷 연결을 확인해주세요.")
