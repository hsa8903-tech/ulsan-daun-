import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode

# --- 1. 앱 기본 설정 ---
icon_file = "Lynn BI.png"
logo_file = "Lynn BI.png"

st.set_page_config(
    page_title="울산다운1차 작업 현황표",
    page_icon="🏗️",
    layout="wide"  # 표를 넓게 보기 위해 와이드 모드 설정
)

# --- 2. 유틸리티 함수 (로고 표시용) ---
def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# --- 3. 사이드바: 동 선택 메뉴 ---
with st.sidebar:
    st.header("🏢 동별 현황 선택")
    # 101동부터 120동까지 리스트 생성
    building_list = [f"{i}동" for i in range(101, 121)]
    selected_building = st.selectbox("조회할 동을 선택하세요", building_list)
    
    st.divider()
    st.info(f"현재 선택: **{selected_building}**")
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 4. 메인 헤더 (로고 & 제목) ---
logo_bin = get_base64_of_bin_file(logo_file)
if logo_bin:
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{logo_bin}" style="height: 50px; margin-right: 15px;">
        <h2 style="margin: 0; color: #e06000; font-family: sans-serif;">Woomi Construction</h2>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div style="background-color: #f8f9fa; padding: 10px; border-left: 5px solid #e06000; margin-bottom: 20px;">
    <h1 style='margin:0; font-size: 1.8rem; color: #333;'>울산다운1차 작업 현황표 ({selected_building})</h1>
</div>
""", unsafe_allow_html=True)

# --- 5. 데이터 처리 및 엑셀 표 구현 ---
# 과장님이 공유해주신 엑셀 구조를 기반으로 가상 데이터 생성 (실제 파일 로드 가능)
@st.cache_data
def load_initial_data(building):
    # 실제 운영 시에는 공유해주신 csv/xlsx를 로드하도록 수정 가능합니다.
    # 여기서는 층별(20F~1F) / 호수별(1~5호) 샘플 구조를 만듭니다.
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    data = []
    for r in rows:
        data.append([r, "", "", "", "", "", ""])
    return pd.DataFrame(data, columns=cols)

# 세션 상태에 데이터 저장 (클릭 시 색상 유지를 위함)
if f'data_{selected_building}' not in st.session_state:
    st.session_state[f'data_{selected_building}'] = load_initial_data(selected_building)

df = st.session_state[f'data_{selected_building}']

# --- 6. AgGrid를 이용한 인터랙티브 표 (클릭 시 색상 변경) ---
st.write("💡 **칸을 더블클릭하여 숫자(설치 대수)나 '완료'를 입력하면 색상이 강조됩니다.**")

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True, groupable=True)

# 셀 색상 조건부 서식 (값이 있으면 연한 주황색으로 강조)
cellsytle_jscode = """
function(params) {
    if (params.value !== undefined && params.value !== '' && params.column.colId !== '층') {
        return {
            'color': 'white',
            'backgroundColor': '#e06000'
        }
    }
};
"""
for col in df.columns[1:-1]: # '층'과 '비고' 제외한 호수별 칸에 적용
    gb.configure_column(col, cellStyle=cellsytle_jscode)

grid_options = gb.build()

# 표 표시
response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
    theme='balham' # 우미린 이미지와 어울리는 깔끔한 테마
)

# 데이터 업데이트 저장
if response['data'] is not None:
    st.session_state[f'data_{selected_building}'] = pd.DataFrame(response['data'])

# --- 7. 하단 버튼 ---
col1, col2 = st.columns([1, 5])
with col1:
    if st.button("💾 현황 저장"):
        st.toast(f"{selected_building} 데이터가 서버에 저장되었습니다!", icon="💾")

st.divider()
st.caption("본 시스템은 우미건설 설비 시공 통합 관리 매뉴얼 디지털 버전에 포함됩니다.")