import streamlit as st
import pandas as pd
import os
import base64
from PIL import Image

# 라이브러리 체크 및 임포트
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
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    return pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)

if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

current_df = st.session_state[data_key].copy()

# --- 5. 클릭 시 색상 토글 및 너비 조절 로직 ---
# 클릭 시 V <-> 공백 전환 (토글 기능)
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        let currVal = event.value;
        // 값이 있으면 지우고(흰색), 없으면 V(주황색) 채우기
        event.node.setDataValue(event.column.colId, (currVal === 'V' || currVal === 'v') ? '' : 'V');
    }
}
""")

cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return {
            'backgroundColor': '#e06000',
            'color': '#e06000'
        }
    }
    return null;
};
""")

gb = GridOptionsBuilder.from_dataframe(current_df)

# 열 너비 설정: 기본 너비를 절반(50)으로 줄임
gb.configure_default_column(editable=False, minWidth=50, width=50, sortable=False)
gb.configure_grid_options(onCellClicked=cell_clicked_js)

# 층 컬럼은 글자가 보여야 하므로 너비를 조금 더 유지
gb.configure_column("층", width=60, minWidth=60)
gb.configure_column("비고", width=150, minWidth=100, editable=True)

for col in current_df.columns[1:-1]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.subheader(f"📍 {selected_b} - {selected_status} 공정 현황")
st.info("💡 클릭 시 **주황색(완료)** 표시, 다시 클릭하면 **흰색(취소)**으로 바뀝니다.")

grid_response = AgGrid(
    current_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',
    key=f"grid_{data_key}",
    height=550,
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE  # 설정한 너비 강제 적용
)

if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

st.divider()
if st.button("💾 데이터 최종 확정"):
    st.success(f"[{selected_b} {selected_status}] 현황이 성공적으로 반영되었습니다.")
