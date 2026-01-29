import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode
except ImportError:
    st.error("requirements.txt에 streamlit-aggrid를 추가해야 합니다.")

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 현황표",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 로고 및 스타일 (에러 방지를 위해 간단하게 수정) ---
icon_file = "Lynn BI.png"
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

# --- 3. 사이드바 (101동~120동) ---
with st.sidebar:
    st.header("🏢 동별 선택")
    building_list = [f"{i}동" for i in range(101, 121)]
    # 세션 상태를 사용하여 선택 값 유지
    if 'selected_b' not in st.session_state:
        st.session_state.selected_b = building_list[0]
    
    selected_building = st.selectbox("동을 선택하세요", building_list, key='building_selector')
    st.divider()
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 4. 메인 제목 ---
logo_bin = get_base64_of_bin_file(logo_file)
if logo_bin:
    st.image(Image.open(logo_file), width=200) # HTML 대신 스트림릿 표준 함수 사용 (에러 방지)
    st.subheader("Woomi Construction")

st.title(f"📍 {selected_building} 작업 현황표")
st.write("💡 칸에 내용을 입력하면 **주황색**으로 표시됩니다.")

# --- 5. 데이터 생성 및 AgGrid 설정 ---
@st.cache_data
def create_default_data(b_name):
    # 20층부터 1층까지 구성
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    return pd.DataFrame([[r] + [""]*6 for r in rows], columns=cols)

# 동이 바뀌면 데이터 새로 로드
if f'df_{selected_building}' not in st.session_state:
    st.session_state[f'df_{selected_building}'] = create_default_data(selected_building)

df = st.session_state[f'df_{selected_building}']

# AgGrid 설정
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True, minWidth=100)

# 셀 색상 변경 로직 (JavaScript) - 이 부분이 Error 62의 원인이 될 수 있어 간결하게 정리
cellsytle_jscode = """
function(params) {
    if (params.value && params.value.toString().trim() !== '' && params.column.colId !== '층') {
        return {
            'color': 'white',
            'backgroundColor': '#e06000',
            'fontWeight': 'bold'
        }
    }
}
"""
for col in df.columns[1:-1]:
    gb.configure_column(col, cellStyle={'styleConditions': [{'condition': 'params.value != ""', 'style': {'backgroundColor': '#e06000', 'color': 'white'}}]})

grid_options = gb.build()

# 표 출력 (테마를 깔끔하게 유지)
grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham', # 에러 발생 확률이 낮은 안정적인 테마
    key=f"grid_{selected_building}" # 동별로 고유 키 부여 (에러 해결 핵심)
)

# 데이터 저장
if grid_response['data'] is not None:
    st.session_state[f'df_{selected_building}'] = pd.DataFrame(grid_response['data'])
