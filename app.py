import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Đường Đi Ngắn Nhất", layout="wide")

st.markdown("""
    <style>
    .main, .stApp { background-color: #FFFFFF !important; }
    .stButton>button {
        width: 100%; height: 3.5em; border-radius: 12px;
        font-weight: bold; background-color: #007bff !important; color: white !important;
    }
    div.stButton > button[key="fit_btn"] { background-color: #28a745 !important; height: 2.8em; margin-bottom: 10px; }
    div.stButton > button[key="clear_btn"] { background-color: #dc3545 !important; }
    input { height: 3em !important; font-size: 16px !important; }
    .result-box {
        background-color: #f8f9fa; padding: 15px; border-radius: 12px;
        border: 1px solid #dee2e6; margin: 10px 0;
    }
    .step-log {
        background-color: #ffffff; padding: 10px; border-left: 4px solid #007bff;
        margin-bottom: 10px; font-family: sans-serif; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    iframe { border: 1px solid #ddd !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state: st.session_state.edges = [] 
if 'nodes' not in st.session_state: st.session_state.nodes = set()

st.title("📍 Tìm đường đi có tổng trọng số nhỏ nhất")

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

path_nodes, best_edge_ids, total_dist = [], [], 0

if st.session_state.nodes:
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT", expanded=True):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Điểm đi", sorted(list(st.session_state.nodes)))
        end_node = c2.selectbox("Điểm đến", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 TÌM!!"):
            # --- TỰ TRIỂN KHAI DIJKSTRA ĐỂ LẤY BƯỚC GIẢI ---
            adj = {node: [] for node in st.session_state.nodes}
            for e in st.session_state.edges:
                adj[e['from']].append({'to': e['to'], 'w': e['weight'], 'id': e['id']})
                adj[e['to']].append({'to': e['from'], 'w': e['weight'], 'id': e['id']})

            dist = {node: float('inf') for node in st.session_state.nodes}
            dist[start_node] = 0
            parent = {node: None for node in st.session_state.nodes}
            p_edge = {node: None for node in st.session_state.nodes}
            visited = set()
            steps_output = []

            # Thuật toán bắt đầu
            nodes_to_visit = list(st.session_state.nodes)
            
            while nodes_to_visit:
                # Tìm đỉnh có dist nhỏ nhất
                curr = None
                for n in nodes_to_visit:
                    if curr is None or dist[n] < dist[curr]:
                        curr = n
                
                if dist[curr] == float('inf'): break
                
                nodes_to_visit.remove(curr)
                visited.add(curr)
                
                step_text = f"🔍 **Bước {len(visited)}**: Xét đỉnh **{curr}** (Khoảng cách hiện tại: {dist[curr]})"
                update_texts = []

                for edge in adj[curr]:
                    neighbor = edge['to']
                    if neighbor not in visited:
                        new_d = dist[curr] + edge['w']
                        if new_d < dist[neighbor]:
                            old_d = "∞" if dist[neighbor] == float('inf') else dist[neighbor]
                            update_texts.append(f"&nbsp;&nbsp;&nbsp;&nbsp;➡️ Cập nhật đỉnh **{neighbor}**: {old_d} -> **{new_d}** (qua {curr})")
                            dist[neighbor] = new_d
                            parent[neighbor] = curr
                            p_edge[neighbor] = edge['id']
                
                steps_output.append({"title": step_text, "updates": update_texts})
                if curr == end_node: break

            # Truy vết kết quả
            if dist[end_node] != float('inf'):
                temp = end_node
                while temp:
                    path_nodes.append(temp)
                    if p_edge[temp]: best_edge_ids.append(p_edge[temp])
                    temp = parent[temp]
                path_nodes.reverse()
                total_dist = dist[end_node]

                # HIỂN THỊ KẾT QUẢ (Giữ nguyên style cũ)
                st.markdown(f"""
                    <div class="result-box">
                        <p style="margin:0; font-size:1.1em;"><b>Lộ trình:</b> {' ➔ '.join(path_nodes)}</p>
                        <p style="margin:0; font-size:1.1em;"><b>Tổng độ dài:</b> <span style="color:red; font-weight:bold;">{total_dist}</span></p>
                    </div>
                """, unsafe_allow_html=True)

                # HIỂN THỊ CÁC BƯỚC GIẢI THÍCH (Trực quan cho học sinh)
                st.write("### 🧠 Các bước thực hiện thuật toán:")
                for step in steps_output:
                    with st.container():
                        st.markdown(f'<div class="step-log">{step["title"]}</div>', unsafe_allow_html=True)
                        if step["updates"]:
                            for up in step["updates"]:
                                st.markdown(up, unsafe_allow_html=True)
                        else:
                            st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;*Không có đỉnh kề nào cần cập nhật.*")
            else:
                st.error("Không có đường nối giữa hai điểm này!")

st.write("---")
col_util1, col_util2 = st.columns([1, 1])
if col_util1.button("🗑️ XÓA ĐỒ THỊ", key="clear_btn"):
    st.session_state.edges, st.session_state.nodes = [], set()
    components.html("<script>localStorage.clear(); window.parent.location.reload();</script>")
    st.rerun()

net = Network(height="550px", width="100%", bgcolor="#ffffff", font_color="black")
net.set_options("""
{
  "physics": {"enabled": false},
  "interaction": {"navigationButtons": true, "keyboard": true, "zoomView": true, "dragView": true},
  "nodes": {"font": {"size": 20, "strokeWidth": 5, "strokeColor": "white"}}
}
""")

for node in st.session_state.nodes:
    is_p = node in path_nodes
    net.add_node(node, label=node, color="#FF1E1E" if is_p else "#2196F3", size=30 if is_p else 25)

tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    tracker[pair] = tracker.get(pair, 0) + 1
    is_p = e['id'] in best_edge_ids
    net.add_edge(e['from'], e['to'], label=str(e['weight']), 
                 color="#FF1E1E" if is_p else "#D3D3D3", 
                 width=8 if is_p else 2, 
                 smooth={"type": "curvedCW", "roundness": 0.2 * (tracker[pair]-1) if tracker[pair]>1 else 0},
                 font={'background': 'white', 'size': 14})

raw_html = net.generate_html()
# Chèn JS cũ để giữ vị trí đỉnh
custom_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var savedPos = JSON.parse(localStorage.getItem('nodePositions') || '{}');
        Object.keys(savedPos).forEach(function(id) { network.moveNode(id, savedPos[id].x, savedPos[id].y); });
        
        var savedView = JSON.parse(localStorage.getItem('graphView') || '{}');
        if(savedView.scale) network.moveTo({position: savedView.position, scale: savedView.scale});

        network.on("dragEnd", function(params) {
            if (params.nodes.length > 0) {
                var id = params.nodes[0];
                var pos = network.getPositions([id])[id];
                var curPos = JSON.parse(localStorage.getItem('nodePositions') || '{}');
                curPos[id] = pos;
                localStorage.setItem('nodePositions', JSON.stringify(curPos));
            }
        });
        network.on("moveEnd", function() {
            localStorage.setItem('graphView', JSON.stringify({position: network.getViewPosition(), scale: network.getScale()}));
        });
    }, 500); 
});
</script>
"""
components.html(raw_html.replace("</body>", custom_js + "</body>"), height=600)
