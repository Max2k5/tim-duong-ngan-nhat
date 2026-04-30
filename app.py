import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Toán Đồ Thị", layout="wide")

# CSS để giao diện mượt hơn
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    iframe { border: 1px solid #ddd; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

st.title("📍 Hệ Thống Tìm Đường (Bản Full Zoom)")

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
# Bật lại tính năng Zoom và các nút điều hướng
net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")

# Cấu hình Interaction để cho phép Zoom
net.set_options("""
{
  "interaction": {
    "zoomView": true,
    "dragView": true,
    "navigationButtons": true,
    "multiselect": true
  },
  "physics": {
    "enabled": false
  }
}
""")

# Thêm điểm
for node in st.session_state.nodes:
    is_start_end = (len(path_nodes) > 0 and (node == path_nodes[0] or node == path_nodes[-1]))
    color = "#FF1E1E" if is_start_end else ("#FF4B4B" if node in path_nodes else "#2196F3")
    net.add_node(node, label=node, color=color, size=35 if is_start_end else 25)

# Thêm cạnh (Xử lý đường cong khi có nhiều đường nối)
pair_tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    pair_tracker[pair] = pair_tracker.get(pair, 0) + 1
    
    # Tạo độ cong khác nhau cho các đường nối song song
    smooth = {"type": "curvedCW", "roundness": 0.0}
    if pair_tracker[pair] > 1:
        smooth["roundness"] = 0.2 * (pair_tracker[pair] - 1)

    on_path = e['id'] in best_edge_ids
    net.add_edge(
        e['from'], e['to'], 
        label=str(e['weight']), 
        color="#FF1E1E" if on_path else "#ABB2B9",
        width=7 if on_path else 2,
        smooth=smooth
    )

# Nút chức năng phụ
c_1, c_2 = st.columns(2)
with c_1:
    if st.button("🗑️ Xóa toàn bộ"):
        st.session_state.edges = []
        st.session_state.nodes = set()
        st.rerun()
with c_2:
    st.info("💡 Mẹo: Bạn có thể dùng con trỏ chuột để phóng to/thu nhỏ và kéo các điểm đi mọi nơi.")

net.save_graph("graph_full.html")
components.html(open("graph_full.html", 'r', encoding='utf-8').read(), height=650)
