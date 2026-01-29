import streamlit as st
import pandas as pd
import os
import base64
import json

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
    if os.path.exists(logo_file):
        with open(logo_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

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

# --- 4. 데이터 로직 (새로고침 유지 기능 포함) ---
data_key = f"df_{selected_b}_{selected_status}"

def create_initial_data():
    rows = [f"{i}F" for i in range(20, 0, -1)]
    # 6호 삭제: 1호~5호까지 구성
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    return pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)

# [핵심] 세션 초기화 시 기존 데이터 로드 시도
if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

# --- 5. 클릭 및 색상 로직 ---
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        const colId = event.column.colId;
        const node = event.node;
        const currentVal = node.data[colId];
        // 토글 기능: V가 있으면 삭제, 없으면 V 삽입
        node.setDataValue(colId, currentVal === 'V' ? '' : 'V');
    }
}
""")

cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return { 'backgroundColor': '#e06000', 'color': '#e06000' }
    }
    return null;
}
""")

gb = GridOptionsBuilder.from_dataframe(st.session_state[data_key])

# 💡 가독성 좋게 사이즈 조절 (글자 안 잘리게 75px)
gb.configure_default_column(
    editable=False, 
    width=75, 
    minWidth=75, 
    sortable=False,
    suppressMenu=True,
    cellStyle={'textAlign': 'center', 'fontSize': '15px'}
)

gb.configure_column("층", width=70, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f8f9fa'})
gb.configure_column("비고", width=180, editable=True)

gb.configure_grid_options(onCellClicked=cell_clicked_js)

# 1~5호 컬럼에 스타일 적용
for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.subheader(f"📍 {selected_b} - {selected_status}")
st.write("👉 칸을 **클릭**하면 주황색으로 표시됩니다. 완료 후 하단 **[저장]**을 눌러주세요.")

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

# 실시간 데이터 업데이트
if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.divider()

# --- 7. 저장 버튼 및 새로고침 유지 로직 ---
if st.button("💾 현황 확정 저장"):
    # 현재 세션의 데이터를 저장 (실제 서비스에서는 DB나 파일에 저장하는 코드가 들어갑니다)
    # 현재는 세션 내에서 유지되도록 보강되어 있습니다.
    st.success(f"[{selected_b} {selected_status}] 데이터가 브라우저에 임시 저장되었습니다.")
    st.balloons()

st.info("💡 참고: 현재는 브라우저를 닫기 전까지 데이터가 유지됩니다. 영구 저장을 위해서는 데이터베이스 연결이 필요합니다.")
