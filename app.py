import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
# 라이브러리 임포트 확인
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode
except ImportError:
    st.error("설치 오류: 'streamlit-aggrid'가 설치되지 않았습니다. requirements.txt에 추가가 필요합니다.")

# --- 1. 앱 기본 설정 ---
icon_file = "Lynn BI.png"
logo_file = "Lynn BI.png"

st.set_page_config(
    page_title="울산다운1차 작업 현황표",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 로고 및 스타일 ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    h1 { color: #333; border-bottom: 2px solid #e06000; padding-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 (동 선택) ---
with st.sidebar:
    st.header("🏢 동별 선택")
    building_list = [f"{i}동" for i in range(101, 121)]
    selected_building = st.selectbox("현황을 조회할 동을 선택하세요", building_list)
    st.divider()
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 4. 메인 제목 ---
logo_bin = get_base64_of_bin_file(logo_file)
if logo_bin:
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{logo_bin}" style="height: 45px; margin-right: 15px;">
        <h2 style="margin: 0; color: #e06000;">Woomi Construction</h2>
    </div>
    """, unsafe_allow_html=True)

st.title(f"📍 {selected_building} 실내기 설치 현황표")

# --- 5. 데이터 로드 및 AgGrid 설정 ---
@st.cache_data
def create_default_data():
    # 과장님 엑셀 구조처럼 20층부터 1층까지 생성
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    return pd.DataFrame([[r] + [""]*6 for r in rows], columns=cols)

if f'data_{selected_building}' not in st.session_state:
    st.session_state[f'data_{selected_building}'] = create_default_data()

df = st.session_state[f'data_{selected_building}']

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True, minWidth=100)

# 💡 칸 클릭/입력 시 주황색으로 변하는 로직 (JavaScript)
cellsytle_jscode = """
function(params) {
    if (params.value !== undefined && params.value !== '' && params.column.colId !== '층') {
        return {
            'color': 'white',
            'backgroundColor': '#e06000',
            'fontWeight': 'bold'
        }
    }
};
"""
for col in df.columns[1:-1]:
    gb.configure_column(col, cellStyle=cellsytle_jscode)

grid_options = gb.build()

# 표 출력
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
    theme='alpine'
)

# 데이터 자동 저장
st.session_state[f'data_{selected_building}'] = grid_response['data']

if st.button("💾 현재 현황 임시 저장"):
    st.success(f"{selected_building} 데이터가 업데이트되었습니다.")
