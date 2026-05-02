import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Toán Đồ Thị Trực Quan", layout="wide")

st.markdown("""
    <style>
    .main, .stApp { background-color: #FFFFFF !important; }
    div.stButton > button {
        background-color: #0056b3 !important;
        color: white !important;
        border-radius: 10px;
        font-weight: bold;
    }
    input { background-color: #F8F9FA !important; color: black !important; }
    h1, h2, label, p { color: #212529 !important; }
    iframe { border: 1px solid #eee !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo dữ liệu và tọa độ cố định
if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()
if 'pos' not in st.session_state:
    st.session_state.pos = {} # Lưu tọa độ (x, y) của từng điểm

st.title("📍 Hệ Thống Tìm Đường (Bản Mượt)")

# --- 2. PHẦN NHẬP LIỆU (Sử dụng Form để gom thao tác) ---
with st.sidebar:
    st.header("⚙️ Điều khiển")
    with st.form("input_form"):
        u = st.text_input("Từ điểm", placeholder="A").upper().strip()
        v = st.text_input("Đến điểm", placeholder="B").upper().strip()
        w = st.number_input("Khoảng cách", min_value=0.1, value=5.0)
        submit = st.form_submit_button("THÊM ĐƯỜNG NỐI")
        
    if submit and u and v and u != v:
        edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
        st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
        st.session_state.nodes.add(u)
        st.session_state.nodes.add(v)
        st.rerun()

    if st.button("🗑️ XÓA SẠCH", use_container_width=True):
        st.session_state.edges = []
        st.session_state.nodes = set()
        st.session_state.pos = {}
        st.rerun()

# --- 3. TÍNH TOÁN DIJKSTRA ---
path_nodes = []
best_edge_ids = []

st.subheader("🚩 Tìm đường ngắn nhất")
c_start, c_end, c_btn = st.columns([2, 2, 1])
start_n = c_start.selectbox("Bắt đầu", sorted(list(st.session_state.nodes)) if st.session_state.nodes else ["Chưa có điểm"])
end_n = c_end.selectbox("Kết thúc", sorted(list(st.session_state.nodes)) if st.session_state.nodes else ["Chưa có điểm"])

if c_btn.button("🚀 CHẠY", use_container_width=True):
    if st.session_state.nodes:
        G_calc = nx.MultiGraph()
        for e in st.session_state.edges:
            G_calc.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])
        try:
            path_nodes = nx.shortest_path(G_calc, source=start_n, target=end_n, weight='weight')
            dist = nx.shortest_path_length(G_calc, source=start_n, target=end_n, weight='weight')
            st.success(f"Kết quả: {' ➔ '.join(path_nodes)} | Tổng: {dist}")
            for i in range(len(path_nodes)-1):
                u_n, v_n = path_nodes[i], path_nodes[i+1]
                all_e = [e for e in st.session_state.edges if (e['from']==u_n and e['to']==v_n) or (e['from']==v_n and e['to']==u_n)]
                best_edge_ids.append(min(all_e, key=lambda x: x['weight'])['id'])
        except:
            st.error("Không có đường!")

# --- 4. VẼ ĐỒ THỊ (CỐ ĐỊNH TỌA ĐỘ) ---
def draw_graph():
    # Tạo Graph của NetworkX để tính toán tọa độ
    G_viz = nx.Graph()
    for n in st.session_state.nodes:
        G_viz.add_node(n)
    for e in st.session_state.edges:
        G_viz.add_edge(e['from'], e['to'])

    # Chỉ tính tọa độ cho những điểm CHƯA có tọa độ
    if len(st.session_state.nodes) > 0:
        new_pos = nx.spring_layout(G_viz, pos=st.session_state.pos if st.session_state.pos else None, 
                                   fixed=st.session_state.pos.keys() if st.session_state.pos else None,
                                   seed=42, k=0.5)
        st.session_state.pos = new_pos

    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#000000")
    net.toggle_physics(False)

    # Thêm Node với tọa độ cố định (nhân với 1000 để trải rộng trên màn hình)
    for node in st.session_state.nodes:
        x, y = st.session_state.pos[node]
        on_path = node in path_nodes
        color = "#FF1E1E" if on_path else "#007BFF"
        net.add_node(node, label=node, color=color, size=25, x=x*1000, y=y*1000)

    # Thêm Edge
    pair_tracker = {}
    for e in st.session_state.edges:
        pair = tuple(sorted((e['from'], e['to'])))
        pair_tracker[pair] = pair_tracker.get(pair, 0) + 1
        roundness = 0.2 * (pair_tracker[pair] - 1) if pair_tracker[pair] > 1 else 0
        on_path = e['id'] in best_edge_ids
        
        net.add_edge(e['from'], e['to'], label=str(e['weight']), 
                     color="#FF1E1E" if on_path else "#ABB2B9", 
                     width=7 if on_path else 2,
                     smooth={"type": "curvedCW", "roundness": roundness})

    net.set_options("""
    {"interaction": {"zoomView": true, "dragView": true, "navigationButtons": true},
     "nodes": {"font": {"size": 18, "strokeWidth": 5, "strokeColor": "#ffffff"}},
     "edges": {"font": {"align": "top", "size": 14, "strokeWidth": 4, "strokeColor": "#ffffff"}}}
    """)
    
    return net.generate_html()

# Hiển thị đồ thị
html_content = draw_graph()
components.html(html_content, height=650)
