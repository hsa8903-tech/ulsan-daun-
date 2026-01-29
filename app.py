import streamlit as st
import pandas as pd
import os
import base64
import json

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 관리",
    page_icon="🏗️",
    layout="wide"
)

# 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("오류: requirements.txt에 'streamlit-aggrid'가 누락되었습니다.")

# --- 2. 데이터 영구 저장/로드 함수 (새로고침 대응) ---
DB_FILE = "installation_data.json"

def load_all_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_all_data(data_dict):
    # 세션 상태에 있는 모든 동/공정 데이터를 JSON 파일로 저장
    save_data = {}
    for key, df in data_dict.items():
        if key.startswith("df_") and isinstance(df, pd.DataFrame):
            save_data[key] = df.to_json(orient='split')
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f)

# --- 3. 로고 및 헤더 설정 ---
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# 상단 헤더 및 CSS (여백 최소화)
st.markdown(f"""
<style>
    .block-container {{ padding-top: 1rem; padding-bottom: 0rem; }}
    [data-testid="stHeader"] {{ visibility: hidden; }} /* 스트림릿 기본 상단 바 제거 */
</style>
<div style="display: flex; align-items: center; padding: 5px 10px; border-bottom: 2px solid #e06000; margin-bottom: 10px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 25px; margin-right: 12px;">
    <h3 style="margin: 0; color: #333;">울산다운1차 작업 관리</h3>
</div>
""", unsafe_allow_html=True)

# --- 4. 사이드바 (동/현황 선택) ---
with st.sidebar:
    st.header("⚙️ 관리 설정")
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 현황 선택", status_list)
    
    st.divider()
    # 저장 버튼 사이드바 배치 (접근성 향상)
    if st.button("💾 전체 현황 저장 (F5 대응)", use_container_width=True):
        save_all_data(st.session_state)
        st.success("서버 저장 완료 (새로고침 가능)")
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 5. 데이터 초기화 및 로드 ---
data_key = f"df_{selected_b}_{selected_status}"

# 앱 시작 시 파일에서 데이터 불러오기
if 'db_loaded' not in st.session_state:
    saved_db = load_all_data()
    for k, v in saved_db.items():
        st.session_state[k] = pd.read_json(v, orient='split')
    st.session_state['db_loaded'] = True

# 해당 동/공정 데이터가 없으면 새로 생성
if data_key not in st.session_state:
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    st.session_state[data_key] = pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)

# --- 6. 클릭 토글 및 디자인 최적화 ---
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        const colId = event.column.colId;
        const node = event.node;
        const currentVal = node.data[colId];
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

# 💡 [핵심] 너비를 기존의 절반 수준(35px)으로 축소
gb.configure_default_column(
    editable=False, 
    width=35,           # 기존 70px -> 35px로 축소
    minWidth=35, 
    sortable=False,
    suppressMenu=True,  # 상단 메뉴바 숨기기
    cellStyle={'textAlign': 'center', 'fontSize': '12px'}
)

# 층수와 비고는 글자가 보여야 하므로 너비 유지
gb.configure_column("층", width=55, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'})
gb.configure_column("비고", width=120, editable=True)

gb.configure_grid_options(rowHeight=28, headerHeight=30, onCellClicked=cell_clicked_js)

for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 7. 화면 표시 ---
st.write(f"**📍 {selected_b} - {selected_status} 현황**")

grid_response = AgGrid(
    st.session_state[data_key],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{selected_b}_{selected_status}",
    height=620, 
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
)

# 실시간 데이터 세션 업데이트
if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.caption("※ 작업 후 왼쪽 사이드바의 [전체 현황 저장]을 꼭 눌러주세요.")
