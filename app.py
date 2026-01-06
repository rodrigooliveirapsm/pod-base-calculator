import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pod Panel Calculator", page_icon="🔨", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    h1 { color: #2E86C1; } 
    .stButton>button { border-radius: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- VISUALIZATION ENGINE (UPDATED) ---
def draw_modular_cutplan(length, span, centers, panel_data):
    """
    Draws the POD structure (Bearers/Fascia) and overlays the Modular Plywood Panels.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # CONSTANTS FOR DRAWING
    FASCIA_W = 45
    BEARER_W = 90
    
    # 1. Setup the Pod Area
    # Add some padding for visual clarity
    ax.set_xlim(-100, span + 100)
    ax.set_ylim(-100, length + 200)
    ax.set_xlabel("Pod Span (mm)")
    ax.set_ylabel("Bearer Length (mm)")
    ax.set_title("Visual Layout: Modular Panels on Timber Frame", fontsize=14, pad=20)
    
    # --- LAYER 1: TIMBER STRUCTURE (Browns) ---
    
    # A. Draw Fascias (Darker Wood)
    # Start Fascia
    rect_f1 = patches.Rectangle((0, 0), FASCIA_W, length, linewidth=1, edgecolor='black', facecolor='#8D6E63')
    ax.add_patch(rect_f1)
    ax.text(FASCIA_W/2, -50, "Fascia", ha='center', fontsize=8, rotation=90)
    
    # End Fascia
    rect_f2 = patches.Rectangle((span - FASCIA_W, 0), FASCIA_W, length, linewidth=1, edgecolor='black', facecolor='#8D6E63')
    ax.add_patch(rect_f2)
    
    # B. Draw Bearers (Lighter Wood)
    # Centers are passed in. We draw a box 90mm wide centered on that line.
    for i, c in enumerate(centers):
        # Calculate bottom-left corner of the bearer
        bx = c - (BEARER_W / 2)
        
        rect_b = patches.Rectangle((bx, 0), BEARER_W, length, linewidth=0.5, edgecolor='black', facecolor='#D7CCC8')
        ax.add_patch(rect_b)
        
        # Centerline (Dashed) for reference
        ax.axvline(x=c, color='black', linestyle='--', alpha=0.3, linewidth=0.5)
        
        # Label Bearer
        ax.text(c, length + 50, f"B{i+1}", ha='center', fontsize=9, fontweight='bold', color='#5D4037')

    # --- LAYER 2: PLYWOOD PANELS (Blues with Transparency) ---
    # We iterate through the calculated panel data
    
    current_x = 0
    colors = ['#29B6F6', '#4FC3F7'] # Bright Blues
    
    for idx, panel in enumerate(panel_data):
        w = panel['width_mm']
        l = panel['length_mm']
        
        # Draw Panel with Alpha (Transparency) so we can see the timber underneath
        # We alternate colors to show the joint clearly
        c_code = colors[idx % 2]
        
        rect_p = patches.Rectangle(
            (current_x, 0), w, l, 
            linewidth=2, edgecolor='blue', facecolor=c_code, alpha=0.5
        )
        ax.add_patch(rect_p)
        
        # Label the Panel Size
        mid_x = current_x + (w / 2)
        mid_y = l / 2
        ax.text(mid_x, mid_y, f"{w:.0f} mm", ha='center', va='center', fontsize=10, fontweight='bold', color='white',
                bbox=dict(facecolor='black', alpha=0.3, edgecolor='none', pad=1))
        
        current_x += w # Move cursor to next panel start

    ax.set_aspect('equal', adjustable='box')
    plt.grid(False) # Turn off grid to keep it clean
    
    return fig

# --- LOGIC ENGINE ---
def calculate_pod_cuts(length, span, supports):
    results = {}
    
    # CONSTANTS
    FASCIA_W = 45
    BEARER_W = 90
    SHEET_MAX_L = 2400
    
    # 1. SPACING
    first_center = FASCIA_W + (BEARER_W / 2)
    last_center = span - (FASCIA_W + (BEARER_W / 2))
    dist = last_center - first_center
    spacing_cc = dist / (supports - 1)
    gap = spacing_cc - BEARER_W
    
    results['spacing_cc'] = spacing_cc
    results['gap'] = gap
    centers = [first_center + (i * spacing_cc) for i in range(supports)]
    results['centers'] = centers
    
    # 2. MODULAR LIST & PLOT DATA
    end_panel_w = first_center + spacing_cc
    mid_panel_w = spacing_cc
    mid_qty = max(0, supports - 3)
    
    modular_list = [] # For the Table
    panel_plot_data = [] # For the Visualizer
    
    # A. Start Panel
    # Note: If length > 2400, this panel is physically split, but visually we show the "Zone".
    # For visualization simplicity, we draw the full "Zone" (Strip).
    
    modular_list.append({"Qty": 1, "Type": "Start Panel", "Size (LxW)": f"{length:.0f} x {end_panel_w:.1f} mm"})
    panel_plot_data.append({'width_mm': end_panel_w, 'length_mm': length})
    
    # B. Mid Panels
    if mid_qty > 0:
        modular_list.append({"Qty": mid_qty, "Type": "Mid Panel", "Size (LxW)": f"{length:.0f} x {mid_panel_w:.1f} mm"})
        # Add each mid panel individually to plot data so they draw sequentially
        for _ in range(mid_qty):
            panel_plot_data.append({'width_mm': mid_panel_w, 'length_mm': length})
            
    # C. End Panel (Only if > 2 bearers)
    if supports > 2:
        modular_list.append({"Qty": 1, "Type": "End Panel", "Size (LxW)": f"{length:.0f} x {end_panel_w:.1f} mm"})
        panel_plot_data.append({'width_mm': end_panel_w, 'length_mm': length})
    
    # Special Case: 2 Bearers (Start and End are the same/meet in middle?)
    # With 2 bearers, First Center is start, Last Center is end.
    # Logic holds: Start Panel covers to Center 2. End Panel covers from Center 1? 
    # Actually with 2 bearers, Start Panel goes 0 -> Center 2 (End).
    # If supports=2, calculation gives 1 Start Panel width = 0 to End Center.
    # Let's trust the spacing math above, it works for N>=3 generally. 
    
    results['modular_df'] = pd.DataFrame(modular_list)
    results['panel_plot_data'] = panel_plot_data
    
    # 3. OPTIMIZED LIST (Just for Table)
    # (Simplified logic for table display only)
    if length <= 1200: sheet_reach = 2400 
    else: sheet_reach = 1200 
    
    optimized_list = []
    current_pos = 0
    row_num = 1
    
    while current_pos < span:
        target = round(current_pos + sheet_reach, 2)
        if target >= span:
            strip_width = span - current_pos
        else:
            valid = [p for p in centers if p <= target and p > current_pos]
            if not valid: return "ERROR"
            strip_width = valid[-1] - current_pos
            
        remaining_len = length
        part_num = 1
        while remaining_len > 0:
            cut_len = min(remaining_len, SHEET_MAX_L)
            optimized_list.append({
                "Cut ID": f"Row {row_num}.{part_num}",
                "Width (mm)": f"{strip_width:.1f}",
                "Length (mm)": f"{cut_len:.0f}",
            })
            remaining_len -= cut_len
            part_num += 1
        current_pos += strip_width
        if target >= span: break
        row_num += 1
        
    results['optimized_df'] = pd.DataFrame(optimized_list)
    return results

# --- UI LAYOUT ---
st.title("🔨 Pod Ply Base Calculator")

# Inputs
with st.container():
    st.write("---")
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        bearer_len = st.number_input("Bearer Length", value=3114, step=10)
    with c2:
        num_bearers = st.number_input("Total Bearers", value=7, min_value=3)
    with c3:
        total_span = st.number_input("Total Pod Span", value=3504, step=10)
    st.write("---")

if st.button("Generate Cut Plan", type="primary", use_container_width=True):
    
    data = calculate_pod_cuts(bearer_len, total_span, num_bearers)
    
    if data == "ERROR":
        st.error("❌ Bearer spacing is too wide for plywood sheets.")
    else:
        # TABS
        tab1, tab2, tab3 = st.tabs(["🖼️ Visual Plan", "📊 Cut List", "ℹ️ Spacing Info"])
        
        with tab1:
            st.subheader("Visual Layout (Modular Strategy)")
            st.caption("Showing 45mm Fascia (Brown), 90mm Bearers (Tan), and Plywood Panels (Blue).")
            st.caption("✅ The Blue Panel edges should land exactly on the dashed centerlines.")
            
            # Draw the Plot
            fig = draw_modular_cutplan(bearer_len, total_span, data['centers'], data['panel_plot_data'])
            st.pyplot(fig)
            
        with tab2:
            st.subheader("1. Modular Panels (Offcuts)")
            st.dataframe(data['modular_df'], hide_index=True, use_container_width=True)
            
            st.divider()
            
            st.subheader("2. Optimized Full Sheets")
            st.dataframe(data['optimized_df'], hide_index=True, use_container_width=True)
            
        with tab3:
            st.metric("Center-to-Center Spacing", f"{data['spacing_cc']:.1f} mm")
            st.metric("Clear Gap Between Timber", f"{data['gap']:.1f} mm")
