import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

# 1. THIẾT LẬP GIAO DIỆN (SỬA LỖI NÚT TRẮNG)
st.set_page_config(page_title="Toán Đồ Thị Trực Quan", layout="wide")

st.markdown("""
    <style>
    /* Ép nền trang web luôn màu trắng sáng */
    .main, .stApp { background-color: #FFFFFF !important; }
    
    /* Cấu hình nút bấm: Ép màu xanh đậm, chữ trắng hoàn toàn */
    div.stButton > button:first-child {
        background-color: #0056b3 !important;
        color: #FFFFFF !important;
        border: 2px solid #004494 !important;
        border-radius: 10px;
        font-weight: bold;
        height: 3em;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #004494 !important;
        color: #FFFFFF !important;
        border-color: #002d62 !important;
    }

    /* Nút xóa sạch: Cho màu đỏ để dễ phân biệt và không bị trắng */
    div.stButton > button[key="clear_btn"] {
        background-color: #d32f2f !important;
        border-color: #b71c1c !important;
    }

    /* Các ô nhập liệu: Chữ đen, nền xám nhạt */
    input {
        color: #000000 !important;
        background-color: #F8F9FA !important;
        border: 1px solid #CED4DA !important;
    }

    /* Chữ tiêu đề và nhãn: Ép màu đen */
    h1, h2, h3, label, p, span {
        color: #212529 !important;
    }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

st.title("📍 Ứng dụng Tìm Đường (Bản Sửa Lỗi Nút)")

# --- 2. NHẬP LIỆU ---
with st.expander("➕ THÊM ĐƯỜNG NỐI", expanded=True):
    c1, c2, c3 = st.columns([1, 1, 1])
    u = c1.text_input("Từ điểm", placeholder="A").upper().strip()
    v = c2.text_input("Đến điểm", placeholder="B").upper().strip()
    w = c3.number_input("Khoảng cách", min_value=0.1, value=5.0)
    
    if st.button("XÁC NHẬN NỐI ĐƯỜNG"):
        if u and v and u != v:
            edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

# --- 3. TÍNH TOÁN ---
path_nodes = []
best_edge_ids = []

if st.session_state.nodes:
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT"):
        col_s, col_e = st.columns(2)
        start_n = col_s.selectbox("Điểm xuất phát", sorted(list(st.session_state.nodes)))
        end_n = col_e.selectbox("Điểm đích", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 CHẠY THUẬT TOÁN"):
            G = nx.MultiGraph()
            for e in st.session_state.edges:
                G.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])
            try:
                path_nodes = nx.shortest_path(G, source=start_n, target=end_n, weight='weight')
                dist = nx.shortest_path_length(G, source=start_n, target=end_n, weight='weight')
                st.success(f"Đường đi: {' ➔ '.join(path_nodes)} | Tổng: {dist}")
                
                for i in range(len(path_nodes)-1):
                    u_n, v_n = path_nodes[i], path_nodes[i+1]
                    all_edges = [e for e in st.session_state.edges if (e['from'] == u_n and e['to'] == v_n) or (e['from'] == v_n and e['to'] == u_n)]
                    best_edge = min(all_edges, key=lambda x: x['weight'])
                    best_edge_ids.append(best_edge['id'])
            except:
                st.error("Không có đường nối!")

# --- 4. VẼ ĐỒ THỊ ---
net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
net.set_options("""
{
  "interaction": {"zoomView": true, "dragView": true, "navigationButtons": true},
  "nodes": {"font": {"size": 16, "strokeWidth": 4, "strokeColor": "#ffffff"}},
  "edges": {"font": {"align": "top", "size": 14, "strokeWidth": 4, "strokeColor": "#ffffff", "color": "#000000"}},
  "physics": {"enabled": false}
}
""")

for node in st.session_state.nodes:
    on_path = node in path_nodes
    color = "#FF1E1E" if on_path else "#007BFF"
    net.add_node(node, label=node, color=color, size=25)

pair_tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    pair_tracker[pair] = pair_tracker.get(pair, 0) + 1
    smooth = {"type": "curvedCW", "roundness": 0.2 * (pair_tracker[pair]-1) if pair_tracker[pair]>1 else 0}
    on_path = e['id'] in best_edge_ids
    net.add_edge(e['from'], e['to'], label=str(e['weight']), color="#FF1E1E" if on_path else "#6C757D", width=7 if on_path else 2, smooth=smooth)

# Nút xóa được đặt key riêng để áp màu đỏ
if st.button("🗑️ XÓA SẠCH ĐỒ THỊ", key="clear_btn"):
    st.session_state.edges = []
    st.session_state.nodes = set()
    st.rerun()

net.save_graph("graph.html")
components.html(open("graph.html", 'r', encoding='utf-8').read(), height=650)
