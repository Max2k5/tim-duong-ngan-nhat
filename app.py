import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Toán Đồ Thị Trực Quan", layout="wide")

# CSS tối ưu giao diện
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #f0f2f6; }
    iframe { border: 1px solid #eee; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

st.title("📍 Hệ Thống Tìm Đường (Chống chồng chữ)")

# --- 1. NHẬP LIỆU ---
with st.expander("➕ THÊM ĐƯỜNG NỐI", expanded=True):
    c1, c2, c3 = st.columns([1, 1, 1])
    u = c1.text_input("Từ điểm", placeholder="A").upper().strip()
    v = c2.text_input("Đến điểm", placeholder="B").upper().strip()
    w = c3.number_input("Khoảng cách", min_value=0.1, value=5.0)
    
    if st.button("Xác nhận nối đường"):
        if u and v and u != v:
            edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

# --- 2. TÍNH TOÁN ---
path_nodes = []
best_edge_ids = []

if st.session_state.nodes:
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT"):
        col_s, col_e = st.columns(2)
        start_n = col_s.selectbox("Điểm xuất phát", sorted(list(st.session_state.nodes)))
        end_n = col_e.selectbox("Điểm đích", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 Chạy Dijkstra"):
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

# --- 3. VẼ ĐỒ THỊ ---
net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")

# Cấu hình Interaction & Tắt Physics
net.set_options("""
{
  "interaction": {
    "zoomView": true,
    "dragView": true,
    "navigationButtons": true
  },
  "nodes": {
    "font": {
      "size": 16,
      "face": "arial",
      "background": "white"
    }
  },
  "edges": {
    "font": {
      "align": "top",
      "background": "white",
      "size": 14,
      "strokeWidth": 0
    },
    "color": { "inherit": false }
  },
  "physics": { "enabled": false }
}
""")

# Thêm điểm (Node)
for node in st.session_state.nodes:
    on_path = node in path_nodes
    color = "#FF1E1E" if on_path else "#2196F3"
    # Dùng nhãn nằm trên/dưới nút để tránh bị cạnh đè
    net.add_node(node, label=node, color=color, size=25, font={'color': color, 'weight': 'bold'})

# Thêm đường nối (Edge)
pair_tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    pair_tracker[pair] = pair_tracker.get(pair, 0) + 1
    
    # Độ cong cho các đường song song
    smooth = {"type": "curvedCW", "roundness": 0.0}
    if pair_tracker[pair] > 1:
        smooth["roundness"] = 0.25 * (pair_tracker[pair] - 1)

    on_path = e['id'] in best_edge_ids
    net.add_edge(
        e['from'], e['to'], 
        label=f" {str(e['weight'])} ", # Thêm khoảng trắng để dễ nhìn
        color="#FF1E1E" if on_path else "#D3D3D3",
        width=7 if on_path else 2,
        smooth=smooth,
        font={'background': 'white'} # Tạo khung trắng cho con số
    )

# Nút Xóa
if st.button("🗑️ Xóa sạch đồ thị"):
    st.session_state.edges = []
    st.session_state.nodes = set()
    st.rerun()

net.save_graph("graph_clean.html")
components.html(open("graph_clean.html", 'r', encoding='utf-8').read(), height=650)
