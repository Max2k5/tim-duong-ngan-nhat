import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

# 1. CẤU HÌNH GIAO DIỆN
st.set_page_config(page_title="Tìm Đường Thông Minh", layout="wide")

st.markdown("""
    <style>
    .main, .stApp { background-color: #FFFFFF !important; }
    .stButton>button {
        width: 100%; height: 3.5em; border-radius: 12px;
        font-weight: bold; background-color: #007bff !important; color: white !important;
    }
    div.stButton > button[key="fit_btn"] { background-color: #28a745 !important; height: 2.5em; margin-bottom: 10px; }
    div.stButton > button[key="clear_btn"] { background-color: #dc3545 !important; }
    input { height: 3em !important; font-size: 16px !important; }
    .result-box {
        background-color: #f8f9fa; padding: 15px; border-radius: 12px;
        border: 1px solid #dee2e6; margin: 10px 0;
    }
    iframe { border: 1px solid #ddd !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state:
    st.session_state.edges = [] 
if 'nodes' not in st.session_state:
    st.session_state.nodes = set()

st.title("📍 Tìm đường đi có trọng số ngắn nhất")

# --- 2. NHẬP LIỆU ---
with st.expander("➕ THÊM ĐƯỜNG NỐI", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1])
    u = col1.text_input("Từ điểm").upper().strip()
    v = col2.text_input("Đến điểm").upper().strip()
    w = col3.number_input("Khoảng cách", min_value=0.1, value=5.0)
    
    if st.button("Thêm đường nối"):
        if u and v and u != v:
            edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

# --- 3. TÍNH TOÁN ---
path_nodes = []
best_edge_ids = []
total_dist = 0

if st.session_state.nodes:
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT", expanded=True):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Điểm đi", sorted(list(st.session_state.nodes)))
        end_node = c2.selectbox("Điểm đến", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 TÌM!!"):
            G = nx.MultiGraph()
            for e in st.session_state.edges:
                G.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])
            try:
                path_nodes = nx.shortest_path(G, source=start_node, target=end_node, weight='weight')
                total_dist = nx.shortest_path_length(G, source=start_node, target=end_node, weight='weight')
                for i in range(len(path_nodes)-1):
                    u_n, v_n = path_nodes[i], path_nodes[i+1]
                    all_e = [e for e in st.session_state.edges if (e['from']==u_n and e['to']==v_n) or (e['from']==v_n and e['to']==u_n)]
                    best_edge_ids.append(min(all_e, key=lambda x: x['weight'])['id'])
                
                st.markdown(f"""
                    <div class="result-box">
                        <p style="margin:0;"><b>Lộ trình:</b> {' ➔ '.join(path_nodes)}</p>
                        <p style="margin:0;"><b>Tổng độ dài:</b> <span style="color:red; font-weight:bold;">{total_dist}</span></p>
                    </div>
                """, unsafe_allow_html=True)
            except:
                st.error("Không có đường nối!")

# --- 4. VẼ ĐỒ THỊ ---
st.write("---")
net = Network(height="550px", width="100%", bgcolor="#ffffff", font_color="black")

# KHÓA CHẶT PHYSICS Ở ĐÂY
net.set_options("""
{
  "physics": {
    "enabled": false
  },
  "interaction": {
    "navigationButtons": true,
    "keyboard": true,
    "zoomView": true,
    "dragView": true
  },
  "nodes": {
    "font": {"size": 20, "strokeWidth": 5, "strokeColor": "white"}
  }
}
""")

for node in st.session_state.nodes:
    on_path = node in path_nodes
    net.add_node(node, label=node, color="#FF1E1E" if on_path else "#2196F3", size=30 if on_path else 25)

pair_tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    pair_tracker[pair] = pair_tracker.get(pair, 0) + 1
    on_path = e['id'] in best_edge_ids
    net.add_edge(e['from'], e['to'], label=str(e['weight']), 
                 color="#FF1E1E" if on_path else "#D3D3D3", 
                 width=8 if on_path else 2, 
                 smooth={"type": "curvedCW", "roundness": 0.2 * (pair_tracker[pair]-1) if pair_tracker[pair]>1 else 0},
                 font={'background': 'white', 'size': 14})

# Script JavaScript giữ vị trí
raw_html = net.generate_html()
custom_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var savedCoords = JSON.parse(localStorage.getItem('nodePositions') || '{}');
        Object.keys(savedCoords).forEach(function(nodeId) {
            network.moveNode(nodeId, savedCoords[nodeId].x, savedCoords[nodeId].y);
        });
        var savedView = JSON.parse(localStorage.getItem('graphView') || '{}');
        if(savedView.scale) { network.moveTo({position: savedView.position, scale: savedView.scale}); }

        network.on("dragEnd", function(params) {
            if (params.nodes.length > 0) {
                var nodeId = params.nodes[0];
                var pos = network.getPositions([nodeId])[nodeId];
                var currentCoords = JSON.parse(localStorage.getItem('nodePositions') || '{}');
                currentCoords[nodeId] = pos;
                localStorage.setItem('nodePositions', JSON.stringify(currentCoords));
            }
        });
        network.on("moveEnd", function() {
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
components.html(final_html, height=600)

if st.button("🗑️ XÓA SẠCH DỮ LIỆU", key="clear_btn"):
    st.session_state.edges = []
    st.session_state.nodes = set()
    components.html("<script>localStorage.clear(); window.parent.location.reload();</script>")
    st.rerun()
