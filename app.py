import streamlit as st
import pandas as pd
import os
import json

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 현황표",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 데이터 영구 저장/로드 시스템 (강화 버전) ---
# 현재 파일이 있는 디렉토리에 저장하여 경로 유실 방지
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "installation_data.json")

def load_data_from_file():
    """서버 파일에서 데이터를 읽어와 세션 상태에 로드"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    # JSON 문자열을 데이터프레임으로 복구
                    st.session_state[key] = pd.read_json(value, orient='split')
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")

def save_data_to_file():
    """현재 세션의 데이터를 JSON 파일로 영구 저장"""
    save_dict = {}
    for key, value in st.session_state.items():
        if key.startswith("df_") and isinstance(value, pd.DataFrame):
            save_dict[key] = value.to_json(orient='split')
    
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(save_dict, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"데이터 저장 중 오류 발생: {e}")
        return False

# 앱 실행 시 파일에서 데이터 로드 (세션이 비어있을 때만)
if 'db_loaded' not in st.session_state:
    load_data_from_file()
    st.session_state['db_loaded'] = True

# --- 3. 헤더 디자인 ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    [data-testid="stHeader"] { visibility: hidden; }
    .stButton > button { font-weight: bold; border-radius: 8px; height: 3em; }
</style>
<div style="padding: 10px 5px; border-bottom: 3px solid #e06000; margin-bottom: 20px;">
    <h3 style="margin: 0; color: #333;">🏗️ 울산다운1차 작업 현황표</h3>
</div>
""", unsafe_allow_html=True)

# --- 4. 상단 선택기 (동/공정 선택) ---
col_b, col_s = st.columns(2)
with col_b:
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
with col_s:
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 공정 선택", status_list)

# --- 5. 데이터 준비 (비고 열 삭제) ---
data_key = f"df_{selected_b}_{selected_status}"

if data_key not in st.session_state:
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호"]
    st.session_state[data_key] = pd.DataFrame([[str(r)] + [""]*5 for r in rows], columns=cols)

# --- 6. 저장 버튼 (파일 시스템에 즉시 기록) ---
if st.button(f"💾 {selected_b} {selected_status} 현황 영구 저장", use_container_width=True):
    if save_data_to_file():
        st.success("✅ 파일에 안전하게 저장되었습니다. 이제 며칠 뒤에 접속해도 유지됩니다.")
        st.balloons()

# --- 7. 현황표(AgGrid) 라이브러리 설정 ---
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
    
    cell_clicked_js = JsCode("""
    function(event) {
        if (event.column.colId !== '층') {
            const colId = event.column.colId;
            const node = event.node;
            node.setDataValue(colId, node.data[colId] === 'V' ? '' : 'V');
        }
    }
    """)

    cellstyle_jscode = JsCode("""
    function(params) {
        if (params.value === 'V') {
            return { 'backgroundColor': '#e06000', 'color': 'white' }
        }
        return {'textAlign': 'center'};
    }
    """)

    current_df = st.session_state[data_key]
    gb = GridOptionsBuilder.from_dataframe(current_df)

    gb.configure_default_column(
        editable=False, 
        width=70, 
        sortable=False,
        suppressMenu=True,
        suppressMovable=True,
        cellStyle={'textAlign': 'center', 'fontSize': '15px'}
    )

    gb.configure_column("층", width=80, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0'})
    for col in ["1호", "2호", "3호", "4호", "5호"]:
        gb.configure_column(col, cellStyle=cellstyle_jscode)

    gb.configure_grid_options(rowHeight=40, headerHeight=45, onCellClicked=cell_clicked_js)
    grid_options = gb.build()

    grid_response = AgGrid(
        current_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        theme='balham',
        key=f"grid_{selected_b}_{selected_status}",
        height=750, 
        columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
    )

    if grid_response['data'] is not None:
        st.session_state[data_key] = pd.DataFrame(grid_response['data'])

except ImportError:
    st.error("현황표 표시를 위해 'streamlit-aggrid' 설치가 필요합니다.")

st.caption("우미건설(주) 울산다운1차 설비팀")
