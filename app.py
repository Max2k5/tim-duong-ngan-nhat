import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Toán Đồ Thị", layout="wide")

# Tối ưu giao diện để nhìn rõ trên điện thoại
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stTextInput>div>div>input { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

st.title("📍 Hệ Thống Tìm Đường Đi")

# --- KHU VỰC ĐIỀU KHIỂN ---
with st.expander("➕ THÊM ĐƯỜNG NỐI MỚI", expanded=True):
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        u = st.text_input("Từ điểm", placeholder="A").upper().strip()
    with c2:
        v = st.text_input("Đến điểm", placeholder="B").upper().strip()
    with c3:
        w = st.number_input("Khoảng cách", min_value=0.1, value=5.0)
    
    if st.button("Xác nhận nối"):
        if u and v and u != v:
            # Lưu mỗi cạnh với một ID duy nhất để phân biệt
            st.session_state.edges.append({
                'from': u, 'to': v, 'weight': w, 'id': len(st.session_state.edges)
            })
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

# --- KHU VỰC TÍNH TOÁN ---
path_nodes = []
best_edge_ids = []

if st.session_state.nodes:
    with st.expander("🚩 CHẠY THUẬT TOÁN"):
        col_s, col_e = st.columns(2)
        start_n = col_s.selectbox("Điểm bắt đầu", sorted(list(st.session_state.nodes)))
        end_n = col_e.selectbox("Điểm kết thúc", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 Tìm đường ngắn nhất"):
            # Dùng MultiGraph để tìm đường
            G = nx.MultiGraph()
            for e in st.session_state.edges:
                G.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])
            
            try:
                path_nodes = nx.shortest_path(G, source=start_n, target=end_n, weight='weight')
                dist = nx.shortest_path_length(G, source=start_n, target=end_n, weight='weight')
                st.success(f"Kết quả: {' ➔ '.join(path_nodes)} (Tổng: {dist})")
                
                # Tìm ID các cạnh thuộc đường đi ngắn nhất để tô màu
                for i in range(len(path_nodes)-1):
                    u_n, v_n = path_nodes[i], path_nodes[i+1]
                    # Lấy tất cả các cạnh giữa 2 điểm này và chọn cạnh nhỏ nhất
                    all_edges = [e for e in st.session_state.edges if (e['from'] == u_n and e['to'] == v_n) or (e['from'] == v_n and e['to'] == u_n)]
                    best_edge = min(all_edges, key=lambda x: x['weight'])
                    best_edge_ids.append(best_edge['id'])
            except:
                st.error("Không có đường nối giữa hai điểm này!")

# --- VẼ ĐỒ THỊ ---
net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black")

# CẤU HÌNH VẬT LÝ: Tắt lực hút để các điểm không tự lại gần nhau
net.toggle_physics(False) 

# Thêm điểm
for node in st.session_state.nodes:
    color = "#FF4B4B" if node in path_nodes else "#2196F3"
    net.add_node(node, label=node, color=color, size=30)

# Thêm cạnh (Xử lý chồng đường)
# Đếm số đường nối giữa các cặp để tạo độ cong khác nhau
pair_count = {}

for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    pair_count[pair] = pair_count.get(pair, 0) + 1
    
    # Nếu là đường thứ 2 trở đi giữa cùng 2 điểm, ta tăng độ cong (smooth)
    smooth_config = {"type": "curvedCW", "roundness": 0.0}
    if pair_count[pair] > 1:
        smooth_config["roundness"] = 0.2 * (pair_count[pair] - 1)

    is_on_path = e['id'] in best_edge_ids
    
    net.add_edge(
        e['from'], e['to'], 
        label=str(e['weight']), 
        color="#FF4B4B" if is_on_path else "#ABB2B9",
        width=6 if is_on_path else 2,
        smooth=smooth_config
    )

# Lưu và hiển thị
if st.button("🗑️ Xóa toàn bộ dữ liệu"):
    st.session_state.edges = []
    st.session_state.nodes = set()
    st.rerun()

net.save_graph("graph.html")
components.html(open("graph.html", 'r', encoding='utf-8').read(), height=550)
