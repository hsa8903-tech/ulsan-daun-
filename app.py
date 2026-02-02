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

# --- 2. 데이터 영구 저장/로드 시스템 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "installation_data.json")

def load_data_from_file():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    st.session_state[key] = pd.read_json(value, orient='split')
        except Exception as e:
            st.error(f"데이터 로드 오류: {e}")

def save_data_to_file():
    save_dict = {}
    for key, value in st.session_state.items():
        if key.startswith("df_") and isinstance(value, pd.DataFrame):
            save_dict[key] = value.to_json(orient='split')
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(save_dict, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}")
        return False

if 'db_loaded' not in st.session_state:
    load_data_from_file()
    st.session_state['db_loaded'] = True

# --- 3. 헤더 디자인 및 격자선 CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    [data-testid="stHeader"] { visibility: hidden; }
    /* 표의 격자선을 더 명확하게 만들기 위한 스타일 */
    .ag-theme-balham .ag-ltr .ag-cell {
        border-right: 1px solid #d9dcde !important;
        border-bottom: 1px solid #d9dcde !important;
    }
    .stButton > button { font-weight: bold; border-radius: 8px; height: 3em; background-color: #f0f2f6; }
</style>
<div style="padding: 10px 5px; border-bottom: 3px solid #e06000; margin-bottom: 15px;">
    <h3 style="margin: 0; color: #333;">🏗️ 울산다운1차 작업 현황표</h3>
</div>
""", unsafe_allow_html=True)

# --- 4. 상단 선택기 ---
col_b, col_s = st.columns(2)
with col_b:
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
with col_s:
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 공정 선택", status_list)

# --- 5. 데이터 준비 (호수 자동 기입 로직) ---
data_key = f"df_{selected_b}_{selected_status}"

def create_initial_data():
    # 20층부터 1층까지
    rows = []
    for i in range(20, 0, -1):
        row_data = [f"{i}F"]
        for ho in range(1, 6):
            # 호수 계산 (예: 15층 3호 -> 1503호)
            unit_number = f"{i}{ho:02d}호"
            row_data.append(unit_number)
        rows.append(row_data)
    
    cols = ["층", "1호", "2호", "3호", "4호", "5호"]
    return pd.DataFrame(rows, columns=cols)

if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

# --- 6. 저장 버튼 ---
if st.button(f"💾 {selected_b} {selected_status} 현황 영구 저장", use_container_width=True):
    if save_data_to_file():
        st.success(f"✅ {selected_b} 데이터가 안전하게 저장되었습니다.")
        st.balloons()

# --- 7. 현황표(AgGrid) 설정 ---
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
    
    # 클릭 시 호수 텍스트 뒤에 완료 표시 토글
    cell_clicked_js = JsCode("""
    function(event) {
        if (event.column.colId !== '층') {
            const colId = event.column.colId;
            const node = event.node;
            let val = node.data[colId];
            
            if (val.includes('✅')) {
                node.setDataValue(colId, val.replace(' ✅', ''));
            } else {
                node.setDataValue(colId, val + ' ✅');
            }
        }
    }
    """)

    # 완료 표시(✅)가 있으면 주황색 배경 적용
    cellstyle_jscode = JsCode("""
    function(params) {
        if (params.value && params.value.includes('✅')) {
            return { 'backgroundColor': '#e06000', 'color': 'white', 'fontWeight': 'bold' }
        }
        return {'textAlign': 'center'};
    }
    """)

    current_df = st.session_state[data_key]
    gb = GridOptionsBuilder.from_dataframe(current_df)

    gb.configure_default_column(
        editable=False, 
        width=85, 
        sortable=False,
        suppressMenu=True,
        suppressMovable=True,
        cellStyle={'textAlign': 'center', 'fontSize': '14px'}
    )

    gb.configure_column("층", width=70, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0'})
    for col in ["1호", "2호", "3호", "4호", "5호"]:
        gb.configure_column(col, cellStyle=cellstyle_jscode)

    # 행 높이를 40으로 설정하여 터치 및 가독성 향상
    gb.configure_grid_options(rowHeight=40, headerHeight=45, onCellClicked=cell_clicked_js)
    grid_options = gb.build()

    grid_response = AgGrid(
        current_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        theme='balham', # 격자선이 가장 잘 보이는 테마
        key=f"grid_{selected_b}_{selected_status}",
        height=750, 
        columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
    )

    if grid_response['data'] is not None:
        st.session_state[data_key] = pd.DataFrame(grid_response['data'])

except ImportError:
    st.error("'streamlit-aggrid' 라이브러리 설치가 필요합니다.")

st.caption(f"우미건설(주) 울산다운1차 설비팀 - {selected_b} 관리용")
