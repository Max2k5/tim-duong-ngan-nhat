import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Toán Đồ Thị Pro", layout="wide")

# CSS cố định giao diện
st.markdown("""
    <style>
    .main, .stApp { background-color: #FFFFFF !important; }
    div.stButton > button { background-color: #0056b3 !important; color: white !important; width: 100%; }
    iframe { border: 1px solid #eee !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()
if 'pos' not in st.session_state:
    st.session_state.pos = {}

st.title("📍 Đồ Thị Không Reset Zoom")

# --- 1. NHẬP LIỆU ---
with st.sidebar:
    st.header("⚙️ Cài đặt")
    u = st.text_input("Từ điểm").upper().strip()
    v = st.text_input("Đến điểm").upper().strip()
    w = st.number_input("Khoảng cách", min_value=0.1, value=5.0)
    
    if st.button("➕ NỐI ĐƯỜNG"):
        if u and v and u != v:
            edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

    if st.button("🗑️ XÓA TOÀN BỘ"):
        st.session_state.edges = []
        st.session_state.nodes = set()
        st.session_state.pos = {}
        st.rerun()

# --- 2. TÍNH TOÁN DIJKSTRA ---
path_nodes = []
best_edge_ids = []
st.subheader("🚩 Lộ trình ngắn nhất")
c1, c2, c3 = st.columns([2, 2, 1])
start_node = c1.selectbox("Điểm đi", sorted(list(st.session_state.nodes)) if st.session_state.nodes else ["-"])
end_node = c2.selectbox("Điểm đến", sorted(list(st.session_state.nodes)) if st.session_state.nodes else ["-"])

if c3.button("🚀 CHẠY"):
    if st.session_state.nodes and start_node != "-":
        G = nx.MultiGraph()
        for e in st.session_state.edges:
            G.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])
        try:
            path_nodes = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
            dist = nx.shortest_path_length(G, source=start_node, target=end_node, weight='weight')
            st.success(f"Kết quả: {' ➔ '.join(path_nodes)} | Tổng: {dist}")
            for i in range(len(path_nodes)-1):
                u_n, v_n = path_nodes[i], path_nodes[i+1]
                all_e = [e for e in st.session_state.edges if (e['from']==u_n and e['to']==v_n) or (e['from']==v_n and e['to']==u_n)]
                best_edge_ids.append(min(all_e, key=lambda x: x['weight'])['id'])
        except:
            st.error("Không có đường!")

# --- 3. VẼ ĐỒ THỊ VỚI SCRIPT LƯU VỊ TRÍ ---
def get_graph_html():
    # Tính tọa độ cố định
    G_viz = nx.Graph()
    G_viz.add_nodes_from(st.session_state.nodes)
    G_viz.add_edges_from([(e['from'], e['to']) for e in st.session_state.edges])
    
    new_pos = nx.spring_layout(G_viz, pos=st.session_state.pos if st.session_state.pos else None, 
                               fixed=st.session_state.pos.keys() if st.session_state.pos else None,
                               seed=42)
    st.session_state.pos = new_pos

    net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="#000000")
    net.toggle_physics(False)

    for node in st.session_state.nodes:
        x, y = st.session_state.pos[node]
        color = "#FF1E1E" if node in path_nodes else "#007BFF"
        net.add_node(node, label=node, color=color, size=25, x=x*1000, y=y*1000)

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

    net.set_options("""{"interaction": {"navigationButtons": true}}""")
    
    raw_html = net.generate_html()
    
    # CHÈN SCRIPT "THẦN THÁNH" VÀO HTML
    custom_script = """
    <script>
    // Chờ đồ thị khởi tạo xong
    setTimeout(function() {
        var network = network; // Biến network từ pyvis
        
        // 1. Phục hồi vị trí cũ từ localStorage
        var savedView = localStorage.getItem('graphView');
        if (savedView) {
            var view = JSON.parse(savedView);
            network.moveTo({
                position: view.position,
                scale: view.scale
            });
        }

        // 2. Lắng nghe sự kiện di chuyển/zoom để lưu lại
        network.on("afterDrawing", function() {
            var currentView = {
                position: network.getViewPosition(),
                scale: network.getScale()
            };
            localStorage.setItem('graphView', JSON.stringify(currentView));
        });
    }, 500);
    </script>
    """
    return raw_html.replace("</body>", custom_script + "</body>")

# Hiển thị
html_content = get_graph_html()
components.html(html_content, height=650)
