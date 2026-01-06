import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import colorsys
import string

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pod Ply Base Calculator", page_icon="🔨", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    h1 { color: #2E86C1; } 
    .stButton>button { border-radius: 8px; font-weight: bold; }
    
    /* TABLE STYLING: FORCE CENTER ALIGNMENT EVERYWHERE */
    /* Target the DataFrame container */
    [data-testid="stDataFrame"] {
        width: 100%;
    }
    
    /* Header Cells */
    [data-testid="stDataFrame"] [role="columnheader"] {
        text-align: center !important;
        justify-content: center !important;
        display: flex !important;
    }
    
    /* Data Cells */
    [data-testid="stDataFrame"] [role="gridcell"] {
        text-align: center !important;
        justify-content: center !important;
        display: flex !important;
    }
    
    /* Generic row content alignment */
    [data-testid="stDataFrame"] div[role="row"] {
        justify-content: center !important;
    }
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

# --- GENERIC DRAWING ENGINE (TOP & FRONT VIEWS) ---
def draw_pod_diagram(base_width, base_length, centers, panels, title, gap_val, cc_val):
    if base_width <= 0 or base_length <= 0: return None
    
    # 1. SETUP FIGURE WITH 2 SUBPLOTS
    fig, (ax_top, ax_front) = plt.subplots(2, 1, figsize=(12, 14), 
                                           gridspec_kw={'height_ratios': [4, 1], 'hspace': 0.05})

    # ============================================
    # TOP VIEW DRAWING (ax_top)
    # ============================================
    FASCIA_W = 45
    BEARER_W = 90
    
    ax_top.set_xlim(-300, base_length + 300)
    ax_top.set_ylim(-450, base_width + 300) 
    ax_top.axis('off')
    ax_top.set_title(title, fontsize=14, weight='bold', color='#333', pad=20)
    
    # Timber Frame (Top)
    ax_top.add_patch(patches.Rectangle((0, 0), FASCIA_W, base_width, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    ax_top.add_patch(patches.Rectangle((base_length - FASCIA_W, 0), FASCIA_W, base_width, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    
    for i, c in enumerate(centers):
        bx = c - (BEARER_W / 2)
        ax_top.add_patch(patches.Rectangle((bx, 0), BEARER_W, base_width, linewidth=0.5, edgecolor='black', facecolor='#D7CCC8'))
        ax_top.axvline(x=c, color='black', linestyle='--', alpha=0.3, linewidth=0.5)
        ax_top.text(c, base_width + 40, f"B{i+1}", ha='center', fontsize=9, fontweight='bold', color='#5D4037')

    # External Dimensions (Top)
    dim_y_top = base_width + 150
    ax_top.annotate("", xy=(0, dim_y_top), xytext=(base_length, dim_y_top), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax_top.text(base_length/2, dim_y_top + 20, f"Base Length: {base_length:.0f} mm", ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    dim_x_left = -150
    ax_top.annotate("", xy=(dim_x_left, 0), xytext=(dim_x_left, base_width), arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax_top.text(dim_x_left - 20, base_width/2, f"Base Width: {base_width:.0f} mm", ha='right', va='center', fontsize=11, fontweight='bold', rotation=90)

    # Spacing Dimensions (Top)
    if len(centers) >= 2:
        for i in range(len(centers) - 1):
            # A. Gap
            b_left_edge = centers[i] + (BEARER_W / 2)
            b_right_edge = centers[i+1] - (BEARER_W / 2)
            y_gap = -100 
            ax_top.annotate("", xy=(b_left_edge, y_gap), xytext=(b_right_edge, y_gap), arrowprops=dict(arrowstyle='<->', color='#C0392B', lw=1.0))
            mid_gap = (b_left_edge + b_right_edge) / 2
            ax_top.text(mid_gap, y_gap - 40, f"Gap: {gap_val:.0f}", ha='center', va='top', fontsize=8, color='#C0392B', fontweight='bold')

            # B. C/C
            c1 = centers[i]
            c2 = centers[i+1]
            y_cc = -250 
            ax_top.plot([c1, c1], [0, y_cc], color='#2980B9', linestyle=':', linewidth=0.5, alpha=0.5)
            ax_top.plot([c2, c2], [0, y_cc], color='#2980B9', linestyle=':', linewidth=0.5, alpha=0.5)
            ax_top.annotate("", xy=(c1, y_cc), xytext=(c2, y_cc), arrowprops=dict(arrowstyle='<->', color='#2980B9', lw=1.0))
            mid_cc = (c1 + c2) / 2
            ax_top.text(mid_cc, y_cc - 40, f"C/C: {cc_val:.0f}", ha='center', va='top', fontsize=8, color='#2980B9', fontweight='bold')

    # Panels (Top) - And prepare color map for Front View
    base_palette = ['#1F77B4', '#FF7F0E', '#2CA02C', '#D62728', '#9467BD', '#8C564B', '#E377C2', '#BCBD22', '#17BECF']
    unique_sizes = sorted(list(set((p['w'], p['l']) for p in panels)))
    size_color_map = {size: base_palette[i % len(base_palette)] for i, size in enumerate(unique_sizes)}
    
    prev_size = None
    use_lighter_tone = False 
    
    front_view_segments = {} 

    for idx, p in enumerate(panels):
        curr_size = (p['w'], p['l'])
        base_hex = size_color_map[curr_size]
        if curr_size == prev_size: use_lighter_tone = not use_lighter_tone
        else: use_lighter_tone = False
        final_color = adjust_lightness(base_hex, 1.3) if use_lighter_tone else base_hex
            
        rect = patches.Rectangle((p['x'], p['y']), p['w'], p['l'], linewidth=1.5, edgecolor='white', facecolor=final_color, alpha=0.85)
        ax_top.add_patch(rect)
        
        if p['x'] not in front_view_segments:
            front_view_segments[p['x']] = {'w': p['w'], 'c': final_color}

        if p['w'] > 100 and p['l'] > 200:
            mid_x = p['x'] + (p['w'] / 2); mid_y = p['y'] + (p['l'] / 2)
            label_text = f"{p['id']}\n{p['l']:.0f}x{p['w']:.0f}"
            ax_top.text(mid_x, mid_y, label_text, ha='center', va='center', fontsize=10, color='white', fontweight='bold', bbox=dict(facecolor='black', alpha=0.2, edgecolor='none', pad=1))
        prev_size = curr_size
    
    ax_top.set_aspect('equal', adjustable='datalim')

    # ============================================
    # FRONT VIEW DRAWING (ax_front)
    # ============================================
    TOTAL_TIMBER_H = 90
    SINGLE_TIMBER_H = 45
    PLY_THICK = 17
    TOTAL_H = TOTAL_TIMBER_H + PLY_THICK
    
    # 1. REMOVED TITLE
    
    ax_front.set_xlim(-300, base_length + 300)
    ax_front.set_ylim(-100, 200) # Increased top limit to fit dimensions above
    ax_front.axis('off')

    # --- 1. Draw Structure (Bearers & Fascia) ---
    ax_front.axhline(y=0, color='black', linewidth=1)

    # Fascia (Ends)
    ax_front.add_patch(patches.Rectangle((0, 0), FASCIA_W, TOTAL_TIMBER_H, linewidth=1, edgecolor='black', facecolor='#8D6E63'))
    ax_front.add_patch(patches.Rectangle((base_length - FASCIA_W, 0), FASCIA_W, TOTAL_TIMBER_H, linewidth=1, edgecolor='black', facecolor='#8D6E63'))

    # Bearers
    for c in centers:
        bx = c - (BEARER_W / 2)
        ax_front.add_patch(patches.Rectangle((bx, 0), BEARER_W, SINGLE_TIMBER_H, linewidth=1, edgecolor='black', facecolor='#2CA02C'))
        ax_front.add_patch(patches.Rectangle((bx, SINGLE_TIMBER_H), BEARER_W, SINGLE_TIMBER_H, linewidth=1, edgecolor='black', facecolor='#2CA02C'))

    # --- 2. Draw Spacing Dimensions (Internal Gaps) - MOVED OUT (ABOVE) ---
    if len(centers) >= 2:
        for i in range(len(centers) - 1):
            b_left_edge = centers[i] + (BEARER_W / 2)
            b_right_edge = centers[i+1] - (BEARER_W / 2)
            
            # Position ABOVE the Plywood (Total H is ~107mm, place this at 135mm)
            dim_y = TOTAL_H + 28 
            
            ax_front.annotate("", xy=(b_left_edge, dim_y), xytext=(b_right_edge, dim_y), 
                              arrowprops=dict(arrowstyle='<->', color='red', lw=1.0))
            
            mid_gap = (b_left_edge + b_right_edge) / 2
            ax_front.text(mid_gap, dim_y + 10, f"{gap_val:.0f}", ha='center', va='bottom', fontsize=8, color='red', fontweight='bold')


    # --- 3. Draw Plywood Panels ---
    sorted_x_keys = sorted(front_view_segments.keys())

    for x_pos in sorted_x_keys:
        seg = front_view_segments[x_pos]
        w = seg['w']
        c = seg['c']
        
        ax_front.add_patch(patches.Rectangle((x_pos, TOTAL_TIMBER_H), w, PLY_THICK, linewidth=1, edgecolor='black', facecolor=c))
        
        dim_y = -30
        ax_front.annotate("", xy=(x_pos, dim_y), xytext=(x_pos + w, dim_y), 
                          arrowprops=dict(arrowstyle='<->', color='black', lw=1.0))
        mid_x = x_pos + (w / 2)
        ax_front.text(mid_x, dim_y - 20, f"{w:.0f}", ha='center', va='top', fontsize=9, fontweight='bold')

    ax_front.set_aspect('equal', adjustable='datalim')

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
            # Force No Decimals (.0f)
            "Size [mm]": f"{cut_len:.0f} x {width:.0f}", 
            "raw_w": width,
            "raw_l": cut_len
        })
        plot_data.append({
            'x': start_x, 'y': current_y, 'w': width, 'l': cut_len
        })
        current_y += cut_len
        remaining -= cut_len
        part += 1
    return table_rows, plot_data

# --- HELPER: ASSIGN IDs ---
def assign_panel_ids(table_rows, plot_data):
    if not plot_data: return
    unique_sizes = list(set((p['w'], p['l']) for p in plot_data))
    unique_sizes.sort(key=lambda x: (x[0]*x[1], x[1]), reverse=True)
    id_map = {}
    letters = string.ascii_uppercase
    for i, size in enumerate(unique_sizes):
        letter = letters[i] if i < 26 else f"Z{i}"
        id_map[size] = letter
    for p in plot_data: p['id'] = id_map[(p['w'], p['l'])]
    for row in table_rows: row['Panel ID'] = id_map[(row['raw_w'], row['raw_l'])]
    return

# --- CALCULATION ENGINE ---
def calculate_pod_cuts(base_width, base_length, supports):
    if base_width <= 0 or base_length <= 0 or supports < 2: return "INVALID"
    results = {}
    FASCIA_W = 45; BEARER_W = 90; SHEET_MAX_L = 2400
    
    first_center = FASCIA_W + (BEARER_W / 2)
    last_center = base_length - (FASCIA_W + (BEARER_W / 2))
    dist = last_center - first_center
    spacing_cc = dist / (supports - 1)
    gap = spacing_cc - BEARER_W
    results['spacing_cc'] = spacing_cc; results['gap'] = gap
    centers = [first_center + (i * spacing_cc) for i in range(supports)]
    results['centers'] = centers
    
    # --- MODULAR ---
    end_panel_w = first_center + spacing_cc
    mid_panel_w = spacing_cc
    mid_qty = max(0, supports - 3)
    mod_table = []; mod_plot = []; current_x = 0
    
    if supports == 2:
        t, p = split_panel_length(base_width, base_length, 0, "Full Span", SHEET_MAX_L)
        mod_table.extend(t); mod_plot.extend(p)
    else:
        t, p = split_panel_length(base_width, end_panel_w, 0, "End/Start Panels", SHEET_MAX_L)
        mod_table.extend(t); mod_plot.extend(p); current_x += end_panel_w
        if mid_qty > 0:
            for i in range(mid_qty):
                t, p = split_panel_length(base_width, mid_panel_w, current_x, "Mid Panel", SHEET_MAX_L)
                mod_table.extend(t); mod_plot.extend(p); current_x += mid_panel_w
        t, p = split_panel_length(base_width, end_panel_w, current_x, "End/Start Panels", SHEET_MAX_L)
        mod_table.extend(t); mod_plot.extend(p)

    assign_panel_ids(mod_table, mod_plot)
    df_mod = pd.DataFrame(mod_table)
    if not df_mod.empty:
        df_mod = df_mod.groupby(['Panel ID', 'Size [mm]'], as_index=False)['Qty'].sum().sort_values(by='Panel ID') 
    else: df_mod = pd.DataFrame()
    results['modular_df'] = df_mod; results['modular_plot'] = mod_plot

    # --- OPTIMIZED ---
    sheet_reach = 2400 if base_width <= 1200 else 1200 
    opt_table = []; opt_plot = []; current_pos = 0
    
    while current_pos < base_length:
        target = round(current_pos + sheet_reach, 2)
        if target >= base_length: strip_width = base_length - current_pos
        else:
            snap = [p for p in centers if p <= target and p > current_pos][-1]
            strip_width = snap - current_pos
        remaining_len = base_width; current_y = 0
        while remaining_len > 0:
            cut_len = min(remaining_len, SHEET_MAX_L)
            # Force No Decimals (.0f)
            opt_table.append({"Qty": 1, "Size [mm]": f"{cut_len:.0f} x {strip_width:.0f}", "raw_w": strip_width, "raw_l": cut_len})
            opt_plot.append({'x': current_pos, 'y': current_y, 'w': strip_width, 'l': cut_len})
            current_y += cut_len; remaining_len -= cut_len
        current_pos += strip_width
        if target >= base_length: break
        
    assign_panel_ids(opt_table, opt_plot)
    df_opt = pd.DataFrame(opt_table)
    if not df_opt.empty:
        df_opt = df_opt.groupby(['Panel ID', 'Size [mm]'], as_index=False)['Qty'].sum().sort_values(by='Panel ID')
    else: df_opt = pd.DataFrame()
    results['optimized_df'] = df_opt; results['optimized_plot'] = opt_plot
    return results

# --- UI LAYOUT ---
st.title("🔨 Pod Ply Base Calculator")

with st.container():
    st.write("---")
    c1, c2, c3 = st.columns([1,1,1]) 
    with c1: base_length = st.number_input("Base Length [mm]", value=3504, step=10, min_value=0)
    with c2: base_width = st.number_input("Base Width [mm]", value=3114, step=10, min_value=0)
    with c3: num_bearers = st.number_input("Number of Bearers", value=7, step=1, min_value=0)
    st.write("---")

if st.button("Generate Cut Plan", type="primary", use_container_width=True):
    if base_width == 0 or base_length == 0 or num_bearers == 0:
        st.warning("⚠️ Please enter all dimensions. Fields cannot be 0.")
    elif num_bearers < 2:
        st.error("❌ You must have at least 2 bearers.")
    else:
        data = calculate_pod_cuts(base_width, base_length, num_bearers)
        if data == "ERROR": st.error("❌ Error: Bearer spacing is too wide for standard plywood sheets.")
        elif data == "INVALID": st.error("❌ Invalid inputs.")
        else:
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
                    cols = ['Panel ID', 'Qty', 'Size [mm]']
                    st.dataframe(data['modular_df'][cols], hide_index=True, use_container_width=True)
                with c2:
                    st.subheader("B. Optimized List")
                    st.dataframe(data['optimized_df'][cols], hide_index=True, use_container_width=True)
