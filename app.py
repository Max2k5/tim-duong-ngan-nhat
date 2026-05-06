import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Đường Đi Ngắn Nhất & Lý Thuyết Đồ Thị", layout="wide")

# Giữ nguyên CSS cũ
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
    .theory-box {
        background-color: #fff3cd; padding: 15px; border-radius: 12px;
        border: 1px solid #ffeeba; margin: 10px 0; color: #856404;
    }
    iframe { border: 1px solid #ddd !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state: st.session_state.edges = [] 
if 'nodes' not in st.session_state: st.session_state.nodes = set()

# Biến dùng chung để tô màu đồ thị
path_nodes, best_edge_ids = [], []

st.title("📍 Tìm đường đi ngắn nhất & Phân tích Đồ thị")

with st.expander("➕ THÊM ĐƯỜNG NỐI", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1])
    u = col1.text_input("Từ điểm").upper().strip()
    v = col2.text_input("Đến điểm").upper().strip()
    w = col3.number_input("Khoảng cách", min_value=0.1, value=5.0)
    
    if st.button("Thêm đường nối"):
        if u and v and u != v:
            existing_edge = next((e for e in st.session_state.edges if (e['from'] == u and e['to'] == v) or (e['from'] == v and e['to'] == u)), None)
            if existing_edge:
                existing_edge['weight'] = w
            else:
                edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
                st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
                st.session_state.nodes.add(u); st.session_state.nodes.add(v)
            st.rerun()

# Tạo đồ thị NetworkX để tính toán
G_simple = nx.Graph()
for e in st.session_state.edges:
    G_simple.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])

# --- PHẦN 1: DIJKSTRA (GIỮ NGUYÊN) ---
if st.session_state.nodes:
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT (DIJKSTRA)", expanded=False):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Điểm đi", sorted(list(st.session_state.nodes)), key="dijk_start")
        end_node = c2.selectbox("Điểm đến", sorted(list(st.session_state.nodes)), key="dijk_end")
        if st.button("🚀 TÌM ĐƯỜNG NGẮN NHẤT"):
            dist = {n: float('inf') for n in st.session_state.nodes}; dist[start_node] = 0
            parent = {n: None for n in st.session_state.nodes}; p_edge = {n: None for n in st.session_state.nodes}
            visited = set(); nodes_to_visit = list(st.session_state.nodes)
            while nodes_to_visit:
                curr = min(nodes_to_visit, key=lambda n: dist[n])
                if dist[curr] == float('inf'): break
                nodes_to_visit.remove(curr); visited.add(curr)
                for neighbor in G_simple.neighbors(curr):
                    if neighbor not in visited:
                        weight = G_simple[curr][neighbor]['weight']
                        if dist[curr] + weight < dist[neighbor]:
                            dist[neighbor] = dist[curr] + weight
                            parent[neighbor] = curr
                            p_edge[neighbor] = G_simple[curr][neighbor]['id']
                if curr == end_node: break
            if dist[end_node] != float('inf'):
                temp = end_node
                while temp:
                    path_nodes.append(temp)
                    if p_edge[temp]: best_edge_ids.append(p_edge[temp])
                    temp = parent[temp]
                path_nodes.reverse()
                st.success(f"Đường đi ngắn nhất: {' ➔ '.join(path_nodes)} (Tổng: {dist[end_node]})")

    # --- PHẦN 2: PHÂN TÍCH EULER ---
    with st.expander("📐 PHÂN TÍCH EULER", expanded=False):
        if st.button("🔍 KIỂM TRA EULER"):
            degrees = dict(G_simple.degree())
            odd_nodes = [n for n, d in degrees.items() if d % 2 != 0]
            is_connected = nx.is_connected(G_simple) if len(st.session_state.nodes) > 0 else False
            
            # Liệt kê bậc các đỉnh
            deg_desc = ", ".join([f"Đỉnh {n} có bậc {d}" for n, d in sorted(degrees.items())])
            
            if is_connected and len(odd_nodes) == 0:
                st.info("✅ Đồ thị có Chu trình Euler")
                circuit = list(nx.eulerian_circuit(G_simple))
                path_nodes = [u for u, v in circuit] + [circuit[-1][1]]
                # Lấy edge IDs để tô màu
                for u_n, v_n in circuit:
                    best_edge_ids.append(G_simple[u_n][v_n]['id'])
                st.markdown(f"""<div class="theory-box"><b>Lý do:</b> Ta thấy các đỉnh: {deg_desc} đều là số chẵn và đồ thị này liên thông nên đồ thị này có chu trình Euler là: <b>{' ➔ '.join(path_nodes)}</b></div>""", unsafe_allow_html=True)
            
            elif is_connected and len(odd_nodes) == 2:
                st.info("✅ Đồ thị có Đường đi Euler")
                u_start, v_end = odd_nodes[0], odd_nodes[1]
                path_gen = list(nx.eulerian_path(G_simple, source=u_start))
                path_nodes = [u for u, v in path_gen] + [path_gen[-1][1]]
                for u_n, v_n in path_gen:
                    best_edge_ids.append(G_simple[u_n][v_n]['id'])
                st.markdown(f"""<div class="theory-box"><b>Lý do:</b> Ta thấy các đỉnh: {deg_desc} có đúng hai đỉnh <b>{u_start}</b> và <b>{v_end}</b> có bậc lẻ ({degrees[u_start]} và {degrees[v_end]}). Ngoài ra đồ thị liên thông nên có đường đi Euler là: <b>{' ➔ '.join(path_nodes)}</b></div>""", unsafe_allow_html=True)
            
            else:
                reason = "đồ thị không liên thông" if not is_connected else f"có {len(odd_nodes)} đỉnh bậc lẻ (nhiều hơn 2)"
                st.warning("❌ Không có đường đi hay chu trình Euler")
                st.markdown(f"""<div class="theory-box"><b>Lý do:</b> {deg_desc}. Đồ thị này không thỏa mãn điều kiện Euler vì {reason}.</div>""", unsafe_allow_html=True)

    # --- PHẦN 3: PHÂN TÍCH HAMILTON ---
    with st.expander("💎 PHÂN TÍCH HAMILTON", expanded=False):
        if st.button("🔍 KIỂM TRA HAMILTON"):
            n = len(st.session_state.nodes)
            degrees = dict(G_simple.degree())
            
            # Kiểm tra Ore/Dirac cho Chu trình
            dirac = all(d >= n/2 for d in degrees.values()) if n >= 3 else False
            ore = True
            non_adj_pairs = []
            if n >= 3:
                for i, u_node in enumerate(sorted(list(st.session_state.nodes))):
                    for v_node in sorted(list(st.session_state.nodes))[i+1:]:
                        if not G_simple.has_edge(u_node, v_node):
                            if degrees[u_node] + degrees[v_node] < n: ore = False
                            non_adj_pairs.append((u_node, v_node, degrees[u_node] + degrees[v_node]))
            else: ore = False

            # Thuật toán tìm Hamilton (Backtracking đơn giản cho học tập)
            def get_hamilton_path(graph):
                for start in graph.nodes():
                    for path in nx.all_simple_paths(graph, start, None):
                        if len(path) == n: return path
                return None

            def get_hamilton_circuit(graph):
                for start in graph.nodes():
                    for path in nx.all_simple_paths(graph, start, None):
                        if len(path) == n and graph.has_edge(path[-1], path[0]):
                            return path + [path[0]]
                return None

            h_circuit = get_hamilton_circuit(G_simple)
            h_path = get_hamilton_path(G_simple)

            if h_circuit:
                st.info("✅ Đồ thị có Chu trình Hamilton")
                path_nodes = h_circuit
                for i in range(len(path_nodes)-1): best_edge_ids.append(G_simple[path_nodes[i]][path_nodes[i+1]]['id'])
                
                reason = ""
                if dirac: reason = f"Thỏa định lý Dirac: n={n}, tất cả bậc đỉnh ≥ {n/2}."
                elif ore: reason = f"Thỏa định lý Ore: n={n}, mọi cặp đỉnh không kề nhau có tổng bậc ≥ {n}."
                else: reason = "Đồ thị có chu trình Hamilton (không phụ thuộc định lý Dirac/Ore)."
                
                st.markdown(f"""<div class="theory-box"><b>Lý do:</b> {reason}<br>Chu trình: <b>{' ➔ '.join(path_nodes)}</b></div>""", unsafe_allow_html=True)
            
            elif h_path:
                st.info("✅ Đồ thị có Đường đi Hamilton")
                path_nodes = h_path
                for i in range(len(path_nodes)-1): best_edge_ids.append(G_simple[path_nodes[i]][path_nodes[i+1]]['id'])
                
                path_cond = all(d >= (n-1)/2 for d in degrees.values()) if n >= 3 else False
                reason = f"Thỏa hệ quả: n={n}, mỗi đỉnh có bậc không nhỏ hơn (n-1)/2 = {(n-1)/2}." if path_cond else "Đồ thị có đường đi Hamilton dựa trên kiểm tra cấu trúc."
                
                st.markdown(f"""<div class="theory-box"><b>Lý do:</b> {reason}<br>Đường đi: <b>{' ➔ '.join(path_nodes)}</b></div>""", unsafe_allow_html=True)
            else:
                st.warning("❌ Không tìm thấy đường đi/chu trình Hamilton")

# --- PHẦN HIỂN THỊ ĐỒ THỊ (GIỮ NGUYÊN JS VÀ STYLE) ---
st.write("---")
col_util1, col_util2 = st.columns([1, 1])
if col_util1.button("🗑️ XÓA ĐỒ THỊ", key="clear_btn"):
    st.session_state.edges, st.session_state.nodes = [], set()
    components.html("<script>localStorage.clear(); window.parent.location.reload();</script>")
    st.rerun()

net = Network(height="550px", width="100%", bgcolor="#ffffff", font_color="black")
net.set_options('{"physics": {"enabled": false}, "interaction": {"navigationButtons": true}}')

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
                 smooth={"type": "curvedCW", "roundness": 0.2 * (tracker[pair]-1) if tracker[pair]>1 else 0})

raw_html = net.generate_html()
custom_js = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        var savedPos = JSON.parse(localStorage.getItem('nodePositions') || '{}');
        Object.keys(savedPos).forEach(function(id) { network.moveNode(id, savedPos[id].x, savedPos[id].y); });
        network.on("dragEnd", function(params) {
            if (params.nodes.length > 0) {
                var id = params.nodes[0];
                var pos = network.getPositions([id])[id];
                var curPos = JSON.parse(localStorage.getItem('nodePositions') || '{}');
                curPos[id] = pos;
                localStorage.setItem('nodePositions', JSON.stringify(curPos));
            }
        });
    }, 500); 
});
</script>
"""
components.html(raw_html.replace("</body>", custom_js + "</body>"), height=600)
