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

# --- 2. 데이터 영구 저장/로드 시스템 (규격 갱신 로직 추가) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "installation_data.json")

def create_initial_data(building_name):
    """특정 동의 초기 호수 데이터를 생성"""
    rows = []
    for i in range(20, 0, -1):
        row_data = [f"{i}F"]
        for ho in range(1, 6):
            unit_number = f"{i}{ho:02d}호"
            row_data.append(unit_number)
        rows.append(row_data)
    cols = ["층", "1호", "2호", "3호", "4호", "5호"]
    return pd.DataFrame(rows, columns=cols)

def load_data_from_file():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    df = pd.read_json(value, orient='split')
                    # 만약 불러온 데이터에 '비고'가 있거나 규격이 다르면 초기화 대상에서 제외하고 갱신
                    st.session_state[key] = df
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

# 앱 시작 시 데이터 로드
if 'initialized' not in st.session_state:
    load_data_from_file()
    st.session_state['initialized'] = True

# --- 3. 헤더 디자인 및 격자선 CSS ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    [data-testid="stHeader"] { visibility: hidden; }
    /* 격자선 강화 및 텍스트 가운데 정렬 강제 */
    .ag-theme-balham .ag-ltr .ag-cell {
        border-right: 1px solid #d9dcde !important;
        border-bottom: 1px solid #d9dcde !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
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

# --- 5. 데이터 준비 (101동 및 기존 데이터 규격 자동 갱신) ---
data_key = f"df_{selected_b}_{selected_status}"

# 데이터가 없거나, 옛날 규격(열 개수가 다르거나 호수 정보가 없음)인 경우 새로 생성
if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data(selected_b)
else:
    # 101동 등이 옛날 방식일 경우 강제 업데이트 로직
    current_df = st.session_state[data_key]
    if "비고" in current_df.columns or len(current_df.columns) != 6:
        st.session_state[data_key] = create_initial_data(selected_b)
    elif not current_df.iloc[0, 1].endswith("호"): # 호수 텍스트가 없는 옛날 데이터인 경우
        st.session_state[data_key] = create_initial_data(selected_b)

# --- 6. 저장 버튼 ---
if st.button(f"💾 {selected_b} {selected_status} 현황 영구 저장", use_container_width=True):
    if save_data_to_file():
        st.success(f"✅ {selected_b} 현황이 안전하게 저장되었습니다.")
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

    # 💡 가운데 정렬(textAlign, display, justifyContent) 강화
    cellstyle_jscode = JsCode("""
    function(params) {
        let style = {
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'textAlign': 'center',
            'fontSize': '14px'
        };
        if (params.value && params.value.includes('✅')) {
            style['backgroundColor'] = '#e06000';
            style['color'] = 'white';
            style['fontWeight'] = 'bold';
        }
        return style;
    }
    """)

    current_df = st.session_state[data_key]
    gb = GridOptionsBuilder.from_dataframe(current_df)

    gb.configure_default_column(
        editable=False, 
        width=90, 
        sortable=False,
        suppressMenu=True,
        suppressMovable=True
    )

    gb.configure_column("층", width=70, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f0f0f0', 'textAlign': 'center'})
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
    st.error("'streamlit-aggrid' 설치가 필요합니다.")

st.caption(f"우미건설(주) 울산다운1차 설비팀 전용 - {selected_b} 작업 관리")
