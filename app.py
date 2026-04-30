import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Tìm đường đi ngắn nhất", layout="wide")

st.title("🌐 Ứng dụng Tìm đường đi ngắn nhất (Dijkstra)")
st.sidebar.header("Cấu hình Đồ thị")

# Khởi tạo đồ thị trong session state để không bị mất dữ liệu khi load lại trang
if 'edges' not in st.session_state:
    st.session_state.edges = []
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

# --- GIAO DIỆN BÊN TRÁI: NHẬP DỮ LIỆU ---
with st.sidebar:
    st.subheader("1. Thêm cạnh mới")
    u = st.text_input("Điểm đầu (ví dụ: A)").upper()
    v = st.text_input("Điểm cuối (ví dụ: B)").upper()
    w = st.number_input("Khoảng cách", min_value=0.0, value=1.0)
    
    if st.button("Thêm đường nối"):
        if u and v and u != v:
            st.session_state.edges.append((u, v, w))
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.success(f"Đã nối {u} - {v} với d={w}")
        else:
            st.error("Vui lòng nhập tên điểm hợp lệ!")

    if st.button("Xóa toàn bộ đồ thị"):
        st.session_state.edges = []
        st.session_state.nodes = set()
        st.rerun()

    st.markdown("---")
    st.subheader("2. Tìm đường")
    start_node = st.selectbox("Chọn điểm bắt đầu", list(st.session_state.nodes))
    end_node = st.selectbox("Chọn điểm kết thúc", list(st.session_state.nodes))

# --- GIAO DIỆN CHÍNH: HIỂN THỊ ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Sơ đồ mạng lưới (Có thể kéo thả)")
    G = nx.Graph()
    for n1, n2, weight in st.session_state.edges:
        G.add_edge(n1, n2, weight=weight)

    # Tính toán Dijkstra nếu có đủ dữ liệu
    path = []
    if st.button("🚀 Chạy thuật toán Dijkstra"):
        try:
            path = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
            distance = nx.shortest_path_length(G, source=start_node, target=end_node, weight='weight')
            st.success(f"Đường đi ngắn nhất: {' ➔ '.join(path)}")
            st.info(f"Tổng khoảng cách: {distance}")
        except:
            st.error("Không tìm thấy đường đi giữa hai điểm này!")

    # Vẽ đồ thị bằng Pyvis (Tương tác được)
    net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")
    for node in st.session_state.nodes:
        color = "#ff9800" if node in path else "#2196f3"
        net.add_node(node, label=node, color=color)
    
    path_edges = list(zip(path, path[1:])) if path else []
    for n1, n2, weight in st.session_state.edges:
        is_path = (n1, n2) in path_edges or (n2, n1) in path_edges
        width = 5 if is_path else 2
        color = "#f44336" if is_path else "#9e9e9e"
        net.add_edge(n1, n2, title=f"Khoảng cách: {weight}", label=str(weight), width=width, color=color)

    net.save_graph("graph.html")
    HtmlFile = open("graph.html", 'r', encoding='utf-8')
    components.html(HtmlFile.read(), height=550)

with col2:
    st.subheader("Danh sách các cạnh")
    if st.session_state.edges:
        for e in st.session_state.edges:
            st.text(f"📍 {e[0]} --({e[2]})--> {e[1]}")
    else:
        st.write("Chưa có dữ liệu.")
