import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# 💡 오류 방지를 위한 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode
except ImportError:
    st.error("오류: 'streamlit-aggrid' 모듈을 찾을 수 없습니다. requirements.txt 파일을 확인해 주세요.")

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 현황표",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 로고 및 스타일 (기존 유지) ---
icon_file = "Lynn BI.png"
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# --- 3. 사이드바 (날씨 제거, 101동~120동 나열) ---
with st.sidebar:
    st.header("🏢 동별 현황")
    # 101동부터 120동까지 리스트
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
        <h2 style="margin: 0; color: #e06000; font-family: sans-serif;">Woomi Construction</h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style="background-color: #f8f9fa; padding: 10px; border-left: 5px solid #e06000; margin-bottom: 20px;">
    <h1 style='margin:0; font-size: 1.8rem; color: #333;'>울산다운1차 작업 현황표 ({selected_building})</h1>
</div>
""", unsafe_allow_html=True)

# --- 5. 데이터 로드 및 AgGrid 설정 ---
@st.cache_data
def create_default_data():
    # 20층부터 1층까지 5호 조합
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    return pd.DataFrame([[r] + [""]*6 for r in rows], columns=cols)

# 세션에 데이터 유지
if f'data_{selected_building}' not in st.session_state:
    st.session_state[f'data_{selected_building}'] = create_default_data()

df = st.session_state[f'data_{selected_building}']

# AgGrid 설정 (클릭 시 주황색 변경 로직 포함)
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True, minWidth=100)

# 셀 색상 변경 스크립트
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

# 변경 데이터 세션 저장
st.session_state[f'data_{selected_building}'] = grid_response['data']

if st.button("💾 현재 페이지 현황 저장"):
    st.success(f"{selected_building} 현황이 반영되었습니다.")
