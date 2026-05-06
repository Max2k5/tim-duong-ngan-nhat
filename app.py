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
    .theory-box {
        background-color: #fff3cd; padding: 15px; border-radius: 12px;
        border: 1px solid #ffeeba; margin: 10px 0; color: #856404; line-height: 1.6;
    }
    iframe { border: 1px solid #ddd !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

if 'edges' not in st.session_state: st.session_state.edges = [] 
if 'nodes' not in st.session_state: st.session_state.nodes = set()

path_nodes, best_edge_ids = [], []

st.title("📍 Tìm đường đi có tổng trọng số nhỏ nhất")

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

# Khởi tạo đồ thị NetworkX
G_simple = nx.Graph()
G_simple.add_nodes_from(st.session_state.nodes) # Đảm bảo thêm đủ node kể cả khi cô lập
for e in st.session_state.edges:
    G_simple.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])

if st.session_state.nodes:
    # --- PHẦN 1: DIJKSTRA (GIỮ NGUYÊN) ---
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT", expanded=False):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Điểm đi", sorted(list(st.session_state.nodes)))
        end_node = c2.selectbox("Điểm đến", sorted(list(st.session_state.nodes)))
        if st.button("🚀 TÌM!!"):
            try:
                path_nodes = nx.shortest_path(G_simple, source=start_node, target=end_node, weight='weight')
                total_dist = nx.shortest_path_length(G_simple, source=start_node, target=end_node, weight='weight')
                for i in range(len(path_nodes)-1):
                    u_n, v_n = path_nodes[i], path_nodes[i+1]
                    best_edge_ids.append(G_simple[u_n][v_n]['id'])
                st.markdown(f'<div class="result-box"><b>Lộ trình:</b> {" ➔ ".join(path_nodes)}<br><b>Tổng độ dài:</b> <span style="color:red;">{total_dist}</span></div>', unsafe_allow_html=True)
            except: st.error("Không có đường nối!")

    # --- PHẦN 2: PHÂN TÍCH EULER ---
    with st.expander("📐 PHÂN TÍCH EULER", expanded=False):
        if st.button("🔍 KIỂM TRA EULER"):
            degrees = dict(G_simple.degree())
            odd_nodes = [n for n, d in degrees.items() if d % 2 != 0]
            is_connected = nx.is_connected(G_simple)
            deg_desc = ", ".join([f"Đỉnh <b>{n}</b> có bậc <b>{d}</b>" for n, d in sorted(degrees.items())])
            
            if is_connected and len(odd_nodes) == 0:
                circuit = list(nx.eulerian_circuit(G_simple))
                path_nodes = [u for u, v in circuit] + [circuit[-1][1]]
                best_edge_ids = [G_simple[u][v]['id'] for u, v in circuit]
                st.markdown(f'<div class="theory-box">Ta thấy các đỉnh: {deg_desc} đều là số chẵn và đồ thị này liên thông nên đồ thị này có chu trình Euler là: <b>{" ➔ ".join(path_nodes)}</b></div>', unsafe_allow_html=True)
            elif is_connected and len(odd_nodes) == 2:
                u_s, v_e = odd_nodes[0], odd_nodes[1]
                path_gen = list(nx.eulerian_path(G_simple, source=u_s))
                path_nodes = [u for u, v in path_gen] + [path_gen[-1][1]]
                best_edge_ids = [G_simple[u][v]['id'] for u, v in path_gen]
                st.markdown(f'<div class="theory-box">Ta thấy các đỉnh: {deg_desc} có đúng hai đỉnh <b>{u_s}</b> và <b>{v_e}</b> có bậc lẻ ({degrees[u_s]} và {degrees[v_e]}). Ngoài ra đồ thị liên thông nên có đường đi Euler là: <b>{" ➔ ".join(path_nodes)}</b></div>', unsafe_allow_html=True)
            else:
                st.warning("Không thỏa mãn điều kiện Euler.")

    # --- PHẦN 3: PHÂN TÍCH HAMILTON ---
    with st.expander("💎 PHÂN TÍCH HAMILTON", expanded=False):
        if st.button("🔍 KIỂM TRA HAMILTON"):
            n = len(st.session_state.nodes)
            degrees = dict(G_simple.degree())
            
            # Hàm tìm đường đi/chu trình Hamilton (Backtracking)
            def find_hamilton():
                all_nodes = list(st.session_state.nodes)
                def backtrack(curr, path):
                    if len(path) == n:
                        return path
                    for neighbor in G_simple.neighbors(curr):
                        if neighbor not in path:
                            res = backtrack(neighbor, path + [neighbor])
                            if res: return res
                    return None
                
                for start in all_nodes:
                    path = backtrack(start, [start])
                    if path:
                        # Kiểm tra chu trình
                        if G_simple.has_edge(path[-1], path[0]):
                            return path + [path[0]], "circuit"
                        return path, "path"
                return None, None

            res_path, res_type = find_hamilton()
            
            if res_path:
                path_nodes = res_path
                for i in range(len(path_nodes)-1):
                    best_edge_ids.append(G_simple[path_nodes[i]][path_nodes[i+1]]['id'])
                
                if res_type == "circuit":
                    # Giải thích Chu trình (Dirac/Ore)
                    dirac = all(d >= n/2 for d in degrees.values()) if n >= 3 else False
                    ore = True
                    if n >= 3:
                        for i, u_n in enumerate(sorted(list(st.session_state.nodes))):
                            for v_n in sorted(list(st.session_state.nodes))[i+1:]:
                                if not G_simple.has_edge(u_n, v_n) and degrees[u_n] + degrees[v_n] < n:
                                    ore = False; break
                    else: ore = False
                    
                    reason = "Đồ thị thỏa mãn chu trình Hamilton."
                    if dirac: reason = f"Thỏa định lý Dirac: $n={n} \geq 3$ và mọi đỉnh đều có bậc $\geq n/2 = {n/2}$."
                    elif ore: reason = f"Thỏa định lý Ore: $n={n} \geq 3$ và mọi cặp đỉnh không kề nhau đều có tổng bậc $\geq n = {n}$."
                    
                    st.markdown(f'<div class="theory-box"><b>Chu trình Hamilton:</b><br>{reason}<br>Lộ trình: <b>{" ➔ ".join(path_nodes)}</b></div>', unsafe_allow_html=True)
                else:
                    # Giải thích Đường đi
                    path_cond = all(d >= (n-1)/2 for d in degrees.values()) if n >= 3 else False
                    reason = "Đồ thị có đường đi Hamilton."
                    if path_cond: reason = f"Thỏa hệ quả: Đơn đồ thị có $n={n}$ đỉnh và mỗi đỉnh có bậc không nhỏ hơn $(n-1)/2 = {(n-1)/2}$."
                    st.markdown(f'<div class="theory-box"><b>Đường đi Hamilton:</b><br>{reason}<br>Lộ trình: <b>{" ➔ ".join(path_nodes)}</b></div>', unsafe_allow_html=True)
            else:
                st.warning("Không tìm thấy chu trình hoặc đường đi Hamilton.")

# --- PHẦN HIỂN THỊ ĐỒ THỊ ---
st.write("---")
if st.button("🗑️ XÓA ĐỒ THỊ", key="clear_btn"):
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
