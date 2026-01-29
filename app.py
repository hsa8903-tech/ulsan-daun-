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
    initial_sidebar_state="collapsed" # 모바일에서는 버튼으로 제어하기 위해 기본은 닫음
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

# --- 3. 헤더 및 모바일 전용 버튼 ---
logo_file = "Lynn BI.png"
def get_base64_of_bin_file(bin_file):
    if os.path.exists(logo_file):
        with open(logo_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# CSS: 모바일에서 상단 버튼 강조
st.markdown(f"""
<style>
    .block-container {{ padding-top: 0rem; padding-bottom: 0rem; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    /* 모바일에서 설정창 열기 버튼 스타일 */
    .mobile-btn {{
        background-color: #e06000;
        color: white;
        padding: 8px 15px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 10px;
        font-weight: bold;
        cursor: pointer;
    }}
</style>
""", unsafe_allow_html=True)

# 최상단 로고 바
st.markdown(f"""
<div style="display: flex; align-items: center; padding: 10px 5px; border-bottom: 2px solid #e06000;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 25px; margin-right: 10px;">
    <h4 style="margin: 0; color: #333; font-size: 1.1rem;">울산다운1차 작업 관리</h4>
</div>
""", unsafe_allow_html=True)

# 💡 [핵심] 모바일 사용자를 위한 사이드바 호출 가이드
st.info("💡 동/현황 변경은 왼쪽 상단의 **'>' 화살표** 또는 **사이드바**를 열어주세요.")

# --- 4. 사이드바 구성 ---
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
    st.caption("우미건설(주) 울산다운1차 설비팀")

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

# --- 6. 클릭 토글 및 열 순서 고정 로직 ---
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

# 💡 [핵심] 컬럼 정의 시 고정 순서 및 이동 방지 설정
gb = GridOptionsBuilder.from_dataframe(st.session_state[data_key])

gb.configure_default_column(
    editable=False, 
    width=42, 
    minWidth=42, 
    sortable=False,
    suppressMenu=True,
    suppressMovable=True, # 💡 열 이동 금지 (순서 고정)
    cellStyle={'textAlign': 'center', 'fontSize': '12px'}
)

# 층수 고정
gb.configure_column("층", width=55, pinned='left', suppressMovable=True, cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'})
# 호수 순서대로 개별 설정 (순서 강제)
for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode, suppressMovable=True)
# 비고열 설정
gb.configure_column("비고", width=120, editable=True, suppressMovable=True)

gb.configure_grid_options(
    rowHeight=30, 
    headerHeight=35, 
    onCellClicked=cell_clicked_js,
    suppressColumnVirtualisation=True
)

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
