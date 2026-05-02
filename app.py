import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

# 1. CẤU HÌNH GIAO DIỆN TỐI ƯU MOBILE
st.set_page_config(page_title="Tìm Đường Thông Minh", layout="wide")

st.markdown("""
    <style>
    /* Ép nền trắng toàn bộ */
    .main, .stApp { background-color: #FFFFFF !important; }
    
    /* Làm các nút bấm to, dễ chạm trên điện thoại */
    .stButton>button {
        width: 100%;
        height: 3.5em;
        border-radius: 12px;
        font-weight: bold;
        background-color: #007bff !important;
        color: white !important;
        border: none;
        margin-top: 10px;
    }
    
    /* Tối ưu các ô nhập liệu cho mobile */
    input {
        height: 3em !important;
        font-size: 16px !important; /* Chống tự động zoom trên iPhone */
    }
    
    /* Khung kết quả nổi bật */
    .result-box {
        background-color: #e7f3ff;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #007bff;
        margin: 10px 0;
    }
    
    /* Bo góc khung vẽ đồ thị */
    iframe {
        border: 1px solid #ddd !important;
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

st.title("📍 Công Cụ Tìm Đường")

# --- 2. NHẬP LIỆU (Thiết kế dạng thẻ cuộn cho Mobile) ---
with st.expander("➕ THÊM ĐƯỜNG NỐI MỚI", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        u = st.text_input("Điểm bắt đầu", placeholder="Ví dụ: A").upper().strip()
    with col2:
        v = st.text_input("Điểm kết thúc", placeholder="Ví dụ: B").upper().strip()
    
    w = st.number_input("Độ dài/Khoảng cách", min_value=0.1, value=5.0, step=1.0)
    
    if st.button("XÁC NHẬN NỐI ĐƯỜNG"):
        if u and v and u != v:
            edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

# --- 3. TÌM ĐƯỜNG & HIỂN THỊ KẾT QUẢ ---
path_nodes = []
best_edge_ids = []
total_dist = 0

if st.session_state.nodes:
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT", expanded=True):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Chọn điểm đi", sorted(list(st.session_state.nodes)))
        end_node = c2.selectbox("Chọn điểm đến", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 TÌM ĐƯỜNG & TÔ MÀU"):
            G = nx.MultiGraph()
            for e in st.session_state.edges:
                G.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])
            try:
                path_nodes = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
                total_dist = nx.shortest_path_length(G, source=start_node, target=end_node, weight='weight')
                
                # Xác định các ID cạnh để tô màu
                for i in range(len(path_nodes)-1):
                    u_n, v_n = path_nodes[i], path_nodes[i+1]
                    all_e = [e for e in st.session_state.edges if (e['from']==u_n and e['to']==v_n) or (e['from']==v_n and e['to']==u_n)]
                    best_edge_ids.append(min(all_e, key=lambda x: x['weight'])['id'])
                
                # HIỂN THỊ KẾT QUẢ CHI TIẾT
                st.markdown(f"""
                    <div class="result-box">
                        <h3 style="margin-top:0; color:#0056b3;">✅ Đã tìm thấy đường đi!</h3>
                        <p style="font-size:18px;"><b>Lộ trình:</b> {' ➔ '.join(path_nodes)}</p>
                        <p style="font-size:18px;"><b>Tổng độ dài:</b> <span style="color:red; font-weight:bold;">{total_dist}</span></p>
                    </div>
                """, unsafe_allow_html=True)
            except:
                st.error("Không có đường nối giữa hai điểm này!")

# --- 4. VẼ ĐỒ THỊ (GHI NHỚ VỊ TRÍ) ---
net = Network(height="550px", width="100%", bgcolor="#ffffff", font_color="black")
net.toggle_physics(False)

for node in st.session_state.nodes:
    on_path = node in path_nodes
    color = "#FF1E1E" if on_path else "#2196F3"
    net.add_node(node, label=node, color=color, size=30 if on_path else 25, 
                 font={'size': 20, 'strokeWidth': 5, 'strokeColor': 'white'})

pair_tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    pair_tracker[pair] = pair_tracker.get(pair, 0) + 1
    roundness = 0.2 * (pair_tracker[pair]-1) if pair_tracker[pair]>1 else 0
    on_path = e['id'] in best_edge_ids
    
    net.add_edge(e['from'], e['to'], label=str(e['weight']), 
                 color="#FF1E1E" if on_path else "#D3D3D3", 
                 width=8 if on_path else 2, smooth={"type": "curvedCW", "roundness": roundness},
                 font={'background': 'white', 'size': 14})

# Script giữ vị trí đồ thị
raw_html = net.generate_html()
custom_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var savedCoords = JSON.parse(localStorage.getItem('nodePositions') || '{}');
        Object.keys(savedCoords).forEach(function(nodeId) {
            network.moveNode(nodeId, savedCoords[nodeId].x, savedCoords[nodeId].y);
        });
        network.on("dragEnd", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var pos = network.getPositions([nodeId])[nodeId];
                var currentCoords = JSON.parse(localStorage.getItem('nodePositions') || '{}');
                currentCoords[nodeId] = pos;
                localStorage.setItem('nodePositions', JSON.stringify(currentCoords));
            }
        });
        var savedView = JSON.parse(localStorage.getItem('graphView') || '{}');
        if(savedView.scale) { network.moveTo({position: savedView.position, scale: savedView.scale}); }
        network.on("zoom", function() {
            localStorage.setItem('graphView', JSON.stringify({position: network.getViewPosition(), scale: network.getScale()}));
        });
    }, 500); 
});
</script>
"""
final_html = raw_html.replace("</body>", custom_js + "</body>")
components.html(final_html, height=600)

if st.button("🗑️ XÓA SẠCH ĐỒ THỊ", key="clear_btn"):
    st.session_state.edges = []
    st.session_state.nodes = set()
    components.html("<script>localStorage.clear(); window.parent.location.reload();</script>")
    st.rerun()
