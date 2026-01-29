import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# 라이브러리 체크 및 임포트
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("오력: requirements.txt에 'streamlit-aggrid'가 누락되었습니다.")

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 관리",
    page_icon="🏗️",
    layout="wide"
)

# --- 2. 로고 및 헤더 설정 ---
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(bin_file):
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# 상단 고정 헤더
st.markdown(f"""
<div style="display: flex; align-items: center; padding: 10px; border-bottom: 2px solid #e06000; margin-bottom: 20px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 40px; margin-right: 15px;">
    <h2 style="margin: 0; color: #333;">울산다운1차 작업 관리</h2>
</div>
""", unsafe_allow_html=True)

# --- 3. 사이드바 구성 (드롭다운 방식) ---
with st.sidebar:
    st.header("⚙️ 관리 설정")
    
    # 동 선택 목록
    b_list = [f"{i}동" for i in range(101, 121)]
    selected_b = st.selectbox("🏢 동 선택", b_list)
    
    # 현황 선택 목록 (요청하신 대로 드롭다운으로 변경)
    status_list = ["실내기", "실외기", "판넬", "시운전"]
    selected_status = st.selectbox("📋 현황 선택", status_list)
    
    st.divider()
    st.caption("우미건설(주) 울산다운1차 설비팀")

# --- 4. 데이터 로직 (오류 방지 강화) ---
data_key = f"df_{selected_b}_{selected_status}"

def create_initial_data():
    rows = [f"{i}F" for i in range(20, 0, -1)]
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    new_df = pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)
    return new_df

# 세션에 데이터가 없으면 초기화
if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

# 데이터프레임 복사본 사용 (AttributeError 방지)
current_df = st.session_state[data_key].copy()

# --- 5. 클릭 시 색상 변경 로직 ---
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        let currVal = event.value;
        event.node.setDataValue(event.column.colId, currVal === 'V' ? '' : 'V');
    }
}
""")

cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return {
            'color': '#e06000',
            'backgroundColor': '#e06000',
        }
    }
    return null;
};
""")

# GridOptions 설정
gb = GridOptionsBuilder.from_dataframe(current_df)
gb.configure_default_column(editable=False, minWidth=100, sortable=False)
gb.configure_grid_options(onCellClicked=cell_clicked_js)

for col in current_df.columns[1:-1]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.subheader(f"📍 {selected_b} - {selected_status} 공정 현황")
st.info("💡 해당 칸을 **클릭**하면 주황색으로 완료 표시됩니다.")

grid_response = AgGrid(
    current_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{data_key}", # 고유 키 부여로 충돌 방지
    height=550,
    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS
)

# 데이터 실시간 저장
if grid_response['data'] is not None:
    # AgGrid 결과를 다시 데이터프레임으로 변환하여 저장
    updated_df = pd.DataFrame(grid_response['data'])
    st.session_state[data_key] = updated_df

# 하단 저장 버튼
st.divider()
if st.button("💾 데이터 최종 확정"):
    st.success(f"[{selected_b} {selected_status}] 현황이 성공적으로 저장되었습니다.")
