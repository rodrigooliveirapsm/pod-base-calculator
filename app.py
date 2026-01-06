import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pod Ply Base Calculator", page_icon="🔨", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    h1 { color: #2E86C1; } 
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- GENERIC DRAWING ENGINE ---
def draw_pod_diagram(length, span, centers, panels, title, gap_val):
    # Safety Check: If span or length is 0, don't try to draw
    if length <= 0 or span <= 0: return None
    
    fig, ax = plt.subplots(figsize=(12, 9)) 
    
    # CONSTANTS
    FASCIA_W = 45
    BEARER_W = 90
    
    # 1. Setup Canvas
    ax.set_xlim(-200, span + 200)
    ax.set_ylim(-300, length + 200) 
    
    ax.set_xlabel("Pod Span (mm)")
    ax.set_ylabel("Bearer Length (mm)")
    ax.set_title(title, fontsize=14, pad=15)
    
    # 2. Draw Timber Frame
    # Fascias
    ax.add_patch(patches.Rectangle((0, 0), FASCIA_W, length, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    ax.add_patch(patches.Rectangle((span - FASCIA_W, 0), FASCIA_W, length, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    
    # Bearers
    for i, c in enumerate(centers):
        bx = c - (BEARER_W / 2)
        ax.add_patch(patches.Rectangle((bx, 0), BEARER_W, length, linewidth=0.5, edgecolor='black', facecolor='#D7CCC8'))
        ax.axvline(x=c, color='black', linestyle='--', alpha=0.3, linewidth=0.5)
        ax.text(c, length + 50, f"B{i+1}", ha='center', fontsize=9, fontweight='bold', color='#5D4037')

    # 3. Draw Gap Dimensions (AT THE BOTTOM)
    if len(centers) >= 2:
        for i in range(len(centers) - 1):
            b_left_edge = centers[i] + (BEARER_W / 2)
            b_right_edge = centers[i+1] - (BEARER_W / 2)
            dim_y = -100 
            
            ax.annotate(
                text="", 
                xy=(b_left_edge, dim_y), 
                xytext=(b_right_edge, dim_y),
                arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=1.0)
            )
            mid_x = (b_left_edge + b_right_edge) / 2
            ax.text(mid_x, dim_y - 50, f"{gap_val:.0f}", 
                    ha='center', va='center', fontsize=9, color='#C0392B', fontweight='bold')

    # 4. Draw Plywood Panels
    colors = ['#29B6F6', '#4FC3F7', '#81D4FA']
    for idx, p in enumerate(panels):
        rect = patches.Rectangle(
            (p['x'], p['y']), p['w'], p['l'], 
            linewidth=1.5, edgecolor='#01579B', facecolor=colors[idx % 3], alpha=0.5
        )
        ax.add_patch(rect)
        if p['w'] > 100 and p['l'] > 200:
            mid_x = p['x'] + (p['w'] / 2)
            mid_y = p['y'] + (p['l'] / 2)
            ax.text(mid_x, mid_y, f"{p['l']:.0f}x{p['w']:.0f}", 
                    ha='center', va='center', fontsize=8, color='white', fontweight='bold',
                    bbox=dict(facecolor='black', alpha=0.3, edgecolor='none', pad=1))

    ax.set_aspect('equal', adjustable='datalim')
    plt.grid(False)
    return fig

# --- HELPER: SPLIT LENGTH ---
def split_panel_length(total_len, width, start_x, row_name, sheet_max=2400):
    table_rows = []
    plot_data = []
    remaining = total_len
    current_y = 0
    part = 1
    
    while remaining > 0:
        cut_len = min(remaining, sheet_max)
        table_rows.append({
            "Qty": 1,
            "Type": f"{row_name} (Part {part})",
            "Size": f"{cut_len:.0f} x {width:.1f} mm"
        })
        plot_data.append({
            'x': start_x, 'y': current_y, 'w': width, 'l': cut_len
        })
        current_y += cut_len
        remaining -= cut_len
        part += 1
    return table_rows, plot_data

# --- CALCULATION ENGINE ---
def calculate_pod_cuts(length, span, supports):
    # Safety Check: Return "INVALID" if inputs are 0 or empty
    if length <= 0 or span <= 0 or supports < 2:
        return "INVALID"

    results = {}
    FASCIA_W = 45
    BEARER_W = 90
    SHEET_MAX_L = 2400
    
    # 1. SPACING
    first_center = FASCIA_W + (BEARER_W / 2)
    last_center = span - (FASCIA_W + (BEARER_W / 2))
    dist = last_center - first_center
    
    # Prevent division by zero if supports=1 (though caught by check above)
    spacing_cc = dist / (supports - 1)
    gap = spacing_cc - BEARER_W
    
    results['spacing_cc'] = spacing_cc
    results['gap'] = gap
    centers = [first_center + (i * spacing_cc) for i in range(supports)]
    results['centers'] = centers
    
    # 2. MODULAR (OFFCUTS)
    end_panel_w = first_center + spacing_cc
    mid_panel_w = spacing_cc
    mid_qty = max(0, supports - 3)
    
    modular_list = []      
    modular_plot_data = [] 
    current_x = 0
    
    if supports == 2:
        t, p = split_panel_length(length, span, 0, "Full Span", SHEET_MAX_L)
        modular_list.extend(t)
        modular_plot_data.extend(p)
    else:
        # Start
        t, p = split_panel_length(length, end_panel_w, 0, "Start Panel", SHEET_MAX_L)
        modular_list.extend(t)
        modular_plot_data.extend(p)
        current_x += end_panel_w
        # Mid
        if mid_qty > 0:
            for i in range(mid_qty):
                t, p = split_panel_length(length, mid_panel_w, current_x, "Mid Panel", SHEET_MAX_L)
                modular_list.extend(t)
                modular_plot_data.extend(p)
                current_x += mid_panel_w
        # End
        t, p = split_panel_length(length, end_panel_w, current_x, "End Panel", SHEET_MAX_L)
        modular_list.extend(t)
        modular_plot_data.extend(p)

    results['modular_df'] = pd.DataFrame(modular_list)
    results['modular_plot'] = modular_plot_data

    # 3. OPTIMIZED (FULL SHEETS)
    if length <= 1200: sheet_reach = 2400 
    else: sheet_reach = 1200 
    
    optimized_list = []      
    optimized_plot_data = [] 
    current_pos = 0
    row_num = 1
    
    while current_pos < span:
        target = round(current_pos + sheet_reach, 2)
        if target >= span:
            strip_width = span - current_pos
            joint_note = "Edge"
        else:
            valid = [p for p in centers if p <= target and p > current_pos]
            if not valid: return "ERROR"
            snap = valid[-1]
            strip_width = snap - current_pos

        remaining_len = length
        current_y = 0
        part_num = 1
        
        while remaining_len > 0:
            cut_len = min(remaining_len, SHEET_MAX_L)
            
            optimized_list.append({
                "Cut ID": f"Row {row_num}.{part_num}",
                "Width": f"{strip_width:.1f}",
                "Length": f"{cut_len:.0f}"
            })
            
            optimized_plot_data.append({
                'x': current_pos, 'y': current_y, 'w': strip_width, 'l': cut_len
            })
            current_y += cut_len
            remaining_len -= cut_len
            part_num += 1
            
        current_pos += strip_width
        if target >= span: break
        row_num += 1
        
    results['optimized_df'] = pd.DataFrame(optimized_list)
    results['optimized_plot'] = optimized_plot_data
    return results

# --- UI LAYOUT ---
st.title("🔨 Pod Ply Base Calculator")

with st.container():
    st.write("---")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        # Min Value is 0 now. User can clear the field.
        bearer_len = st.number_input("Bearer Length", value=3114, step=10, min_value=0)
    with c2:
        num_bearers = st.number_input("Total Bearers", value=7, step=1, min_value=0)
    with c3:
        total_span = st.number_input("Total Pod Span", value=3504, step=10, min_value=0)
    st.write("---")

if st.button("Generate Cut Plan", type="primary", use_container_width=True):
    
    # 1. Validation Logic
    if bearer_len == 0 or num_bearers == 0 or total_span == 0:
        st.warning("⚠️ Please enter all dimensions. Fields cannot be 0.")
    elif num_bearers < 2:
        st.error("❌ You must have at least 2 bearers to calculate spacing.")
    
    # 2. Calculation Logic
    else:
        data = calculate_pod_cuts(bearer_len, total_span, num_bearers)
        
        if data == "ERROR":
            st.error("❌ Error: Bearer spacing is too wide for standard plywood sheets.")
        elif data == "INVALID":
            st.error("❌ Invalid inputs.")
        else:
            # TABS
            tab_vis, tab_data, tab_info = st.tabs(["🖼️ Visual Plans", "📊 Cut Lists", "ℹ️ Spacing Info"])
            
            with tab_vis:
                st.info("💡 **Modular** shows alignment to bearers. **Optimized** shows actual sheet sizes.")
                sub_v1, sub_v2 = st.tabs(["Option A: Modular (Offcuts)", "Option B: Optimized (Full Sheets)"])
                
                with sub_v1:
                    fig1 = draw_pod_diagram(bearer_len, total_span, data['centers'], data['modular_plot'], "Modular Layout", data['gap'])
                    if fig1: st.pyplot(fig1)
                
                with sub_v2:
                    fig2 = draw_pod_diagram(bearer_len, total_span, data['centers'], data['optimized_plot'], "Optimized Layout", data['gap'])
                    if fig2: st.pyplot(fig2)

            with tab_data:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("A. Modular List")
                    st.dataframe(data['modular_df'], hide_index=True, use_container_width=True)
                with c2:
                    st.subheader("B. Optimized List")
                    st.dataframe(data['optimized_df'], hide_index=True, use_container_width=True)
                
            with tab_info:
                st.metric("Center-to-Center Spacing", f"{data['spacing_cc']:.1f} mm")
                st.metric("Clear Gap Between Timber", f"{data['gap']:.1f} mm")
