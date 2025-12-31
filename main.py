import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 지하철 최종 분석", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 지하철 데이터 분석 (수치 보정 완료)")

# 1. 데이터 로드 (가장 최신 달 자동 탐색)
@st.cache_data(ttl=3600)
def get_verified_data():
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

df, found_month = get_verified_data()

if df is not None:
    # 컬럼명 정리 및 대문자화
    df.columns = [c.strip().upper() for c in df.columns]
    
    # [핵심] 모든 데이터를 숫자로 변환 시도 (문자열로 들어오는 숫자 방지)
    # _NUM이 포함된 모든 컬럼을 찾아 숫자로 바꿉니다.
    num_cols = [c for c in df.columns if "NUM" in c or "CNT" in c]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.success(f"✅ {found_month} 데이터 수신 완료 (숫자 변환 성공)")

    # 호선 컬럼 찾기
    line_col = next((c for c in df.columns if "LINE" in c or "호선" in c), df.columns[1])
    lines = sorted(df[line_col].unique())

    # --- 사이드바: 호선 상세 분석 ---
    st.sidebar.header("🔍 상세 분석")
    selected_line = st.sidebar.selectbox("호선 선택", lines, index=lines.index("2호선") if "2호선" in lines else 0)
    
    line_df = df[df[line_col] == selected_line]
    
    # 시간대별 승차 데이터만 추출
    ride_cols = [c for c in num_cols if "RIDE" in c]
    # 시간대별 평균 인원 계산
    avg_ride = line_df[ride_cols].mean().reset_index()
    avg_ride.columns = ['시간대', '인원']
    # '07시'처럼 이름 예쁘게 자르기
    avg_ride['시간'] = avg_ride['시간대'].map(lambda x: x[:2] if x[0].isdigit() else x.split('_')[0])

    # 📊 그래프 1: 상세 분석
    st.subheader(f"📊 {selected_line} 시간대별 평균 승차 인원")
    if avg_ride['인원'].sum() > 0:
        fig1 = px.bar(avg_ride, x='시간', y='인원', color='인원', color_continuous_scale='Reds')
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.warning("데이터 수치가 모두 0입니다. API 응답 내용을 확인해야 합니다.")

    st.markdown("---")

    # --- 기능 2: 1호선 vs 2호선 승객 수 비교 ---
    st.subheader("⚔️ 호선별 승객 규모 비교")
    
    # 비교 대상 (기본 1호선, 2호선)
    comp_lines = st.multiselect("비교할 호선을 선택하세요", lines, default=[l for l in ["1호선", "2호선"] if l in lines])
    
    if comp_lines:
        compare_df = df[df[line_col].isin(comp_lines)]
        # 전체 시간대 승차 인원 합산
        summary = compare_df.groupby(line_col)[ride_cols].sum().sum(axis=1).reset_index()
        summary.columns = ['호선', '총승객수']
        
        col1, col2 = st.columns([2, 1])
        with col1:
            fig2 = px.pie(summary, names='호선', values='총승객수', hole=0.3,
                          title="선택한 호선별 전체 승객 비중")
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            st.write("#### 📈 총 승객 수 (명)")
            for _, row in summary.iterrows():
                st.metric(row['호선'], f"{int(row['총승객수']):,}명")
else:
    st.error("데이터 로드에 실패했습니다. API 키를 확인하거나 잠시 후 다시 시도해주세요.")
