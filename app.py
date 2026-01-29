import streamlit as st
import pandas as pd
import os
import base64
import json

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 관리",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded" # 💡 모바일에서 사이드바를 가급적 펼친 상태로 시작
)

# 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("오류: requirements.txt에 'streamlit-aggrid'가 누락되었습니다.")

# --- 2. 데이터 영구 저장/로드 함수 ---
DB_FILE = "installation_data.json"

def load_all_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_all_data(data_dict):
    save_data = {}
    for key, df in data_dict.items():
        if key.startswith("df_") and isinstance(df, pd.DataFrame):
            save_data[key] = df.to_json(orient='split')
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f)

# --- 3. 로고 및 헤더 설정 ---
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(logo_file):
        with open(logo_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# 모바일 가독성을 위한 CSS 보강
st.markdown(f"""
<style>
    .block-container {{ padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 0.5rem; padding-right: 0.5rem; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    /* 모바일에서 사이드바 화살표 강조 */
    [data-testid="stSidebarNav"] {{ margin-top: 20px; }}
</style>
<div style="display: flex; align-items: center; padding: 5px; border-bottom: 2px solid #e06000; margin-bottom: 10px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 25px; margin-right: 10px;">
    <h4 style="margin: 0; color: #333; font-size: 1.1rem;">울산다운1차 작업 관리</h4>
</div>
""", unsafe_allow_html=True)

# --- 4. 사이드바 (모바일에서는 왼쪽 화살표로 열림) ---
with st.sidebar:
    st.header("⚙️ 관리 설정")
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 현황 선택", status_list)
    
    st.divider()
    if st.button("💾 전체 현황 저장 (F5 대응)", use_container_width=True):
        save_all_data(st.session_state)
        st.success("저장 완료")
    st.write("📢 **폰에서 안 보이면 왼쪽 위 '>' 버튼을 누르세요.**")

# --- 5. 데이터 초기화 및 로드 ---
data_key = f"df_{selected_b}_{selected_status}"
if 'db_loaded' not in st.session_state:
    saved_db = load_all_data()
    for k, v in saved_db.items():
        st.session_state[k] = pd.read_json(v, orient='split')
    st.session_state['db_loaded'] = True

if data_key not in st.session_state:
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    st.session_state[data_key] = pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)

# --- 6. 클릭 토글 및 틀 고정(열 고정) 로직 ---
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        const colId = event.column.colId;
        const node = event.node;
        node.setDataValue(colId, node.data[colId] === 'V' ? '' : 'V');
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

# 💡 [핵심] 열 고정 및 사이즈 설정
gb.configure_default_column(
    editable=False, 
    width=40,           # 열 너비 슬림화
    minWidth=40, 
    sortable=False,
    suppressMenu=True,
    cellStyle={'textAlign': 'center', 'fontSize': '12px'}
)

# 💡 좌측 '층' 열 고정 (Pinned)
gb.configure_column("층", width=55, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'})
gb.configure_column("비고", width=120, editable=True)

# 💡 상단 헤더 고정은 AgGrid 기본 속성이므로 별도 설정 없이 유지됨
gb.configure_grid_options(
    rowHeight=30, 
    headerHeight=35, 
    onCellClicked=cell_clicked_js,
    suppressColumnVirtualisation=True # 모바일 스크롤 시 끊김 방지
)

for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 7. 화면 표시 ---
st.write(f"**📍 {selected_b} - {selected_status}**")

grid_response = AgGrid(
    st.session_state[data_key],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{selected_b}_{selected_status}",
    height=600, 
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
)

if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.caption("작업 완료 후 사이드바의 [전체 현황 저장]을 눌러주세요.")
