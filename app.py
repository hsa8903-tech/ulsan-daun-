import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# 라이브러리 체크 및 임포트
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("requirements.txt에 streamlit-aggrid 추가가 필요합니다.")

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 관리",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 로고 및 헤더 설정 ---
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# 헤더 구성 (로고 + 고정 문구)
header_html = f"""
<div style="display: flex; align-items: center; padding: 10px; background-color: white; border-bottom: 2px solid #e06000; margin-bottom: 20px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 40px; margin-right: 15px;">
    <h2 style="margin: 0; color: #333; font-family: sans-serif;">울산다운1차 작업 관리</h2>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# --- 3. 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 관리 설정")
    
    # 동 선택 (101동~120동)
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
    
    # 현황 선택
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.radio("📋 현황 목록", status_list)
    
    st.divider()
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 4. 데이터 로직 ---
# 동 + 현황별로 고유한 키 생성
data_key = f"data_{selected_b}_{selected_status}"

@st.cache_data
def create_initial_data():
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    # 초기값은 모두 공백
    return pd.DataFrame([[r] + [""]*6 for r in rows], columns=cols)

if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

df = st.session_state[data_key]

# --- 5. 클릭 시 색상 변경 로직 (핵심 기능) ---
# JavaScript: 셀을 클릭하면 값이 "완료"로 바뀌고 색상이 변함
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        if (event.value === 'V') {
            event.node.setDataValue(event.column.colId, '');
        } else {
            event.node.setDataValue(event.column.colId, 'V');
        }
    }
}
""")

# 색상 조건부 서식
cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return {
            'color': '#e06000',
            'backgroundColor': '#e06000',
            'cursor': 'pointer'
        }
    }
    return {'cursor': 'pointer'};
};
""")

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=False, minWidth=100) # 직접 입력 방지
gb.configure_grid_options(onCellClicked=cell_clicked_js) # 클릭 이벤트 등록

for col in df.columns[1:-1]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.subheader(f"📍 {selected_b} - {selected_status} 공정 현황")
st.write("👉 **해당 동/호수 칸을 터치(클릭)하면 주황색으로 완료 표시됩니다.**")

grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.SELECTION_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=data_key, # 동/공정 변경 시 표를 새로 고침
    height=500
)

# 데이터 실시간 저장
if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.divider()
if st.button("💾 서버 현황 확정 저장"):
    st.success(f"{selected_b} {selected_status} 작업 현황이 안전하게 저장되었습니다.")
