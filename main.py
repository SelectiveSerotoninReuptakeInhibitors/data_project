import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="서울 지하철 분석 끝판왕", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 지하철 데이터 분석 (수치 복구 완료)")

@st.cache_data(ttl=3600)
def get_final_data():
    # 데이터가 확실히 존재하는 달부터 역순으로 탐색
    for i in range(2, 12):
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

df, found_month = get_final_data()

if df is not None:
    # 1. 데이터 정제: 모든 컬럼명을 대문자로 통일
    df.columns = [c.strip().upper() for c in df.columns]
    
    # 2. 숫자 변환: 수치형 데이터 강제 형변환
    num_cols = [c for c in df.columns if any(keyword in c for keyword in ["NUM", "CNT", "인원"])]
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    st.success(f"✅ {found_month} 데이터 수신 및 수치 복구 성공!")

    # 3. 호선 컬럼 자동 식별
    line_col = next((c for c in df.columns if any(k in c for k in ["LINE", "호선"])), df.columns[1])
    lines = sorted(df[line_col].unique())

    # --- 기능 1: 상세 분석 ---
    selected_line = st.sidebar.selectbox("🚇 호선 선택", lines, index=lines.index("2호선") if "2호선" in lines else 0)
    line_df = df[df[line_col] == selected_line]

    # [핵심] 승차(RIDE) 데이터 컬럼만 지능적으로 추출
    ride_cols = [c for c in num_cols if "RIDE" in c or "승차" in c]
    
    # 시간대별 합계 계산
    graph_data = line_df[ride_cols].mean().reset_index()
    graph_data.columns = ['시간대', '인원']
    
    # 시간대 이름 가독성 있게 정리 (04시_RIDE -> 04시)
    graph_data['시간'] = graph_data['시간대'].str.extract(r'(\d+)').fillna('00') + "시"

    # 📊 그래프 1
    st.subheader(f"📊 {selected_line} 시간대별 평균 이용객")
    if graph_data['인원'].sum() > 0:
        fig1 = px.bar(graph_data, x='시간', y='인원', color='인원', color_continuous_scale='Turbo')
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.error("⚠️ 데이터를 찾았으나 수치 필터링에 실패했습니다. 컬럼명을 확인하세요.")
        st.write("사용 가능한 컬럼들:", ride_cols)

    st.markdown("---")

    # --- 기능 2: 1호선 vs 2호선 비교 ---
    st.subheader("⚔️ 호선별 승객 규모 비교 (1호선 vs 2호선)")
    comp_targets = [l for l in ["1호선", "2호선"] if l in lines]
    comp_lines = st.multiselect("비교 대상 선택", lines, default=comp_targets)

    if comp_lines:
        comp_df = df[df[line_col].isin(comp_lines)]
        summary = comp_df.groupby(line_col)[ride_cols].sum().sum(axis=1).reset_index()
        summary.columns = ['호선', '총승객수']

        col1, col2 = st.columns([2, 1])
        with col1:
            fig2 = px.pie(summary, names='호선', values='총승객수', hole=0.4, title="전체 승객 비중")
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            for _, row in summary.iterrows():
                st.metric(row['호선'], f"{int(row['총승객수']):,}명")

else:
    st.error("데이터 로드 실패. API 키 활성화 여부를 확인하세요.")
