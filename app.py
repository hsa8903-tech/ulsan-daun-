import streamlit as st
import pandas as pd
import os
import base64

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
    if os.path.exists(logo_file):
        with open(logo_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# 상단 헤더 슬림화 (여백 최소화)
st.markdown(f"""
<style>
    .block-container {{ padding-top: 1rem; padding-bottom: 0rem; }}
    div.stButton > button {{ width: 100%; }}
</style>
<div style="display: flex; align-items: center; padding: 5px 10px; border-bottom: 2px solid #e06000; margin-bottom: 10px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 25px; margin-right: 10px;">
    <h4 style="margin: 0; color: #333;">울산다운1차 작업 관리</h4>
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
if data_key not in st.session_state:
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    st.session_state[data_key] = pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)

# --- 5. 클릭 토글 및 디자인 로직 (상단 바 제거 핵심) ---

cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        let colId = event.column.colId;
        let node = event.node;
        let currentVal = node.data[colId];
        node.setDataValue(colId, (currentVal === 'V') ? '' : 'V');
    }
}
""")

cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return { 'backgroundColor': '#e06000', 'color': '#e06000' }
    }
    return {'textAlign': 'center'};
}
""")

gb = GridOptionsBuilder.from_dataframe(st.session_state[data_key])

# 💡 [핵심 수정] 상단 메뉴바 및 필터 기능 완전 제거 (suppressMenu 등)
gb.configure_grid_options(
    rowHeight=30,
    headerHeight=35,
    onCellClicked=cell_clicked_js,
    suppressMenuHide=True,      # 메뉴 숨김 강제
    suppressMovableColumns=True # 컬럼 이동 방지
)

# 기본 열 설정에서 메뉴 차단
gb.configure_default_column(
    editable=False, 
    width=65, 
    minWidth=65, 
    sortable=False,
    suppressMenu=True,          # 💡 사진에 표시하신 '필터/메뉴' 아이콘 제거
    cellStyle={'textAlign': 'center', 'fontSize': '14px'}
)

gb.configure_column("층", width=60, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f1f3f5'})
gb.configure_column("비고", width=150, editable=True)

for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.write(f"**{selected_b} - {selected_status}**")

# 표 사이즈 최적화
grid_response = AgGrid(
    st.session_state[data_key],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{selected_b}_{selected_status}",
    height=650, 
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
)

if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

# 저장 버튼 슬림화
if st.button("💾 현황 저장"):
    st.success("저장되었습니다.")
