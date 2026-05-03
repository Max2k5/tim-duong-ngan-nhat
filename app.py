import streamlit as st
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(page_title="Học tập Thuật toán Dijkstra", layout="wide")

# Giữ nguyên phần CSS của bạn
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
    .step-header { color: #007bff; font-weight: bold; margin-top: 20px; }
    iframe { border: 1px solid #ddd !important; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# Khởi tạo dữ liệu
if 'edges' not in st.session_state: st.session_state.edges = [] 
if 'nodes' not in st.session_state: st.session_state.nodes = set()

def dijkstra_with_steps(nodes, edges, start_node, end_node):
    # Tạo danh sách kề
    adj = {node: [] for node in nodes}
    for e in edges:
        adj[e['from']].append((e['to'], e['weight'], e['id']))
        adj[e['to']].append((e['from'], e['weight'], e['id']))

    # Khởi tạo nhãn
    distances = {node: float('inf') for node in nodes}
    distances[start_node] = 0
    predecessors = {node: None for node in nodes}
    edge_used = {node: None for node in nodes}
    visited = set()
    logs = []

    nodes_sorted = sorted(list(nodes))
    
    while len(visited) < len(nodes):
        # Chọn đỉnh có khoảng cách nhỏ nhất chưa duyệt (Lựa chọn tham lam)
        unvisited = {n: distances[n] for n in nodes if n not in visited}
        if not unvisited or min(unvisited.values()) == float('inf'):
            break
            
        current_node = min(unvisited, key=unvisited.get)
        
        # Ghi lại trạng thái trước khi cập nhật các láng giềng
        current_log = {
            "Bước": len(logs) + 1,
            "Đỉnh chọn": current_node,
            "Trạng thái nhãn": {n: (distances[n] if distances[n] != float('inf') else "∞") for n in nodes_sorted}
        }
        logs.append(current_log)
        
        if current_node == end_node:
            break
            
        visited.add(current_node)

        # Cập nhật khoảng cách các đỉnh kề
        for neighbor, weight, eid in adj[current_node]:
            if neighbor not in visited:
                new_dist = distances[current_node] + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    predecessors[neighbor] = current_node
                    edge_used[neighbor] = eid

    # Truy vết đường đi
    path = []
    path_edges = []
    curr = end_node
    if distances[end_node] != float('inf'):
        while curr is not None:
            path.append(curr)
            if edge_used[curr]:
                path_edges.append(edge_used[curr])
            curr = predecessors[curr]
        path.reverse()

    return path, path_edges, distances[end_node], logs

st.title("📍 Minh họa từng bước Thuật toán Dijkstra")

with st.expander("➕ QUẢN LÝ ĐỒ THỊ (Thêm đỉnh & cạnh)", expanded=True):
    col1, col2, col3 = st.columns([1, 1, 1])
    u = col1.text_input("Từ điểm (A, B, C...)").upper().strip()
    v = col2.text_input("Đến điểm").upper().strip()
    w = col3.number_input("Trọng số (Khoảng cách)", min_value=0.1, value=5.0)
    
    if st.button("Thêm đường nối"):
        if u and v and u != v:
            edge_id = f"{u}-{v}-{len(st.session_state.edges)}"
            st.session_state.edges.append({'from': u, 'to': v, 'weight': w, 'id': edge_id})
            st.session_state.nodes.add(u)
            st.session_state.nodes.add(v)
            st.rerun()

path_nodes, best_edge_ids, total_dist = [], [], 0

if st.session_state.nodes:
    with st.expander("🚩 THỰC HIỆN GIẢI THUẬT", expanded=True):
        c1, c2 = st.columns(2)
        start_node = c1.selectbox("Chọn điểm bắt đầu", sorted(list(st.session_state.nodes)))
        end_node = c2.selectbox("Chọn điểm kết thúc", sorted(list(st.session_state.nodes)))
        
        if st.button("🚀 BẮT ĐẦU PHÂN TÍCH"):
            path_nodes, best_edge_ids, total_dist, logs = dijkstra_with_steps(
                st.session_state.nodes, st.session_state.edges, start_node, end_node
            )
            
            if not path_nodes:
                st.error("Không tìm thấy đường đi!")
            else:
                # Hiển thị kết quả tổng quát
                st.markdown(f"""
                    <div class="result-box">
                        <p style="margin:0; font-size:1.2em;"><b>Kết quả cuối cùng:</b></p>
                        <p style="margin:0; font-size:1.1em;">Đường đi: {' ➔ '.join(path_nodes)}</p>
                        <p style="margin:0; font-size:1.1em;">Tổng trọng số: <span style="color:red; font-weight:bold;">{total_dist}</span></p>
                    </div>
                """, unsafe_allow_html=True)

                # Hiển thị bảng chi tiết các bước cho học sinh
                st.write("### 📊 Bảng phân tích chi tiết từng bước (Trace Table)")
                df_logs = []
                for log in logs:
                    row = {"Bước": log["Bước"], "Đỉnh chọn": log["Đỉnh chọn"]}
                    row.update(log["Trạng thái nhãn"])
                    df_logs.append(row)
                
                st.table(pd.DataFrame(df_logs))
                st.info("💡 Giải thích: Tại mỗi bước, thuật toán chọn đỉnh có nhãn nhỏ nhất (vàng) để 'tối ưu hóa' các đỉnh kề xung quanh nó.")

st.write("---")
# Phần hiển thị đồ thị và các chức năng phụ khác giữ nguyên
col_util1, col_util2 = st.columns([1, 1])
if col_util1.button("🗑️ XÓA DỮ LIỆU", key="clear_btn"):
    st.session_state.edges, st.session_state.nodes = [], set()
    components.html("<script>localStorage.clear(); window.parent.location.reload();</script>")
    st.rerun()

# --- PHẦN TRỰC QUAN HÓA ĐỒ THỊ ---
net = Network(height="500px", width="100%", bgcolor="#ffffff", font_color="black", notebook=False)
net.set_options("""
{
  "physics": {"enabled": false},
  "interaction": {"navigationButtons": true, "zoomView": true},
  "nodes": {"font": {"size": 20}}
}
""")

for node in st.session_state.nodes:
    is_p = node in path_nodes
    color = "#28a745" if node == start_node else ("#dc3545" if node == end_node else "#2196F3")
    if is_p and node != start_node and node != end_node: color = "#FF1E1E"
    net.add_node(node, label=node, color=color, size=30 if is_p else 25)

tracker = {}
for e in st.session_state.edges:
    pair = tuple(sorted((e['from'], e['to'])))
    tracker[pair] = tracker.get(pair, 0) + 1
    is_p = e['id'] in best_edge_ids
    net.add_edge(e['from'], e['to'], label=str(e['weight']), 
                 color="#FF1E1E" if is_p else "#D3D3D3", 
                 width=7 if is_p else 2, 
                 smooth={"type": "curvedCW", "roundness": 0.2 * (tracker[pair]-1) if tracker[pair]>1 else 0})

raw_html = net.generate_html()
components.html(raw_html.replace("</body>", "</body>"), height=550)
