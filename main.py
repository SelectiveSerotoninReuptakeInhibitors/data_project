import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="서울 지하철 최종 대시보드", layout="wide")
API_KEY = "58717a597473616e38347858797067"

st.title("🚇 서울 지하철 실시간 API 분석 완료!")

# 1. 사이드바 설정
st.sidebar.header("📡 데이터 설정")
target_month = st.sidebar.text_input("조회 월 (YYYYMM)", value="202410")

# 2. 데이터 로드 함수
@st.cache_data(ttl=3600)
def load_final_data(api_key, month):
    # 주소 끝에 슬래시(/)를 붙여서 더 정확하게 요청합니다.
    url = f"http://openAPI.seoul.go.kr:8088/{api_key}/json/CardSubwayTime/1/1000/{month}/"
    try:
        res = requests.get(url)
        data = res.json()
        
        if "CardSubwayTime" in data:
            df = pd.DataFrame(data["CardSubwayTime"]["row"])
            # [핵심] 모든 컬럼명을 대문자로 바꾸고 양끝 공백을 제거해서 에러 방지
            df.columns = [c.strip().upper() for c in df.columns]
            return df, "SUCCESS"
        elif "RESULT" in data:
            return None, data["RESULT"]["MESSAGE"]
        else:
            return None, "데이터 구조 이상"
    except Exception as e:
        return None, str(e)

# 실행!
df, status = load_final_data(API_KEY, target_month)

# 3. 데이터 처리 및 시각화
if df is not None:
    # 🔍 컬럼명 자동 매핑 (LINE_NUM이 없으면 '호선명' 등으로라도 찾음)
    line_col = next((c for c in df.columns if "LINE" in c or "호선" in c), None)
    
    if line_col:
        st.success(f"✅ {target_month} 데이터 연결 성공! (컬럼명: {line_col})")
        
        # 숫자형 변환 (에러 방지)
        for col in df.columns:
            if "NUM" in col or "CNT" in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 호선 선택
        lines = sorted(df[line_col].unique())
        selected_line = st.sidebar.selectbox("🚇 분석할 호선 선택", lines)
        line_df = df[df[line_col] == selected_line]

        # --- 시간대별 그래프 가공 ---
        # 승차(RIDE) 컬럼들만 모으기
        ride_cols = [c for c in df.columns if "RIDE" in c]
        avg_data = line_df[ride_cols].mean().reset_index()
        avg_data.columns = ['시간대', '인원']
        
        # 시간대 이름 예쁘게 정리 (예: FOUR_RIDE_NUM -> 04시)
        time_labels = {
            'FOUR': '04시', 'FIVE': '05시', 'SIX': '06시', 'SEVEN': '07시', 'EIGHT': '08시',
            'NINE': '09시', 'TEN': '10시', 'ELEVEN': '11시', 'TWELVE': '12시', 'THIRTEEN': '13시',
            'FOURTEEN': '14시', 'FIFTEEN': '15시', 'SIXTEEN': '16시', 'SEVENTEEN': '17시',
            'EIGHTEEN': '18시', 'NINETEEN': '19시', 'TWENTY': '20시', 'TWENTY_ONE': '21시',
            'TWENTY_TWO': '22시', 'TWENTY_THREE': '23시'
        }
        avg_data['시간'] = avg_data['시간대'].apply(lambda x: next((v for k, v in time_labels.items() if k in x), x))
        avg_data = avg_data.sort_values('시간')

        # 그래프 출력
        st.subheader(f"📊 {selected_line} 시간대별 이용객 추이")
        fig = px.line(avg_data, x='시간', y='인원', markers=True, 
                      color_discrete_sequence=['#FF4B4B'])
        st.plotly_chart(fig, use_container_width=True)

        # 데이터 표
        with st.expander("데이터 원본 보기"):
            st.dataframe(line_df)
    else:
        st.error("데이터에 호선(LINE) 관련 컬럼을 찾을 수 없습니다.")
        st.write("불러온 컬럼들:", list(df.columns))
else:
    st.error(f"❌ 실패: {status}")
    st.info("날짜를 202410으로 입력하셨나요? 최신 달은 데이터가 없을 수 있습니다.")
