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
    st.error("오류: 'streamlit-aggrid' 라이브러리가 설치되어 있는지 확인해주세요.")

# --- 2. 데이터 영구 저장/로드 시스템 (F5 새로고침 완벽 대응) ---
DB_FILE = "installation_data.json"

def load_data_from_file():
    """앱 시작 시 파일에서 데이터를 읽어와 세션 상태에 로드"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in data.items():
                    # 저장된 JSON 데이터를 다시 데이터프레임으로 변환
                    st.session_state[key] = pd.read_json(value, orient='split')
        except Exception as e:
            st.error(f"데이터 로드 중 오류 발생: {e}")

def save_data_to_file():
    """현재 세션의 모든 데이터를 파일로 영구 기록"""
    save_dict = {}
    for key, value in st.session_state.items():
        if key.startswith("df_") and isinstance(value, pd.DataFrame):
            save_dict[key] = value.to_json(orient='split')
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(save_dict, f)

# 앱 실행 시 최초 1회만 파일에서 데이터 불러오기
if 'initialized' not in st.session_state:
    load_data_from_file()
    st.session_state['initialized'] = True

# --- 3. 헤더 및 디자인 설정 ---
logo_file = "Lynn BI.png"
def get_base64_of_bin_file(bin_file):
    if os.path.exists(logo_file):
        with open(logo_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

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

# --- 4. 상단 선택기 (동/공정 선택) ---
col_b, col_s = st.columns(2)
with col_b:
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
with col_s:
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 공정 선택", status_list)

# --- 5. 현재 동/공정 데이터 준비 ---
data_key = f"df_{selected_b}_{selected_status}"

# 해당 데이터가 세션에 없으면(처음 열면) 새로 생성
if data_key not in st.session_state:
    rows = [f"{i}F" for i in range(20, 0, -1)]
    # 비고 열을 제외한 층 + 1~5호 구성
    cols = ["층", "1호", "2호", "3호", "4호", "5호"]
    st.session_state[data_key] = pd.DataFrame([[str(r)] + [""]*5 for r in rows], columns=cols)

# --- 6. 저장 버튼 (파일 저장 시스템 작동) ---
if st.button(f"💾 {selected_b} {selected_status} 현황 저장", use_container_width=True):
    save_data_to_file()
    st.success("서버에 영구 저장되었습니다! 이제 새로고침(F5)을 해도 데이터가 안전합니다.")
    st.balloons()

# --- 7. 현황표(AgGrid) 설정 및 가독성 최적화 ---
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층') {
        const colId = event.column.colId;
        const node = event.node;
        const currentVal = node.data[colId];
        // 토글 기능: 값이 있으면 지우고, 없으면 V 삽입
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

# 현재 세션 데이터프레임 가져오기
current_df = st.session_state[data_key]
gb = GridOptionsBuilder.from_dataframe(current_df)

# 가독성 및 열 너비 설정 (비고 삭제 후 넓어진 사이즈 반영)
gb.configure_default_column(
    editable=False, 
    width=70,           # 호수별 너비 최적화
    minWidth=65, 
    sortable=False,
    suppressMenu=True,
    suppressMovable=True,
    cellStyle={'textAlign': 'center', 'fontSize': '15px'}
)

# 층수 열 고정 및 디자인
gb.configure_column("층", width=75, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'})

# 1~5호 컬럼 주황색 스타일 적용
for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

# 행 높이 및 클릭 이벤트 설정
gb.configure_grid_options(rowHeight=35, headerHeight=40, onCellClicked=cell_clicked_js)
grid_options = gb.build()

# --- 8. 현황표 출력 ---
grid_response = AgGrid(
    current_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{selected_b}_{selected_status}", # 동/공정별 고유 키로 충돌 방지
    height=720, 
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
)

# 표에서 변경된 내용을 즉시 세션 상태에 저장
if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.divider()
st.caption("우미건설(주) 울산다운1차 설비 시공 통합 관리 시스템")
