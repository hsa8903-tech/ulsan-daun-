import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("오류: requirements.txt에 'streamlit-aggrid'가 누락되었습니다.")

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 관리",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 로고 및 헤더 설정 ---
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file) and bin_file:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# 상단 고정 헤더
st.markdown(f"""
<div style="display: flex; align-items: center; padding: 10px; border-bottom: 2px solid #e06000; margin-bottom: 20px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 35px; margin-right: 15px;">
    <h2 style="margin: 0; color: #333; font-size: 1.5rem;">울산다운1차 작업 관리</h2>
</div>
""", unsafe_allow_html=True)

# --- 3. 사이드바 구성 ---
with st.sidebar:
    st.header("⚙️ 관리 설정")
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
    
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 현황 선택", status_list)
    
    st.divider()
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 4. 데이터 로직 ---
data_key = f"df_{selected_b}_{selected_status}"

def create_initial_data():
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "6호", "비고"]
    return pd.DataFrame([[str(r)] + [""]*7 for r in rows], columns=cols)

if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

# --- 5. 클릭 및 색상 로직 (토글 및 글자 보임 최적화) ---

# 클릭 시 V <-> 공백 무조건 전환 로직
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        const colId = event.column.colId;
        const node = event.node;
        const currentVal = node.data[colId];
        
        // 확실한 토글: V가 있으면 삭제, 없으면 V 삽입
        const newVal = (currentVal === 'V') ? '' : 'V';
        node.setDataValue(colId, newVal);
    }
}
""")

# 색상 및 텍스트 숨김 (주황색 칸은 글자가 안 보이게 배경색과 동일하게 처리)
cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return {
            'backgroundColor': '#e06000',
            'color': '#e06000',
            'textAlign': 'center'
        }
    }
    return {'textAlign': 'center'};
}
""")

gb = GridOptionsBuilder.from_dataframe(st.session_state[data_key])

# 💡 열 너비 조정: '...'이 나오지 않도록 최소 너비를 65로 조정 (절반 느낌 유지)
gb.configure_default_column(
    editable=False, 
    width=65, 
    minWidth=65, 
    sortable=False,
    suppressMenu=True,
    cellStyle={'textAlign': 'center'}
)

# 특정 열 예외 설정
gb.configure_column("층", width=70, minWidth=70, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'})
gb.configure_column("비고", width=150, minWidth=120, editable=True)

# 클릭 이벤트 등록
gb.configure_grid_options(onCellClicked=cell_clicked_js)

# 호수 컬럼들에 스타일 적용
for col in ["1호", "2호", "3호", "4호", "5호", "6호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.subheader(f"📍 {selected_b} - {selected_status}")
st.write("👉 칸을 **클릭**하면 색상이 바뀝니다. (한 번 더 클릭하면 취소)")

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

# 데이터 실시간 저장
if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.divider()
if st.button("💾 현황 확정 저장"):
    st.success(f"[{selected_b} {selected_status}] 데이터가 안전하게 저장되었습니다.")
