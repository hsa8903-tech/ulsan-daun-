import streamlit as st
import pandas as pd
import os
import base64
import json

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 현황표",
    page_icon="🏗️",
    layout="wide"
)

# 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("오류: 'streamlit-aggrid' 라이브러리를 설치해야 합니다.")

# --- 2. 데이터 영구 저장/로드 함수 ---
DB_FILE = "installation_data.json"

def load_all_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_all_data(data_dict):
    save_data = {}
    for key, df in data_dict.items():
        if key.startswith("df_") and isinstance(df, pd.DataFrame):
            save_data[key] = df.to_json(orient='split')
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(save_data, f)

# --- 3. 로고 및 헤더 설정 (명칭 수정 반영) ---
logo_file = "Lynn BI.png"
def get_base64_of_bin_file(bin_file):
    if os.path.exists(logo_file):
        with open(logo_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# CSS: 가독성 및 디자인 최적화
st.markdown(f"""
<style>
    .block-container {{ padding-top: 0.5rem; }}
    [data-testid="stHeader"] {{ visibility: hidden; }}
    .stSelectbox {{ margin-bottom: -15px; }}
    .stButton > button {{ font-weight: bold; border-radius: 8px; }}
</style>
<div style="display: flex; align-items: center; padding: 10px 5px; border-bottom: 2px solid #e06000; margin-bottom: 10px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 28px; margin-right: 12px;">
    <h3 style="margin: 0; color: #333; font-size: 1.3rem; font-weight: 800;">울산다운1차 작업 현황표</h3>
</div>
""", unsafe_allow_html=True)

# --- 4. 상단 선택기 (메인 화면 배치) ---
col_b, col_s = st.columns(2)
with col_b:
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
with col_s:
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 공정 선택", status_list)

# --- 5. 데이터 로드 및 초기화 ---
data_key = f"df_{selected_b}_{selected_status}"
if 'db_loaded' not in st.session_state:
    saved_db = load_all_data()
    for k, v in saved_db.items():
        try:
            st.session_state[k] = pd.read_json(v, orient='split')
        except:
            pass
    st.session_state['db_loaded'] = True

if data_key not in st.session_state:
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    st.session_state[data_key] = pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)

# --- 6. 저장 버튼 ---
if st.button(f"💾 {selected_b} {selected_status} 현황 저장", use_container_width=True):
    save_all_data(st.session_state)
    st.toast("서버에 안전하게 저장되었습니다!", icon="✅")

# --- 7. 표 설정 (AgGrid 가독성 최적화) ---
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        const colId = event.column.colId;
        const node = event.node;
        const currentVal = node.data[colId];
        node.setDataValue(colId, currentVal === 'V' ? '' : 'V');
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

# 순서 고정
current_df = st.session_state[data_key][["층", "1호", "2호", "3호", "4호", "5호", "비고"]]
gb = GridOptionsBuilder.from_dataframe(current_df)

# 💡 [가독성 포인트] 열 너비와 행 높이 조절
gb.configure_default_column(
    editable=False, 
    width=55,           # 1~5호 열 너비 (글자 안 잘리게 조정)
    minWidth=55, 
    sortable=False,
    suppressMenu=True,
    suppressMovable=True,
    cellStyle={'textAlign': 'center', 'fontSize': '14px'}
)

# 층/비고 열 개별 설정
gb.configure_column("층", width=65, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'})
gb.configure_column("비고", width=150, editable=True)

# 💡 행 높이를 35로 키워 터치 편의성 증대
gb.configure_grid_options(rowHeight=35, headerHeight=40, onCellClicked=cell_clicked_js)

for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 8. 현황표 출력 ---
AgGrid(
    current_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{selected_b}_{selected_status}",
    height=680, 
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
)

# 데이터 실시간 업데이트 반영
st.session_state[data_key] = current_df

st.caption("우미건설(주) 울산다운1차 설비 시공 통합 관리 시스템")
