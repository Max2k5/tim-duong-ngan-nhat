import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Phần mềm Tìm đường", layout="wide")

# CSS để tối ưu giao diện điện thoại
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #2196f3; color: white; }
    iframe { border-radius: 15px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.title("🌐 Công cụ Vẽ & Tìm đường tối ưu")

# Khởi tạo dữ liệu
if 'edges' not in st.session_state:
    st.session_state.edges = [] # Lưu: (u, v, weight, key)
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

# --- KHU VỰC ĐIỀU KHIỂN (Dùng Tab để tiết kiệm không gian mobile) ---
tab1, tab2 = st.tabs(["➕ Thêm Điểm/Đường", "🚩 Tìm Đường Ngắn Nhất"])

with tab1:
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        u = st.text_input("Điểm 1", placeholder="A").upper()
    with col2:
        v = st.text_input("Điểm 2", placeholder="B").upper()
    with col3:
        w = st.number_input("Khoảng cách", min_value=0.1, value=1.0, step=0.5)
    
    if st.button("Nối đường"):
        if u and v and u != v:
            # Tạo key riêng cho mỗi cạnh để phân biệt các đường nối trùng điểm
            edge_key = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append((u, v, w, edge_key))
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

with tab2:
    if st.session_state.nodes:
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            start_n = st.selectbox("Điểm đi", list(st.session_state.nodes))
        with c2:
            end_n = st.selectbox("Điểm đến", list(st.session_state.nodes))
        with c3:
            run_btn = st.button("🚀 Tìm ngay")
    else:
        st.write("Hãy thêm điểm trước ở tab bên cạnh!")

# --- XỬ LÝ ĐỒ THỊ ---
# Sử dụng MultiGraph để hỗ trợ nhiều đường nối giữa 2 điểm
G = nx.MultiGraph()
for n1, n2, weight, k in st.session_state.edges:
    G.add_edge(n1, n2, weight=weight, key=k)

path_edges_keys = []
path_nodes = []

if 'run_btn' in locals() and run_btn:
    try:
        # Dijkstra trên MultiGraph sẽ tự chọn cạnh nhỏ nhất giữa 2 node
        path_nodes = nx.shortest_path(G, source=start_n, target=end_n, weight='weight')
        dist = nx.shortest_path_length(G, source=start_n, target=end_n, weight='weight')
        st.success(f"Kết quả: {' ➔ '.join(path_nodes)} | Tổng: {dist}")
        
        # Xác định các cạnh thuộc đường đi để tô màu
        for i in range(len(path_nodes)-1):
            u_node, v_node = path_nodes[i], path_nodes[i+1]
            # Lấy cạnh có trọng số nhỏ nhất giữa 2 node này
            edges_list = G.get_edge_data(u_node, v_node)
            best_edge_key = min(edges_list, key=lambda x: edges_list[x]['weight'])
            path_edges_keys.append(best_edge_key)
    except:
        st.error("Không có đường nối!")

# --- HIỂN THỊ ĐỒ THỊ (PYVIS) ---
net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")

# Giới hạn Zoom và khóa khung hình
net.set_options("""
{
  "interaction": {
    "zoomView": false,
    "hover": true,
    "navigationButtons": true
  },
  "edges": {
    "smooth": {
      "type": "curvedCW",
      "roundness": 0.2
    }
  },
  "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -50,
      "centralGravity": 0.01,
      "springLength": 100,
      "springConstant": 0.08
    },
    "maxVelocity": 50,
    "solver": "forceAtlas2Based",
    "timestep": 0.35
  }
}
""")

for node in st.session_state.nodes:
    color = "#FF4B4B" if node in path_nodes else "#2196f3"
    net.add_node(node, label=node, color=color, size=25)

for n1, n2, weight, k in st.session_state.edges:
    is_path = k in path_edges_keys
    net.add_edge(n1, n2, label=str(weight), 
                 width=5 if is_path else 2, 
                 color="#FF4B4B" if is_path else "#ABB2B9")

# Nút xóa nhanh
if st.button("🗑️ Xóa hết làm lại"):
    st.session_state.edges = []
    st.session_state.nodes = set()
    st.rerun()

net.save_graph("graph.html")
components.html(open("graph.html", 'r', encoding='utf-8').read(), height=550)
