import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
# --- NEW IMPORTS FOR COLOR MANIPULATION ---
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
    """
    Lightens or darkens a given hex color.
    amount > 1 = lighter, amount < 1 = darker.
    """
    try:
        c = mcolors.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mcolors.to_rgb(c))
    # Modify lightness (index 1), clamp between 0 and 1
    new_l = max(0, min(1, amount * c[1]))
    rgb = colorsys.hls_to_rgb(c[0], new_l, c[2])
    return mcolors.to_hex(rgb)

# --- GENERIC DRAWING ENGINE ---
def draw_pod_diagram(base_width, base_length, centers, panels, title, gap_val):
    # Safety Check
    if base_width <= 0 or base_length <= 0: return None
    
    # Create Figure
    fig, ax = plt.subplots(figsize=(12, 10)) 
    
    # CONSTANTS
    FASCIA_W = 45
    BEARER_W = 90
    
    # 1. Setup Canvas Limits
    ax.set_xlim(-300, base_length + 300)
    ax.set_ylim(-300, base_width + 300) 
    ax.axis('off') # Remove default Rulers/Grid
    
    # Add Title
    ax.text(base_length/2, base_width + 250, title, ha='center', fontsize=14, weight='bold', color='#333')
    
    # 2. Draw Timber Frame
    # Fascias
    ax.add_patch(patches.Rectangle((0, 0), FASCIA_W, base_width, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    ax.add_patch(patches.Rectangle((base_length - FASCIA_W, 0), FASCIA_W, base_width, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    
    # Bearers
    for i, c in enumerate(centers):
        bx = c - (BEARER_W / 2)
        ax.add_patch(patches.Rectangle((bx, 0), BEARER_W, base_width, linewidth=0.5, edgecolor='black', facecolor='#D7CCC8'))
        ax.axvline(x=c, color='black', linestyle='--', alpha=0.3, linewidth=0.5)
        # Label Bearers
        ax.text(c, base_width + 40, f"B{i+1}", ha='center', fontsize=9, fontweight='bold', color='#5D4037')

    # 3. Draw EXTERNAL DIMENSIONS (Arrows)
    # Top (Length)
    dim_y_top = base_width + 150
    ax.annotate("", xy=(0, dim_y_top), xytext=(base_length, dim_y_top), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(base_length/2, dim_y_top + 20, f"Base Length: {base_length:.0f} mm", ha='center', va='bottom', fontsize=11, fontweight='bold')
            
    # Left (Width)
    dim_x_left = -150
    ax.annotate("", xy=(dim_x_left, 0), xytext=(dim_x_left, base_width), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(dim_x_left - 20, base_width/2, f"Base Width: {base_width:.0f} mm", ha='right', va='center', fontsize=11, fontweight='bold', rotation=90)

    # 4. Draw GAP DIMENSIONS (Bottom)
    if len(centers) >= 2:
        for i in range(len(centers) - 1):
            b_left_edge = centers[i] + (BEARER_W / 2)
            b_right_edge = centers[i+1] - (BEARER_W / 2)
            dim_y_bot = -100 
            ax.annotate("", xy=(b_left_edge, dim_y_bot), xytext=(b_right_edge, dim_y_bot), arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=1.0))
            mid_x = (b_left_edge + b_right_edge) / 2
            ax.text(mid_x, dim_y_bot - 50, f"{gap_val:.0f}", ha='center', va='center', fontsize=9, color='#C0392B', fontweight='bold')

    # 5. Draw Plywood Panels (SMART COLORING)
    
    # A. Define a palette of distinct colors
    base_palette = [
        '#1F77B4', # Blue
        '#FF7F0E', # Orange
        '#2CA02C', # Green
        '#D62728', # Red
        '#9467BD', # Purple
        '#8C564B', # Brown
        '#E377C2', # Pink
        '#BCBD22', # Olive
        '#17BECF'  # Cyan
    ]
    
    # B. Find unique sizes and map to base colors
    # Create tuples of (w, l) to identify unique sizes
    unique_sizes = sorted(list(set((p['w'], p['l']) for p in panels)))
    size_color_map = {size: base_palette[i % len(base_palette)] for i, size in enumerate(unique_sizes)}
    
    # C. Draw loop with adjacency tone check
    prev_size = None
    use_lighter_tone = False # Toggle for adjacency

    for idx, p in enumerate(panels):
        curr_size = (p['w'], p['l'])
        base_hex = size_color_map[curr_size]

        # Check Adjacency against previous panel in the list
        if curr_size == prev_size:
            # Same size as previous -> toggle tone switch
            use_lighter_tone = not use_lighter_tone
        else:
            # New size -> reset to base tone
            use_lighter_tone = False
            
        # Calculate final color based on tone switch
        if use_lighter_tone:
            # Make it 30% lighter to distinguish from neighbour
            final_color = adjust_lightness(base_hex, 1.3)
        else:
            final_color = base_hex
            
        # Draw Rectangle
        rect = patches.Rectangle(
            (p['x'], p['y']), p['w'], p['l'], 
            linewidth=1.5, edgecolor='white', facecolor=final_color, alpha=0.85
        )
        ax.add_patch(rect)
        
        # Label Size (if big enough)
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
def calculate_pod_cuts(base_width, base_length, supports):
    if base_width <= 0 or base_length <= 0 or supports < 2:
        return "INVALID"

    results = {}
    FASCIA_W = 45
    BEARER_W = 90
    SHEET_MAX_L = 2400
    
    # 1. SPACING
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
    
    modular_list = []      
    modular_plot_data = [] 
    current_x = 0
    
    if supports == 2:
        t, p = split_panel_length(base_width, base_length, 0, "Full Span", SHEET_MAX_L)
        modular_list.extend(t)
        modular_plot_data.extend(p)
    else:
        # Start
        t, p = split_panel_length(base_width, end_panel_w, 0, "Start Panel", SHEET_MAX_L)
        modular_list.extend(t)
        modular_plot_data.extend(p)
        current_x += end_panel_w
        # Mid
        if mid_qty > 0:
            for i in range(mid_qty):
                t, p = split_panel_length(base_width, mid_panel_w, current_x, "Mid Panel", SHEET_MAX_L)
                modular_list.extend(t)
                modular_plot_data.extend(p)
                current_x += mid_panel_w
        # End
        t, p = split_panel_length(base_width, end_panel_w, current_x, "End Panel", SHEET_MAX_L)
        modular_list.extend(t)
        modular_plot_data.extend(p)

    results['modular_df'] = pd.DataFrame(modular_list)
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
    
    # INPUTS CLEANED
    with c1:
        base_length = st.number_input("Base Length [mm]", value=3504, step=10, min_value=0)
    with c2:
        base_width = st.number_input("Base Width [mm]", value=3114, step=10, min_value=0)
    with c3:
        num_bearers = st.number_input("Number of Bearers", value=7, step=1, min_value=0)
    st.write("---")

if st.button("Generate Cut Plan", type="primary", use_container_width=True):
    
    # Validation
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
            # TABS
            tab_vis, tab_data, tab_info = st.tabs(["🖼️ Visual Plans", "📊 Cut Lists", "ℹ️ Spacing Info"])
            
            with tab_vis:
                st.info("💡 **Modular** shows alignment to bearers. **Optimized** shows actual sheet sizes.")
                sub_v1, sub_v2 = st.tabs(["Option A: Modular (Offcuts)", "Option B: Optimized (Full Sheets)"])
                
                with sub_v1:
                    fig1 = draw_pod_diagram(base_width, base_length, data['centers'], data['modular_plot'], "Modular Layout", data['gap'])
                    if fig1: st.pyplot(fig1)
                
                with sub_v2:
                    fig2 = draw_pod_diagram(base_width, base_length, data['centers'], data['optimized_plot'], "Optimized Layout", data['gap'])
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
