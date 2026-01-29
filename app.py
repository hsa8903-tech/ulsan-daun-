import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("오류: requirements.txt에 'streamlit-aggrid'가 누락되었습니다.")

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 관리",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 로고 및 헤더 설정 ---
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file) and bin_file:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

st.markdown(f"""
<div style="display: flex; align-items: center; padding: 10px; border-bottom: 2px solid #e06000; margin-bottom: 20px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 35px; margin-right: 15px;">
    <h2 style="margin: 0; color: #333; font-size: 1.5rem;">울산다운1차 작업 관리</h2>
</div>
""", unsafe_allow_html=True)

# --- 3. 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 관리 설정")
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
    
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 현황 선택", status_list)
    
    st.divider()
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 4. 데이터 로직 ---
data_key = f"df_{selected_b}_{selected_status}"

def create_initial_data():
    rows = [f"{i}F" for i in range(20, 0, -1)]
    # 호수를 더 많이 표시할 수 있도록 1~8호까지 구성 (필요시 조절)
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "6호", "비고"]
    return pd.DataFrame([[str(r)] + [""]*7 for r in rows], columns=cols)

if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

# --- 5. 클릭 및 색상 로직 (토글 기능 강화) ---

# 클릭하면 값이 있으면 지우고, 없으면 'V'를 넣는 자바스크립트
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        let colId = event.column.colId;
        let node = event.node;
        let currentVal = node.data[colId];
        
        if (currentVal === 'V') {
            node.setDataValue(colId, '');
        } else {
            node.setDataValue(colId, 'V');
        }
    }
}
""")

# 값이 'V'일 때만 주황색 배경 적용
cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return {
            'backgroundColor': '#e06000',
            'color': '#e06000'
        }
    }
    return null;
}
""")

gb = GridOptionsBuilder.from_dataframe(st.session_state[data_key])

# 💡 열 너비 절반 축소 (45px로 고정)
gb.configure_default_column(
    editable=False, 
    width=45, 
    minWidth=45, 
    maxWidth=50, 
    sortable=False,
    suppressMenu=True
)

# 층과 비고는 예외적으로 너비 조정
gb.configure_column("층", width=55, minWidth=55, pinned='left')
gb.configure_column("비고", width=120, minWidth=100, editable=True)

# 클릭 이벤트 등록
gb.configure_grid_options(onCellClicked=cell_clicked_js)

# 전 컬럼에 색상 스타일 적용
for col in ["1호", "2호", "3호", "4호", "5호", "6호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.subheader(f"📍 {selected_b} - {selected_status}")
st.write("👉 칸을 **클릭**하면 색상이 토글(주황색 ↔ 흰색)됩니다.")

grid_response = AgGrid(
    st.session_state[data_key],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{selected_b}_{selected_status}", # 동/현황별 유니크 키
    height=550,
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
)

# 데이터 실시간 세션 저장
if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.divider()
if st.button("💾 데이터 서버 확정 저장"):
    st.success(f"[{selected_b} {selected_status}] 현황 저장 완료")
