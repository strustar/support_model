import streamlit as st
import numpy as np
import pyvista as pv
from stpyvista import stpyvista
import hashlib
import warnings
import platform
from pyvista.core.errors import PyVistaFutureWarning
import os

# --- 페이지 설정 ---
st.set_page_config(page_title="동바리 구조 시각화", layout="wide")
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=PyVistaFutureWarning)

# 환경별 설정
if platform.system() == 'Linux':  # Streamlit Cloud 환경
    os.environ["PYVISTA_OFF_SCREEN"] = "true"
    os.environ["PYVISTA_USE_IPYVTK"] = "true"
    os.environ["DISPLAY"] = ":99"
    os.environ["MESA_GL_VERSION_OVERRIDE"] = "3.3"
    pv.OFF_SCREEN = True
    pv.start_xvfb()
else:  # 로컬 Windows 환경
    plotter = pv.Plotter(off_screen=True)
    pv.OFF_SCREEN = False


st.title("🏗️ 3D 동바리 구조 시각화 (PyVista)")
st.write("간격 데이터를 누적해 중공 원형 단면 동바리 구조 생성함")

# --- 사이드바 최적화 ---
with st.sidebar:
    st.header("1️⃣ 간격 입력")
    x_str = st.text_area("가로 간격 (mm)", "610, 1219, 1524", height=70, key="x_in")
    y_str = st.text_area("세로 간격 (mm)", "610, 914, 1219, 1524", height=70, key="y_in")
    z_str = st.text_area("높이 간격 (mm)", "432, 863, 1291, 1725, 1725", height=70, key="z_in")
    
    st.header("2️⃣ 부재 스타일")
    radius   = st.slider("파이프 반경 (mm)", 10, 200, 60, key="r_in")
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        v_color = st.color_picker("🔵 수직 색상", "#4169E1", key="c_v")
        v_opac  = st.slider("수직 투명도", 0.1, 0.7, 1.0, key="o_v")
    with c2:
        x_color = st.color_picker("🔴 가로 색상", "#DC143C", key="c_x")
        x_opac  = st.slider("가로 투명도", 0.1, 0.7, 1.0, key="o_x")
    with c3:
        y_color = st.color_picker("🟢 세로 색상", "#228B22", key="c_y")
        y_opac  = st.slider("세로 투명도", 0.1, 0.7, 1.0, key="o_y")
        
    st.header("3️⃣ 뷰 설정")
    col1, col2 = st.columns(2, gap="large")
    with col1:
        proj = st.radio("투영 모드", ["Perspective", "Orthographic"], index=0, key="proj")
    with col2:
        view = st.selectbox("카메라 뷰", ["Isometric", "Top", "Front", "Right"], index=0, key="view")

# --- 데이터 파싱 & 누적합 계산 ---
valid = False
try:
    xi = np.array([float(v) for v in x_str.split(",") if v.strip()])
    yi = np.array([float(v) for v in y_str.split(",") if v.strip()])
    zi = np.array([float(v) for v in z_str.split(",") if v.strip()])
    if xi.size and yi.size and zi.size:
        x_pos = np.concatenate(([0], np.cumsum(xi)))
        y_pos = np.concatenate(([0], np.cumsum(yi)))
        z_pos = np.concatenate(([0], np.cumsum(zi)))
        valid = True
    else:
        st.warning("⚠️ 모든 간격 입력 필요함")
except:
    st.error("❌ 입력 형식 오류: 숫자와 쉼표만 사용해야 함")

# # --- 메트릭 표시 ---
# if valid:
#     m1, m2, m3 = st.columns(3)
#     with m1:
#         st.metric("가로 포인트", f"{len(x_pos)}개", f"총길이 {x_pos[-1]:.0f}mm")
#     with m2:
#         st.metric("세로 포인트", f"{len(y_pos)}개", f"총길이 {y_pos[-1]:.0f}mm")
#     with m3:
#         st.metric("높이 레벨", f"{len(z_pos)}개", f"총높이 {z_pos[-1]:.0f}mm")

# --- 3D 모델 생성 & 렌더링 ---
if valid:
    # 입력 변경 시마다 갱신되는 고유 키
    key_str = f"{x_str}{y_str}{z_str}{radius}{v_color}{x_color}{y_color}{v_opac}{x_opac}{y_opac}{proj}{view}"
    ukey = hashlib.md5(key_str.encode()).hexdigest()[:8]
    
    pl = pv.Plotter(window_size=[1200,1200])
    # 투영 모드 설정
    if proj == "Orthographic":
        pl.enable_parallel_projection()
    else:
        pl.disable_parallel_projection()

    # 수직 부재
    for x in x_pos:
        for y in y_pos:
            tube = pv.Tube(pointa=[x,y,0], pointb=[x,y,z_pos[-1]],
                           radius=radius)
            pl.add_mesh(tube, color=v_color, opacity=v_opac, smooth_shading=True)
    # 가로 부재 (X축)
    for z in z_pos:
        for y in y_pos:
            for i in range(len(x_pos)-1):
                tube = pv.Tube(pointa=[x_pos[i],y,z],
                               pointb=[x_pos[i+1],y,z],
                               radius=radius*0.8)
                pl.add_mesh(tube, color=x_color, opacity=x_opac, smooth_shading=True)
    # 세로 부재 (Y축)
    for z in z_pos:
        for x in x_pos:
            for i in range(len(y_pos)-1):
                tube = pv.Tube(pointa=[x,y_pos[i],z],
                               pointb=[x,y_pos[i+1],z],
                               radius=radius*0.8)
                pl.add_mesh(tube, color=y_color, opacity=y_opac, smooth_shading=True)

    # 카메라 뷰 선택
    if view == "Isometric":
        pl.view_isometric()
    elif view == "Top":
        pl.view_xy()
    elif view == "Front":
        pl.view_xz()
    elif view == "Right":
        pl.view_yz()

    pl.background_color = 'white'
    pl.add_axes(xlabel='X (mm)', ylabel='Y (mm)', zlabel='Z (mm)')
    

    # # 색상 범례
    # st.markdown("### 🎨 색상 & 투명도 범례")
    # lc1, lc2, lc3 = st.columns(3)
    # with lc1:
    #     st.markdown(f"<span style='color:{v_color}'>█</span> 수직 (투명도 {v_opac:.1f})", unsafe_allow_html=True)
    # with lc2:
    #     st.markdown(f"<span style='color:{x_color}'>█</span> 가로 (투명도 {x_opac:.1f})", unsafe_allow_html=True)
    # with lc3:
    #     st.markdown(f"<span style='color:{y_color}'>█</span> 세로 (투명도 {y_opac:.1f})", unsafe_allow_html=True)

    st.header("📱 3D 모델 뷰어")
    stpyvista(pl, key=f"viewer_{ukey}")

else:
    st.info("💡 유효한 데이터 입력 시 3D 모델 표시됨")
