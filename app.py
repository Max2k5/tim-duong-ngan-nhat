import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Đồ Thị Thông Minh", layout="wide")

# CSS cho giao diện sạch sẽ
st.markdown("""
    <style>
    .main, .stApp { background-color: white !important; }
    .stButton>button { width: 100%; border-radius: 10px; background-color: #007bff; color: white; }
    iframe { border: 1px solid #ddd; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

st.title("📍 Đồ Thị Ghi Nhớ Vị Trí")

# --- 1. NHẬP LIỆU ---
with st.sidebar:
    st.header("➕ Thêm dữ liệu")
    u = st.text_input("Từ điểm").upper().strip()
    v = st.text_input("Đến điểm").upper().strip()
    w = st.number_input("Khoảng cách", min_value=0.1, value=5.0)
    
    if st.button("Nối đường"):
        if u and v and u != v:
            edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

    if st.button("🗑️ Xóa toàn bộ"):
        st.session_state.edges = []
        st.session_state.nodes = set()
        # Xóa luôn bộ nhớ vị trí trong trình duyệt
        components.html("<script>localStorage.clear(); window.parent.location.reload();</script>")
        st.rerun()

# --- 2. TÍNH TOÁN ĐƯỜNG ĐI ---
path_nodes = []
best_edge_ids = []

st.subheader("🚩 Tìm đường và Tô màu")
col1, col2, col3 = st.columns([2, 2, 1])
s_node = col1.selectbox("Bắt đầu", sorted(list(st.session_state.nodes)) if st.session_state.nodes else ["-"])
e_node = col2.selectbox("Đích", sorted(list(st.session_state.nodes)) if st.session_state.nodes else ["-"])

if col3.button("TÔ MÀU ĐƯỜNG ĐI"):
    if st.session_state.nodes and s_node != "-":
        G = nx.MultiGraph()
        for e in st.session_state.edges:
            G.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])
        try:
            path_nodes = nx.shortest_path(G, source=s_node, target=e_node, weight='weight')
            for i in range(len(path_nodes)-1):
                u_n, v_n = path_nodes[i], path_nodes[i+1]
                all_e = [e for e in st.session_state.edges if (e['from']==u_n and e['to']==v_n) or (e['from']==v_n and e['to']==u_n)]
                best_edge_ids.append(min(all_e, key=lambda x: x['weight'])['id'])
            st.success(f"Đã tìm thấy đường đi!")
        except:
            st.error("Không có đường nối!")

# --- 3. VẼ ĐỒ THỊ VỚI NHÚNG JAVASCRIPT GHI NHỚ ---
net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
net.toggle_physics(False) # Tắt vật lý để không bị nhảy

# Thêm Nodes
for node in st.session_state.nodes:
    on_path = node in path_nodes
    color = "#FF1E1E" if on_path else "#2196F3"
    net.add_node(node, label=node, color=color, size=25, font={'size': 18, 'strokeWidth': 5, 'strokeColor': 'white'})

# Thêm Edges
pair_tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    pair_tracker[pair] = pair_tracker.get(pair, 0) + 1
    smooth = {"type": "curvedCW", "roundness": 0.2 * (pair_tracker[pair]-1) if pair_tracker[pair]>1 else 0}
    on_path = e['id'] in best_edge_ids
    
    net.add_edge(e['from'], e['to'], label=str(e['weight']), 
                 color="#FF1E1E" if on_path else "#D3D3D3", 
                 width=7 if on_path else 2, smooth=smooth,
                 font={'background': 'white', 'size': 14})

# Tạo HTML và nhúng Script "Ghi nhớ"
raw_html = net.generate_html()

custom_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        // 1. Phục hồi tọa độ từ localStorage
        var savedCoords = JSON.parse(localStorage.getItem('nodePositions') || '{}');
        Object.keys(savedCoords).forEach(function(nodeId) {
            network.moveNode(nodeId, savedCoords[nodeId].x, savedCoords[nodeId].y);
        });

        // 2. Lắng nghe sự kiện kéo thả để lưu tọa độ
        network.on("dragEnd", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var pos = network.getPositions([nodeId])[nodeId];
                var currentCoords = JSON.parse(localStorage.getItem('nodePositions') || '{}');
                currentCoords[nodeId] = pos;
                localStorage.setItem('nodePositions', JSON.stringify(currentCoords));
            }
        });
        
        // 3. Phục hồi mức Zoom
        var savedView = JSON.parse(localStorage.getItem('graphView') || '{}');
        if(savedView.scale) {
            network.moveTo({position: savedView.position, scale: savedView.scale});
        }
        
        network.on("zoom", function() {
            localStorage.setItem('graphView', JSON.stringify({
                position: network.getViewPosition(),
                scale: network.getScale()
            }));
        });
    }, 500); 
});
</script>
"""

final_html = raw_html.replace("</body>", custom_js + "</body>")
components.html(final_html, height=650)
