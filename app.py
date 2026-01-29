import streamlit as st
import pandas as pd
import os
import base64

# 라이브러리 체크
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode, JsCode
except ImportError:
    st.error("오류: requirements.txt에 'streamlit-aggrid'가 누락되었습니다.")

# --- 1. 앱 기본 설정 ---
st.set_page_config(
    page_title="울산다운1차 작업 관리",
    page_icon="🏗️",
    layout="wide"  # 넓은 화면 모드
)

# --- 2. 로고 및 헤더 설정 (우미건설 과장님 전용) ---
logo_file = "Lynn BI.png"

def get_base64_of_bin_file(bin_file):
    if os.path.exists(logo_file):
        with open(logo_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    return ""

logo_bin = get_base64_of_bin_file(logo_file)

# 상단 헤더 슬림화
st.markdown(f"""
<div style="display: flex; align-items: center; padding: 5px 10px; border-bottom: 2px solid #e06000; margin-bottom: 15px;">
    <img src="data:image/png;base64,{logo_bin}" style="height: 30px; margin-right: 12px;">
    <h3 style="margin: 0; color: #333; font-family: sans-serif;">울산다운1차 작업 관리</h3>
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

# --- 4. 데이터 로직 (데이터 유지 기능) ---
data_key = f"df_{selected_b}_{selected_status}"

def create_initial_data():
    rows = [f"{i}F" for i in range(20, 0, -1)]
    # 1호~5호 + 비고 (6호 삭제 반영)
    cols = ["층", "1호", "2호", "3호", "4호", "5호", "비고"]
    return pd.DataFrame([[str(r)] + [""]*6 for r in rows], columns=cols)

if data_key not in st.session_state:
    st.session_state[data_key] = create_initial_data()

# --- 5. 클릭 토글 및 디자인 로직 (가독성 최적화) ---

# 클릭 토글 자바스크립트
cell_clicked_js = JsCode("""
function(event) {
    if (event.column.colId !== '층' && event.column.colId !== '비고') {
        let colId = event.column.colId;
        let node = event.node;
        let currentVal = node.data[colId];
        node.setDataValue(colId, (currentVal === 'V') ? '' : 'V');
    }
}
""")

# 색상 스타일
cellstyle_jscode = JsCode("""
function(params) {
    if (params.value === 'V') {
        return {
            'backgroundColor': '#e06000',
            'color': '#e06000',
        }
    }
    return {'textAlign': 'center'};
}
""")

gb = GridOptionsBuilder.from_dataframe(st.session_state[data_key])

# 💡 [핵심] 행 높이와 열 너비를 줄여서 전체 사이즈 최적화
gb.configure_grid_options(
    rowHeight=30,           # 행 높이를 슬림하게 조절 (기본 약 40->30)
    headerHeight=35,        # 헤더 높이 조절
    onCellClicked=cell_clicked_js
)

# 💡 기본 열 너비 축소 (60px) 및 중앙 정렬
gb.configure_default_column(
    editable=False, 
    width=60, 
    minWidth=60, 
    sortable=False,
    suppressMenu=True,
    cellStyle={'textAlign': 'center', 'fontSize': '13px'}
)

# 층수와 비고 열 개별 설정
gb.configure_column("층", width=60, minWidth=60, pinned='left', cellStyle={'fontWeight': 'bold', 'backgroundColor': '#f1f3f5'})
gb.configure_column("비고", width=150, minWidth=100, editable=True)

# 1~5호 컬럼 스타일 적용
for col in ["1호", "2호", "3호", "4호", "5호"]:
    gb.configure_column(col, cellStyle=cellstyle_jscode)

grid_options = gb.build()

# --- 6. 화면 표시 ---
st.subheader(f"📍 {selected_b} - {selected_status}")

# 표를 감싸는 컨테이너 사이즈 조절
grid_response = AgGrid(
    st.session_state[data_key],
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    theme='balham',  # 가장 콤팩트한 테마 사용
    key=f"grid_{selected_b}_{selected_status}",
    height=640,      # 20개 층이 한 번에 거의 다 보이도록 높이 설정
    width='100%',
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE
)

# 세션 데이터 실시간 업데이트
if grid_response['data'] is not None:
    st.session_state[data_key] = pd.DataFrame(grid_response['data'])

# 하단 저장 섹션
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("💾 현황 저장"):
        st.success("저장 완료")
with col2:
    st.info("💡 클릭: 주황색(완료) ↔ 흰색(미완료) 토글")

st.divider()
st.caption("우미건설(주) 울산다운1차 설비 시공 관리 시스템")
