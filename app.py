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

# --- 2. THÔNG BÁO & QUẢN LÝ ĐƯỜNG NỐI ---
with st.expander("➕ THÊM ĐƯỜNG NỐI", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1])
    u = col1.text_input("Từ điểm").upper().strip()
    v = col2.text_input("Đến điểm").upper().strip()
    
    # 3. Lựa chọn khoảng cách "Không có" (Đồ thị không trọng số)
    w_type = st.radio("Loại trọng số", ["Có giá trị", "Không có"], horizontal=True)
    if w_type == "Có giá trị":
        w = col3.number_input("Khoảng cách", min_value=0.1, value=5.0)
    else:
        w = 1.0 # Mặc định là 1 nếu không có trọng số

    if st.button("Thêm đường nối"):
        if u and v and u != v:
            existing_edge = next((e for e in st.session_state.edges if (e['from'] == u and e['to'] == v) or (e['from'] == v and e['to'] == u)), None)
            if existing_edge:
                existing_edge['weight'] = w
                st.success(f"✅ Đã cập nhật độ dài {u} - {v} thành {w if w_type == 'Có giá trị' else 'mặc định'}")
            else:
                edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
                st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id, 'is_weighted': (w_type == "Có giá trị")})
                st.session_state.nodes.add(u); st.session_state.nodes.add(v)
                st.success(f"✅ Đã thêm đường nối {u} - {v} thành công!")
            st.rerun()

G_simple = nx.Graph()
G_simple.add_nodes_from(st.session_state.nodes)
for e in st.session_state.edges:
    G_simple.add_edge(e['from'], e['to'], weight=e['weight'], id=e['id'])

if st.session_state.nodes:
    # --- DIJKSTRA ---
    with st.expander("🚩 TÌM ĐƯỜNG NGẮN NHẤT", expanded=False):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Điểm đi", sorted(list(st.session_state.nodes)))
        end_node = c2.selectbox("Điểm đến", sorted(list(st.session_state.nodes)))
        if st.button("🚀 TÌM!!"):
            try:
                path_nodes = nx.shortest_path(G_simple, source=start_node, target=end_node, weight='weight')
                total_dist = nx.shortest_path_length(G_simple, source=start_node, target=end_node, weight='weight')
                best_edge_ids = [G_simple[path_nodes[i]][path_nodes[i+1]]['id'] for i in range(len(path_nodes)-1)]
                st.markdown(f'<div class="result-box"><b>Lộ trình:</b> {" ➔ ".join(path_nodes)}<br><b>Tổng độ dài:</b> <span style="color:red;">{total_dist}</span></div>', unsafe_allow_html=True)
            except: st.error("Không có đường nối!")

    # --- 1. PHÂN TÍCH EULER (KHÔI PHỤC GIẢI THÍCH) ---
    with st.expander("📐 PHÂN TÍCH EULER", expanded=False):
        if st.button("🔍 KIỂM TRA EULER"):
            degrees = dict(G_simple.degree())
            odd_nodes = [n for n, d in degrees.items() if d % 2 != 0]
            is_connected = nx.is_connected(G_simple) if len(st.session_state.nodes) > 1 else True
            deg_desc = ", ".join([f"đỉnh <b>{n}</b> bậc <b>{d}</b>" for n, d in sorted(degrees.items())])
            
            if not is_connected:
                st.warning("❌ Đồ thị không liên thông, không thể có chu trình/đường đi Euler.")
            elif len(odd_nodes) == 0:
                circuit = list(nx.eulerian_circuit(G_simple))
                path_nodes = [u for u, v in circuit] + [circuit[-1][1]]
                best_edge_ids = [G_simple[u][v]['id'] for u, v in circuit]
                st.markdown(f'<div class="theory-box">Ta thấy các đỉnh: {deg_desc} đều là số chẵn và đồ thị liên thông nên đồ thị này có <b>chu trình Euler</b>: <br><b>{" ➔ ".join(path_nodes)}</b></div>', unsafe_allow_html=True)
            elif len(odd_nodes) == 2:
                u_s, v_e = odd_nodes[0], odd_nodes[1]
                path_gen = list(nx.eulerian_path(G_simple, source=u_s))
                path_nodes = [u for u, v in path_gen] + [path_gen[-1][1]]
                best_edge_ids = [G_simple[u][v]['id'] for u, v in path_gen]
                st.markdown(f'<div class="theory-box">Ta thấy các đỉnh: {deg_desc} có đúng hai đỉnh <b>{u_s}</b> và <b>{v_e}</b> có bậc lẻ. Ngoài ra đồ thị liên thông nên có <b>đường đi Euler</b> từ {u_s} đến {v_e}: <br><b>{" ➔ ".join(path_nodes)}</b></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="theory-box">Ta thấy các đỉnh: {deg_desc}. Vì đồ thị có <b>{len(odd_nodes)} đỉnh bậc lẻ</b> (không phải 0 hoặc 2) nên <b>không tồn tại</b> chu trình hay đường đi Euler.</div>', unsafe_allow_html=True)

with st.expander("💎 PHÂN TÍCH HAMILTON", expanded=False):
        if st.button("🔍 KIỂM TRA HAMILTON"):
            n = len(st.session_state.nodes)
            degrees = dict(G_simple.degree())
            nodes_sorted = sorted(list(st.session_state.nodes))
            
            # 1. Kiểm tra các điều kiện định lý đủ
            # Định lý Dirac (cho chu trình)
            dirac_ok = n >= 3 and all(d >= n/2 for d in degrees.values())
            
            # Định lý Ore (cho chu trình)
            ore_ok = True
            if n >= 3:
                for i, u_n in enumerate(nodes_sorted):
                    for v_n in nodes_sorted[i+1:]:
                        if not G_simple.has_edge(u_n, v_n):
                            if degrees[u_n] + degrees[v_n] < n:
                                ore_ok = False; break
                    if not ore_ok: break
            else: ore_ok = False

            # Định lý 4 (cho đường đi) - Theo sách Kết nối tri thức
            path_theorem_ok = n >= 3 and all(d >= (n-1)/2 for d in degrees.values())

            # 2. Thuật toán quay lui tìm lộ trình thực tế
            def find_hamilton():
                def backtrack(curr, path):
                    if len(path) == n: return path
                    for neighbor in G_simple.neighbors(curr):
                        if neighbor not in path:
                            res = backtrack(neighbor, path + [neighbor])
                            if res: return res
                    return None
                for start in nodes_sorted:
                    p = backtrack(start, [start])
                    if p:
                        if G_simple.has_edge(p[-1], p[0]): return p + [p[0]], "circuit"
                        return p, "path"
                return None, None

            res_path, res_type = find_hamilton()
            
            # 3. Hiển thị thông tin bậc đỉnh
            deg_info = ", ".join([f"<b>{node}</b> (bậc {d})" for node, d in degrees.items()])
            st.markdown(f"Số đỉnh $n = {n}$. Bậc các đỉnh: {deg_info}", unsafe_allow_html=True)

            if res_path:
                path_nodes = res_path
                best_edge_ids = [G_simple[path_nodes[i]][path_nodes[i+1]]['id'] for i in range(len(path_nodes)-1)]
                
                if res_type == "circuit":
                    status = "✅ Đồ thị có <b>chu trình Hamilton</b>."
                    if dirac_ok:
                        reason = f"Thỏa <b>định lý Dirac</b> ($d(v) \geq n/2 = {n/2}$)."
                    elif ore_ok:
                        reason = f"Thỏa <b>định lý Ore</b> (mọi cặp đỉnh không kề có tổng bậc $\geq n = {n}$)."
                    else:
                        reason = "Đồ thị có chu trình Hamilton (không thỏa định lý đủ Dirac/Ore)."
                else:
                    status = "✅ Đồ thị có <b>đường đi Hamilton</b>."
                    if path_theorem_ok:
                        reason = (f"Thỏa mãn <b>Định lý 4</b>: Trong đơn đồ thị có {n} đỉnh, "
              f"vì mỗi đỉnh đều có bậc không nhỏ hơn {(n-1)/2}, "
              f"nên đồ thị chắc chắn có một đường đi Hamilton.")
                    else:
                        reason = "Đồ thị tìm thấy đường đi Hamilton bằng thuật toán (không thỏa định lý 4</b>)."

                st.markdown(f'<div class="theory-box">{status}<br><b>Giải thích:</b> {reason}<br>Lộ trình: <b>{" ➔ ".join(path_nodes)}</b></div>', unsafe_allow_html=True)
            else:
                st.warning("❌ Không tìm thấy chu trình hay đường đi Hamilton.")
                st.info(f"Lưu ý: Với $n={n}$, mọi đỉnh cần có bậc $\geq {(n-1)/2}$ để chắc chắn có đường đi Hamilton.")

# --- HIỂN THỊ ĐỒ THỊ ---
st.write("---")
c1, c2 = st.columns([3, 1]) # Chia tỷ lệ 3:1 để nút xóa nằm gọn bên phải
with c1:
    show_labels = st.checkbox("Hiển thị trọng số trên hình", value=True)
with c2:
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
    
    # 3. Xử lý hiển thị nhãn trọng số
    edge_label = ""
    if show_labels:
        edge_label = str(e['weight']) if e.get('is_weighted', True) else ""

    net.add_edge(e['from'], e['to'], label=edge_label, 
                 color="#FF1E1E" if is_p else "#D3D3D3", width=8 if is_p else 2, 
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
