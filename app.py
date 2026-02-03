import streamlit as st
import pandas as pd
import os
import json
import datetime

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 현황표",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 데이터 영구 저장/로드 시스템 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "installation_data.json")

def create_initial_data(building_name):
    """'층' 열 없이 1~5호만 있는 초기 데이터 생성"""
    rows = []
    # 20층부터 1층까지 생성
    for i in range(20, 0, -1):
        row_data = []
        for ho in range(1, 6):
            unit_number = f"{i}{ho:02d}호"
            row_data.append(unit_number)
        rows.append(row_data)
    cols = ["1호", "2호", "3호", "4호", "5호"]
    return pd.DataFrame(rows, columns=cols)

def load_data_from_file():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    df = pd.read_json(value, orient='split')
                    # 기존 데이터에 '층'이나 '비고'가 있다면 삭제하여 규격 통일
                    if '층' in df.columns:
                        df = df.drop(columns=['층'])
                    if '비고' in df.columns:
                        df = df.drop(columns=['비고'])
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

# --- 3. 헤더 디자인 ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    [data-testid="stHeader"] { visibility: hidden; }
    /* 격자선 강화 및 텍스트 가운데 정렬 */
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

# --- 5. 데이터 준비 ---
data_key = f"df_{selected_b}_{selected_status}"

# 데이터가 없거나 열 개수가 5개가 아니면(옛날 규격이면) 초기화
if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data(selected_b)
else:
    current_df = st.session_state[data_key]
    if len(current_df.columns) != 5: # 열이 5개(1~5호)가 아니면 재생성
        st.session_state[data_key] = create_initial_data(selected_b)

# --- 6. 저장 버튼 ---
if st.button(f"💾 {selected_b} {selected_status} 현황 영구 저장", use_container_width=True):
    if save_data_to_file():
        st.success(f"✅ {selected_b} 현황이 안전하게 저장되었습니다.")
        st.balloons()

# --- 7. 현황표(AgGrid) 설정 ---
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
    
    # 💡 [핵심 수정] 층 열 없이도 원래 호수 계산하는 로직
    cell_clicked_js = JsCode("""
    function(event) {
        const colId = event.column.colId; // 예: "1호"
        const node = event.node;
        const currentVal = String(node.data[colId]);
        
        // 날짜(슬래시 / 포함)인지 확인
        if (currentVal.includes('/')) {
            // 날짜라면 -> 원래 호수로 복구
            // 층 열이 없으므로 행 인덱스로 층 계산 (Row 0 = 20F, Row 19 = 1F)
            const floor = 20 - node.rowIndex; 
            
            let unit = colId.replace('호', '');
            if (unit.length < 2) unit = '0' + unit; // 1 -> 01
            
            node.setDataValue(colId, floor + unit + '호');
        } else {
            // 호수라면 -> 오늘 날짜 입력 (M/D)
            const today = new Date();
            const month = today.getMonth() + 1;
            const day = today.getDate();
            const dateStr = month + '/' + day;
            
            node.setDataValue(colId, dateStr);
        }
    }
    """)

    cellstyle_jscode = JsCode("""
    function(params) {
        let style = {
            'display': 'flex',
            'alignItems': 'center',
            'justifyContent': 'center',
            'textAlign': 'center',
            'fontSize': '15px' // 글자 크기 약간 확대
        };
        // 날짜(슬래시 포함)면 주황색
        if (params.value && String(params.value).includes('/')) {
            style['backgroundColor'] = '#e06000';
            style['color'] = 'white';
            style['fontWeight'] = 'bold';
        }
        return style;
    }
    """)

    current_df = st.session_state[data_key]
    gb = GridOptionsBuilder.from_dataframe(current_df)

    # 층 열이 빠졌으므로 너비를 더 넓게(110px) 설정
    gb.configure_default_column(
        editable=False, 
        width=110, 
        sortable=False,
        suppressMenu=True,
        suppressMovable=True
    )

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

st.caption(f"우미건설(주) 울산다운1차 설비팀 전용")
