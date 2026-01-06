import streamlit as st
import pandas as pd

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pod Ply Base Calculator", page_icon="🔨")

# --- CUSTOM CSS FOR TABLET VISIBILITY ---
st.markdown("""
    <style>
    .big-font { font-size:20px !important; }
    .stNumberInput > div > div > input { font-size: 20px; }
    h1 { color: #2E86C1; } 
    h3 { color: #2874A6; }
    </style>
    """, unsafe_allow_html=True)

# --- THE LOGIC ENGINE ---
def calculate_pod_cuts(length, span, supports):
    """
    Returns a dictionary with spacing info and two dataframes (Modular & Optimized).
    """
    results = {}
    
    # CONSTANTS
    FASCIA_W = 45
    BEARER_W = 90
    SHEET_MAX_L = 2400
    
    # 1. SPACING CALCULATION (Frame Logic)
    first_center = FASCIA_W + (BEARER_W / 2)
    last_center = span - (FASCIA_W + (BEARER_W / 2))
    dist = last_center - first_center
    spacing_cc = dist / (supports - 1)
    gap = spacing_cc - BEARER_W
    
    results['spacing_cc'] = spacing_cc
    results['gap'] = gap
    
    # Generate Bearer Center List (0-indexed internally, but we display 1-indexed)
    centers = [first_center + (i * spacing_cc) for i in range(supports)]
    
    # ==========================================
    # STRATEGY A: MODULAR PANELS (Offcuts)
    # ==========================================
    # Logic: 
    # End Panels cover Fascia + Bearer + Gap to next center
    # Mid Panels cover Center-to-Center spacing
    
    end_panel_w = first_center + spacing_cc
    mid_panel_w = spacing_cc
    mid_qty = max(0, supports - 3)
    
    modular_list = []
    
    # End Panel 1 (Start)
    modular_list.append({
        "Qty": 1, 
        "Type": "Start Panel", 
        "Width (mm)": f"{end_panel_w:.1f}", 
        "Length (mm)": f"{length}", 
        "Install Location": "Start -> Bearer #2 Center"
    })
    
    # Middle Panels
    if mid_qty > 0:
        modular_list.append({
            "Qty": mid_qty, 
            "Type": "Mid Panel", 
            "Width (mm)": f"{mid_panel_w:.1f}", 
            "Length (mm)": f"{length}", 
            "Install Location": "Between Bearer Centers"
        })
        
    # End Panel 2 (Finish)
    modular_list.append({
        "Qty": 1, 
        "Type": "End Panel", 
        "Width (mm)": f"{end_panel_w:.1f}", 
        "Length (mm)": f"{length}", 
        "Install Location": f"Bearer #{supports-1} Center -> End"
    })
    
    # Special case: 3 Bearers (End panels meet in middle)
    if supports == 3:
        modular_list = [] # Reset to show just two halves
        modular_list.append({
            "Qty": 2,
            "Type": "Half Panel",
            "Width (mm)": f"{end_panel_w:.1f}",
            "Length (mm)": f"{length}",
            "Install Location": "Meets at Center Bearer (#2)"
        })

    results['modular_df'] = pd.DataFrame(modular_list)

    # ==========================================
    # STRATEGY B: OPTIMIZED (Full Sheets)
    # ==========================================
    
    # Sheet Orientation
    if length <= 1200:
        sheet_reach = 2400 # We can rotate sheet
    else:
        sheet_reach = 1200 # Limited by width
        
    optimized_list = []
    current_pos = 0
    row_num = 1
    
    while current_pos < span:
        # A. Find Strip Width
        target = current_pos + sheet_reach
        target = round(target, 2)
        
        # Check if we finish
        if target >= span:
            strip_width = span - current_pos
            joint_note = "Ends at Pod Edge"
        else:
            # Find snap point
            valid = [p for p in centers if p <= target and p > current_pos]
            if not valid:
                return "ERROR"
            snap = valid[-1]
            strip_width = snap - current_pos
            
            # Identify Bearer Number (index + 1)
            bearer_idx = centers.index(snap)
            joint_note = f"Joint on Bearer #{bearer_idx + 1}"

        # B. Check for Splits (Length Limit)
        remaining_len = length
        part_num = 1
        
        while remaining_len > 0:
            cut_len = min(remaining_len, SHEET_MAX_L)
            
            # For parts > 1 (extensions), check length logic
            # If length is huge, we just list the parts. 
            # Note: Extensions rely on cross-members (noggings) usually.
            
            optimized_list.append({
                "Cut ID": f"Cut {row_num}.{part_num}",
                "Width (mm)": f"{strip_width:.1f}",
                "Length (mm)": f"{cut_len:.0f}",
                "Joint Location": joint_note if part_num == 1 else "Extension Joint (Requires Nogs)"
            })
            
            remaining_len -= cut_len
            part_num += 1
            
        # Move forward
        current_pos += strip_width if target < span else strip_width
        current_pos = round(current_pos, 2)
        if target >= span: break
        row_num += 1
        
    results['optimized_df'] = pd.DataFrame(optimized_list)
    return results

# --- THE USER INTERFACE ---
st.title("🔨 Pod Ply Base Calculator")
st.markdown("Calculate plywood cuts for Pod Base/Flooring.")

# Inputs Area
with st.container():
    st.write("---")
    col1, col2 = st.columns(2)
    with col1:
        bearer_len = st.number_input("Bearer Length (mm)", value=3114, step=10)
        num_bearers = st.number_input("Total Bearers", value=7, step=1, min_value=3)
    with col2:
        total_span = st.number_input("Total Pod Span (mm)", value=3504, step=10)
    st.write("---")

if st.button("CALCULATE CUTS", type="primary", use_container_width=True):
    
    # --- RUN CALCULATIONS ---
    data = calculate_pod_cuts(bearer_len, total_span, num_bearers)
    
    if data == "ERROR":
        st.error(f"❌ Error: Bearer spacing is too wide for standard plywood! Add more bearers.")
    else:
        # --- 1. SPACING DISPLAY ---
        st.subheader("1. Spacing Check")
        c1, c2 = st.columns(2)
        c1.metric("Center-to-Center", f"{data['spacing_cc']:.1f} mm")
        c2.metric("Clear Gap (Between Timber)", f"{data['gap']:.1f} mm")
        
        # --- 2. MODULAR CUTS (MAIN) ---
        st.header("2. Modular Panels (Offcuts Strategy)")
        st.caption("Use this list for single panels between every bearer (recommended for utilizing scrap).")
        
        st.table(data['modular_df'])
        
        # --- 3. OPTIMIZED CUTS (SECONDARY) ---
        st.header("3. Optimized Cuts (Full Sheets)")
        st.caption("Use this list to cover the pod with the largest possible sheets.")
        
        # Determine Sheet Orientation for Note
        orientation = "2400mm" if bearer_len <= 1200 else "1200mm"
        st.info(f"ℹ️ Based on Bearer Length ({bearer_len}mm), sheets are spanning using their {orientation} dimension.")

        st.dataframe(
            data['optimized_df'], 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Cut ID": st.column_config.TextColumn("Cut ID", width="small"),
                "Width (mm)": st.column_config.TextColumn("Width", width="small"),
                "Length (mm)": st.column_config.TextColumn("Length", width="small"),
                "Joint Location": st.column_config.TextColumn("Joint Location", width="large"),
            }
        )
