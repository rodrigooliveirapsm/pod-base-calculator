import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import colorsys

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

# --- HELPER: ADJUST COLOR LIGHTNESS ---
def adjust_lightness(color, amount=0.5):
    try:
        c = mcolors.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mcolors.to_rgb(c))
    new_l = max(0, min(1, amount * c[1]))
    rgb = colorsys.hls_to_rgb(c[0], new_l, c[2])
    return mcolors.to_hex(rgb)

# --- GENERIC DRAWING ENGINE ---
def draw_pod_diagram(base_width, base_length, centers, panels, title, gap_val, cc_val):
    if base_width <= 0 or base_length <= 0: return None
    
    # Increase height to accommodate dual dimension lines at bottom
    fig, ax = plt.subplots(figsize=(12, 11)) 
    
    # CONSTANTS
    FASCIA_W = 45
    BEARER_W = 90
    
    # 1. Setup Canvas
    # Extend bottom limit (-450) to fit both dimension rows
    ax.set_xlim(-300, base_length + 300)
    ax.set_ylim(-450, base_width + 300) 
    ax.axis('off')
    
    ax.text(base_length/2, base_width + 250, title, ha='center', fontsize=14, weight='bold', color='#333')
    
    # 2. Draw Timber Frame
    ax.add_patch(patches.Rectangle((0, 0), FASCIA_W, base_width, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    ax.add_patch(patches.Rectangle((base_length - FASCIA_W, 0), FASCIA_W, base_width, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    
    for i, c in enumerate(centers):
        bx = c - (BEARER_W / 2)
        ax.add_patch(patches.Rectangle((bx, 0), BEARER_W, base_width, linewidth=0.5, edgecolor='black', facecolor='#D7CCC8'))
        ax.axvline(x=c, color='black', linestyle='--', alpha=0.3, linewidth=0.5)
        ax.text(c, base_width + 40, f"B{i+1}", ha='center', fontsize=9, fontweight='bold', color='#5D4037')

    # 3. Draw External Dimensions (Frame)
    # Top (Length)
    dim_y_top = base_width + 150
    ax.annotate("", xy=(0, dim_y_top), xytext=(base_length, dim_y_top), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(base_length/2, dim_y_top + 20, f"Base Length: {base_length:.0f} mm", ha='center', va='bottom', fontsize=11, fontweight='bold')
            
    # Left (Width)
    dim_x_left = -150
    ax.annotate("", xy=(dim_x_left, 0), xytext=(dim_x_left, base_width), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(dim_x_left - 20, base_width/2, f"Base Width: {base_width:.0f} mm", ha='right', va='center', fontsize=11, fontweight='bold', rotation=90)

    # 4. Draw SPACING DIMENSIONS (Bottom)
    if len(centers) >= 2:
        for i in range(len(centers) - 1):
            
            # --- A. Clear Gap (RED, Top Tier) ---
            b_left_edge = centers[i] + (BEARER_W / 2)
            b_right_edge = centers[i+1] - (BEARER_W / 2)
            y_gap = -100 
            
            ax.annotate("", xy=(b_left_edge, y_gap), xytext=(b_right_edge, y_gap), 
                        arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=1.0))
            
            mid_gap = (b_left_edge + b_right_edge) / 2
            ax.text(mid_gap, y_gap - 40, f"Gap: {gap_val:.0f}", 
                    ha='center', va='top', fontsize=8, color='#C0392B', fontweight='bold')

            # --- B. Center-to-Center (BLUE, Bottom Tier) ---
            c1 = centers[i]
            c2 = centers[i+1]
            y_cc = -250 # Lower down
            
            # Draw tiny vertical ticks dropping down from centers
            ax.plot([c1, c1], [0, y_cc], color='#2980B9', linestyle=':', linewidth=0.5, alpha=0.5)
            ax.plot([c2, c2], [0, y_cc], color='#2980B9', linestyle=':', linewidth=0.5, alpha=0.5)
            
            ax.annotate("", xy=(c1, y_cc), xytext=(c2, y_cc), 
                        arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.0))
            
            mid_cc = (c1 + c2) / 2
            ax.text(mid_cc, y_cc - 40, f"C/C: {cc_val:.0f}", 
                    ha='center', va='top', fontsize=8, color='#2980B9', fontweight='bold')

    # 5. Draw Panels (Smart Coloring)
    base_palette = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2', '#BCBD22', '#17BECF']
    unique_sizes = sorted(list(set((p['w'], p['l']) for p in panels)))
    size_color_map = {size: base_palette[i % len(base_palette)] for i, size in enumerate(unique_sizes)}
    
    prev_size = None
    use_lighter_tone = False 

    for idx, p in enumerate(panels):
        curr_size = (p['w'], p['l'])
        base_hex = size_color_map[curr_size]

        if curr_size == prev_size:
            use_lighter_tone = not use_lighter_tone
        else:
            use_lighter_tone = False
            
        final_color = adjust_lightness(base_hex, 1.3) if use_lighter_tone else base_hex
            
        rect = patches.Rectangle(
            (p['x'], p['y']), p['w'], p['l'], 
            linewidth=1.5, edgecolor='white', facecolor=final_color, alpha=0.85
        )
        ax.add_patch(rect)
        
        if p['w'] > 100 and p['l'] > 200:
            mid_x = p['x'] + (p['w'] / 2)
            mid_y = p['y'] + (p['l'] / 2)
            ax.text(mid_x, mid_y, f"{p['l']:.0f}x{p['w']:.0f}", 
                    ha='center', va='center', fontsize=9, color='white', fontweight='bold',
                    bbox=dict(facecolor='black', alpha=0.2, edgecolor='none', pad=1))
        
        prev_size = curr_size

    ax.set_aspect('equal', adjustable='datalim')
    plt.tight_layout()
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
            "Type": f"{row_name}", 
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
def calculate_pod_cuts(base_width, base_length, supports):
    if base_width <= 0 or base_length <= 0 or supports < 2:
        return "INVALID"

    results = {}
    FASCIA_W = 45
    BEARER_W = 90
    SHEET_MAX_L = 2400
    
    first_center = FASCIA_W + (BEARER_W / 2)
    last_center = base_length - (FASCIA_W + (BEARER_W / 2))
    dist = last_center - first_center
    
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
    
    modular_list_raw = [] 
    modular_plot_data = [] 
    current_x = 0
    
    if supports == 2:
        t, p = split_panel_length(base_width, base_length, 0, "Full Span", SHEET_MAX_L)
        modular_list_raw.extend(t)
        modular_plot_data.extend(p)
    else:
        # Start
        t, p = split_panel_length(base_width, end_panel_w, 0, "End/Start Panels", SHEET_MAX_L)
        modular_list_raw.extend(t)
        modular_plot_data.extend(p)
        current_x += end_panel_w
        
        # Mid
        if mid_qty > 0:
            for i in range(mid_qty):
                t, p = split_panel_length(base_width, mid_panel_w, current_x, "Mid Panel", SHEET_MAX_L)
                modular_list_raw.extend(t)
                modular_plot_data.extend(p)
                current_x += mid_panel_w
        
        # End
        t, p = split_panel_length(base_width, end_panel_w, current_x, "End/Start Panels", SHEET_MAX_L)
        modular_list_raw.extend(t)
        modular_plot_data.extend(p)

    df_raw = pd.DataFrame(modular_list_raw)
    if not df_raw.empty:
        df_grouped = df_raw.groupby(['Type', 'Size'], as_index=False)['Qty'].sum()
        df_grouped = df_grouped.sort_values(by='Type', ascending=True) 
    else:
        df_grouped = pd.DataFrame()

    results['modular_df'] = df_grouped
    results['modular_plot'] = modular_plot_data

    # 3. OPTIMIZED (FULL SHEETS)
    if base_width <= 1200: sheet_reach = 2400 
    else: sheet_reach = 1200 
    
    optimized_list = []      
    optimized_plot_data = [] 
    current_pos = 0
    row_num = 1
    
    while current_pos < base_length:
        target = round(current_pos + sheet_reach, 2)
        if target >= base_length:
            strip_width = base_length - current_pos
        else:
            valid = [p for p in centers if p <= target and p > current_pos]
            if not valid: return "ERROR"
            snap = valid[-1]
            strip_width = snap - current_pos

        remaining_len = base_width
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
        if target >= base_length: break
        row_num += 1
        
    results['optimized_df'] = pd.DataFrame(optimized_list)
    results['optimized_plot'] = optimized_plot_data
    return results

# --- UI LAYOUT ---
st.title("🔨 Pod Ply Base Calculator")

with st.container():
    st.write("---")
    c1, c2, c3 = st.columns([1,1,1]) 
    with c1:
        base_length = st.number_input("Base Length [mm]", value=3504, step=10, min_value=0)
    with c2:
        base_width = st.number_input("Base Width [mm]", value=3114, step=10, min_value=0)
    with c3:
        num_bearers = st.number_input("Number of Bearers", value=7, step=1, min_value=0)
    st.write("---")

if st.button("Generate Cut Plan", type="primary", use_container_width=True):
    if base_width == 0 or base_length == 0 or num_bearers == 0:
        st.warning("⚠️ Please enter all dimensions. Fields cannot be 0.")
    elif num_bearers < 2:
        st.error("❌ You must have at least 2 bearers.")
    else:
        data = calculate_pod_cuts(base_width, base_length, num_bearers)
        
        if data == "ERROR":
            st.error("❌ Error: Bearer spacing is too wide for standard plywood sheets.")
        elif data == "INVALID":
            st.error("❌ Invalid inputs.")
        else:
            # REMOVED TAB 3 (Spacing Info)
            tab_vis, tab_data = st.tabs(["🖼️ Visual Plans", "📊 Cut Lists"])
            
            with tab_vis:
                st.info("💡 **Modular** shows the smallest panels that can be cut for that configuration. **Optimized** shows the largest panel that can be retrieved from a new sheet.")
                
                sub_v1, sub_v2 = st.tabs(["Option A: Modular (Offcuts)", "Option B: Optimized (Full Sheets)"])
                with sub_v1:
                    fig1 = draw_pod_diagram(base_width, base_length, data['centers'], data['modular_plot'], "Modular Layout", data['gap'], data['spacing_cc'])
                    if fig1: st.pyplot(fig1)
                with sub_v2:
                    fig2 = draw_pod_diagram(base_width, base_length, data['centers'], data['optimized_plot'], "Optimized Layout", data['gap'], data['spacing_cc'])
                    if fig2: st.pyplot(fig2)

            with tab_data:
                c1, c2 = st.columns(2)
                with c1:
                    st.subheader("A. Modular List")
                    st.dataframe(data['modular_df'], hide_index=True, use_container_width=True)
                with c2:
                    st.subheader("B. Optimized List")
                    st.dataframe(data['optimized_df'], hide_index=True, use_container_width=True)
