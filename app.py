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

# --- 2. 동별 라인 설정 로직 (핵심) ---
def get_lines_for_building(b_name):
    """동 이름을 입력받아 해당 동의 라인(호수) 리스트를 반환"""
    try:
        dong_num = int(b_name.replace("동", ""))
    except:
        return ["1호", "2호", "3호", "4호", "5호"] # 기본값

    # 1. 101~111동: 1~4호
    if 101 <= dong_num <= 111:
        return ["1호", "2호", "3호", "4호"]
    
    # 2. 112동: 1~3호
    elif dong_num == 112:
        return ["1호", "2호", "3호"]
    
    # 3. 113동: 1~5호
    elif dong_num == 113:
        return ["1호", "2호", "3호", "4호", "5호"]
    
    # 4. 114~116동: 1~4호
    elif 114 <= dong_num <= 116:
        return ["1호", "2호", "3호", "4호"]
    
    # 5. 117동: 1~5호
    elif dong_num == 117:
        return ["1호", "2호", "3호", "4호", "5호"]
    
    # 6. 118~120동: 1~4호
    elif 118 <= dong_num <= 120:
        return ["1호", "2호", "3호", "4호"]
    
    # 예외
    return ["1호", "2호", "3호", "4호", "5호"]

# --- 3. 데이터 영구 저장/로드 시스템 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "installation_data.json")

def create_initial_data(b_name):
    """선택된 동에 맞는 초기 데이터 생성"""
    target_cols = get_lines_for_building(b_name)
    rows = []
    for i in range(20, 0, -1):
        row_data = []
        for col in target_cols:
            # col은 "1호" 형태이므로 숫자만 추출
            ho_num = int(col.replace("호", ""))
            unit_number = f"{i}{ho_num:02d}호"
            row_data.append(unit_number)
        rows.append(row_data)
    return pd.DataFrame(rows, columns=target_cols)

def load_data_from_file():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    # 저장된 데이터 로드
                    df = pd.read_json(value, orient='split')
                    
                    # 💡 중요: 저장된 데이터가 있어도, 동 규격이 다르면(예: 4호동인데 5호데이터가 있으면) 열을 맞춤
                    # 키에서 동 이름 추출 (예: df_101동_실내기 -> 101동)
                    parts = key.split('_')
                    if len(parts) >= 2:
                        b_name = parts[1]
                        valid_cols = get_lines_for_building(b_name)
                        
                        # 1. '층', '비고' 삭제
                        if '층' in df.columns: df = df.drop(columns=['층'])
                        if '비고' in df.columns: df = df.drop(columns=['비고'])
                        
                        # 2. 유효한 컬럼만 남기기 (예: 1~5호 데이터 -> 1~4호로 자름)
                        # 데이터프레임의 컬럼 중 유효한 컬럼만 교집합으로 선택
                        existing_valid_cols = [c for c in df.columns if c in valid_cols]
                        df = df[existing_valid_cols]
                        
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

if 'initialized' not in st.session_state:
    load_data_from_file()
    st.session_state['initialized'] = True

# --- 4. 헤더 디자인 ---
st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    [data-testid="stHeader"] { visibility: hidden; }
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

# --- 5. 상단 선택기 ---
col_b, col_s = st.columns(2)
with col_b:
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
with col_s:
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 공정 선택", status_list)

# --- 6. 데이터 준비 및 검증 ---
data_key = f"df_{selected_b}_{selected_status}"
target_cols = get_lines_for_building(selected_b)

# 데이터가 없거나, 현재 동의 라인 수와 데이터의 열 개수가 다르면 재생성/보정
if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data(selected_b)
else:
    current_df = st.session_state[data_key]
    
    # 1. 층 열 제거 (혹시 남아있다면)
    if '층' in current_df.columns:
        current_df = current_df.drop(columns=['층'])
    
    # 2. 열 개수 불일치 확인 (예: 112동인데 5개 열이 있는 경우)
    # 현재 데이터의 컬럼 리스트와 타겟 컬럼 리스트가 다르면
    if list(current_df.columns) != target_cols:
        # 타겟 컬럼에 없는 열은 버리고, 모자란 열은 추가하는 방식보다
        # 안전하게 새로 생성하되 기존 데이터가 있으면 매핑하는 것이 좋으나,
        # 간단하게 '유효한 열만 남기고 없으면 생성' 처리
        
        # 만약 현재 데이터가 타겟보다 열이 많으면 (5개 -> 3개)
        if set(target_cols).issubset(set(current_df.columns)):
             st.session_state[data_key] = current_df[target_cols]
        else:
            # 아예 안 맞으면 초기화 (규격 변경 시 안전장치)
            st.session_state[data_key] = create_initial_data(selected_b)

# --- 7. 저장 버튼 ---
if st.button(f"💾 {selected_b} {selected_status} 현황 영구 저장", use_container_width=True):
    if save_data_to_file():
        st.success(f"✅ {selected_b} ({len(target_cols)}개 라인) 저장 완료")
        st.balloons()

# --- 8. 현황표(AgGrid) 설정 ---
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
    
    # 클릭 이벤트 (날짜 입력 및 복구)
    cell_clicked_js = JsCode("""
    function(event) {
        const colId = event.column.colId; 
        const node = event.node;
        const currentVal = String(node.data[colId]);
        
        if (currentVal.includes('/')) {
            // 복구 로직: 층 열이 없으므로 행 인덱스로 층 계산
            const floor = 20 - node.rowIndex; 
            let unit = colId.replace('호', '');
            if (unit.length < 2) unit = '0' + unit;
            
            node.setDataValue(colId, floor + unit + '호');
        } else {
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
            'fontSize': '15px'
        };
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

    # 라인 수에 따라 칸 너비 자동 조절 (라인이 적으면 넓게)
    col_count = len(target_cols)
    col_width = 110 # 기본값 (4~5라인)
    if col_count <= 3:
        col_width = 150 # 3라인 이하는 더 넓게
    
    gb.configure_default_column(
        editable=False, 
        width=col_width, 
        sortable=False,
        suppressMenu=True,
        suppressMovable=True
    )

    for col in target_cols:
        gb.configure_column(col, cellStyle=cellstyle_jscode)

    gb.configure_grid_options(rowHeight=40, headerHeight=45, onCellClicked=cell_clicked_js)
    grid_options = gb.build()

    grid_response = AgGrid(
        current_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        theme='balham',
        key=f"grid_{selected_b}_{selected_status}_{len(target_cols)}", # 키에 라인수를 넣어 충돌 방지
        height=750, 
        columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
    )

    if grid_response['data'] is not None:
        st.session_state[data_key] = pd.DataFrame(grid_response['data'])

except ImportError:
    st.error("'streamlit-aggrid' 설치가 필요합니다.")

st.caption(f"우미건설(주) 울산다운1차 - 현재 선택: {selected_b} ({len(target_cols)}개 라인)")
