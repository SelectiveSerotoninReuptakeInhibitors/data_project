import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- 1. 기본 설정 및 인증키 ---
st.set_page_config(page_title="서울 지하철 분석 대시보드", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("⏰ 서울 지하철 시간대별 이용 분석 (API 실시간)")

# 사이드바 설정
st.sidebar.header("📡 조회 설정")
# 데이터가 확실히 존재하는 달을 기본값으로 설정
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202410")

# --- 2. 데이터 통합 로딩 함수 ---
@st.cache_data(ttl=3600)
def load_all_subway_data(api_key, month):
    all_rows = []
    # 데이터가 1000건이 넘으므로 두 번에 나누어 호출 (총 2000건 확보)
    for start in [1, 1001]:
        end = start + 999
        url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/{start}/{end}/{month}"
        try:
            res = requests.get(url)
            data = res.json()
            if "CardSubwayTime" in data:
                all_rows.extend(data["CardSubwayTime"]["row"])
        except:
            continue
    
    if not all_rows:
        return None
    return pd.DataFrame(all_rows)

# 데이터 호출
df_raw = load_all_subway_data(API_KEY, target_month)

# --- 3. 데이터 전처리 ---
if df_raw is not None:
    # 숫자형 변환
    num_cols = [col for col in df_raw.columns if "_NUM" in col]
    df_raw[num_cols] = df_raw[num_cols].apply(pd.to_numeric)

    # 호선 선택
    lines = sorted(df_raw["LINE_NUM"].unique())
    selected_line = st.sidebar.selectbox("🚇 분석할 호선 선택", lines)
    line_df = df_raw[df_raw["LINE_NUM"] == selected_line]

    # --- 4. 시간대 데이터 재구성 ---
    # API 영문 컬럼명 -> 숫자 시간 매핑
    time_map = {
        'FOUR': 4, 'FIVE': 5, 'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        'ELEVEN': 11, 'TWELVE': 12, 'THIRTEEN': 13, 'FOURTEEN': 14, 'FIFTEEN': 15,
        'SIXTEEN': 16, 'SEVENTEEN': 17, 'EIGHTEEN': 18, 'NINETEEN': 19, 'TWENTY': 20,
        'TWENTY_ONE': 21, 'TWENTY_TWO': 22, 'TWENTY_THREE': 23, 'MIDNIGHT': 0
    }

    # 승차(RIDE)와 하차(ALIGHT) 데이터 분리 및 집계
    ride_data = []
    alight_data = []

    for eng, hour in time_map.items():
        ride_col = f"{eng}_RIDE_NUM"
        alight_col = f"{eng}_ALIGHT_NUM"
        
        if ride_col in line_df.columns:
            ride_data.append({"시간": hour, "인원": line_df[ride_col].mean(), "구분": "승차"})
        if alight_col in line_df.columns:
            alight_data.append({"시간": hour, "인원": line_df[alight_col].mean(), "구분": "하차"})

    plot_df = pd.concat([pd.DataFrame(ride_data), pd.DataFrame(alight_data)]).sort_values("시간")

    # --- 5. 시각화 영역 ---
    st.subheader(f"📊 {selected_line} 시간대별 승하차 패턴 ({target_month})")

    # (1) 메인 선 그래프
    fig_line = px.line(plot_df, x="시간", y="인원", color="구분", markers=True,
                       title=f"{selected_line} 평균 이용객 추이",
                       color_discrete_map={"승차": "#FF4B4B", "하차": "#1C83E1"})
    fig_line.update_layout(xaxis=dict(tickmode="linear", dtick=1))
    st.plotly_chart(fig_line, use_container_width=True)

    # (2) 주요 지표 (Metrics)
    col1, col2, col3 = st.columns(3)
    peak_ride = plot_df[plot_df["구분"]=="승차"].loc[plot_df[plot_df["구분"]=="승차"]["인원"].idxmax()]
    col1.metric("🏆 최대 승차 시간", f"{int(peak_ride['시간'])}시", f"{int(peak_ride['인원'])}명")
    
    total_stations = len(line_df)
    col2.metric("🚉 분석 역 개수", f"{total_stations}개 역")
    
    avg_daily = plot_df["인원"].mean()
    col3.metric("👥 시간대별 평균 이용", f"{int(avg_daily)}명")

    # (3) 역별 비교 (Top 10)
    st.subheader(f"🔝 {selected_line} 이용객 상위 10개 역")
    line_df['총이용객'] = line_df[num_cols].sum(axis=1)
    top10 = line_df.nlargest(10, '총이용객')
    fig_bar = px.bar(top10, x="SUB_STA_NM", y="총이용객", color="총이용객",
                     labels={"SUB_STA_NM": "역 이름", "총이용객": "전체 이용객 수"})
    st.plotly_chart(fig_bar, use_container_width=True)

    # (4) 상세 데이터
    with st.expander("📄 전체 데이터 표 보기"):
        st.dataframe(line_df)

else:
    st.error("데이터를 불러오지 못했습니다. 날짜(YYYYMM)를 확인해주세요.")
    st.info("💡 팁: 공공데이터는 확정까지 시간이 걸립니다. 202410이나 202409를 입력해보세요.")
