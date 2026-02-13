import streamlit as st
import json
import os
import pandas as pd
import base64
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(
    page_title="NorthCape Turbo Catalogue",
    page_icon="🛋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force Refresh Commit: Triggering Deployment Rebuild
# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* White-labeling: Hide Streamlit Branding & Menus */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden !important;}
    [data-testid="stSidebarCollapseButton"] {display: none !important;}
    
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }

    /* Reduce default Streamlit padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Container for the responsive grid */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
        gap: 24px;
        width: 100%;
        padding-top: 1.5rem;
    }
    
    /* Strictly 3-5 columns on Desktop */
    @media (min-width: 900px) and (max-width: 1199px) {
        .card-grid { grid-template-columns: repeat(3, 1fr); }
    }
    @media (min-width: 1200px) and (max-width: 1599px) {
        .card-grid { grid-template-columns: repeat(4, 1fr); }
    }
    @media (min-width: 1600px) {
        .card-grid { grid-template-columns: repeat(5, 1fr); }
    }

    /* Product Card */
    .product-card {
        background: white;
        padding: 0.75rem;
        border-radius: 14px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.1);
        display: flex;
        flex-direction: column;
        height: 100%;
        max-width: 320px;
    }
    
    .product-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        border-color: #3b82f6;
    }
    
    .image-container {
        width: 100%;
        background: white;
        border-radius: 12px;
        aspect-ratio: 1.2 / 1;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .image-container img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        transition: transform 0.5s ease;
    }
    
    .product-card:hover .image-container img {
        transform: scale(1.25);
    }
    
    /* Swap Image Button */
    .image-container {
        position: relative;
    }
    
    .swap-btn {
        position: absolute;
        bottom: 8px;
        right: 8px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid #e2e8f0;
        border-radius: 50%;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        z-index: 10;
        transition: all 0.2s;
        opacity: 0.6;
    }
    
    .swap-btn:hover {
        opacity: 1;
        background: white;
        transform: scale(1.1);
        border-color: #3b82f6;
    }
    
    .product-card:hover .swap-btn {
        opacity: 0.9;
    }
    
    /* Shortlist Button */
    .shortlist-btn {
        position: absolute;
        top: 6px;
        right: 6px;
        background: rgba(255, 255, 255, 0.95);
        border: 1px solid #e2e8f0;
        border-radius: 50%;
        width: 34px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        z-index: 999;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        opacity: 0.8;
        pointer-events: auto !important;
    }
    
    .shortlist-btn:hover {
        transform: scale(1.1);
        background: #fff;
        opacity: 1;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
    }
    
    .shortlist-btn:active {
        transform: scale(0.9);
        background: #f1f5f9;
    }
    
    .shortlist-btn.active {
        opacity: 1 !important;
        color: #eab308; /* Yellow-500 */
        background: white;
        border-color: #eab308;
    }
    
    .product-card:hover .shortlist-btn {
        opacity: 0.7;
    }
    
    .shortlist-btn:hover {
        opacity: 1 !important;
        transform: scale(1.1);
    }
    
    .card-header {
        display: flex;
        flex-direction: column;
    }
    
    .badge {
        background: #dbeafe;
        color: #1e40af;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        display: inline-block;
        width: fit-content;
        margin-bottom: 0.5rem;
    }
    
    .part-number {
        font-size: 1.05rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 1px;
    }
    
    .collection-text {
        font-size: 0.85rem;
        color: #64748b;
        margin-bottom: 0.2rem;
    }
    
    .card-footer {
        margin-top: auto;
    }
    
    .detail-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.8rem;
        padding: 0.2rem 0;
    }
    
    .detail-label {
        color: #64748b;
        font-weight: 500;
    }
    
    .detail-value {
        color: #0f172a;
        font-weight: 700;
        text-align: right;
    }
    
    .color-link {
        color: #2563eb;
        text-decoration: none;
    }
    
    .color-link:hover {
        text-decoration: underline;
    }
    
    .color-link {
        color: #2563eb;
        text-decoration: none;
        transition: color 0.2s;
        font-weight: 600;
    }
    
    .color-link:hover {
        color: #1d4ed8;
        text-decoration: underline;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
    }
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }

    /* Highlighted Search Bar (Match Reference) */
    div[data-baseweb="input"] {
        border: 1.5px solid #bfdbfe !important;
        border-radius: 12px !important;
        transition: all 0.3s;
        background: white !important;
        padding-left: 8px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #2563eb !important;
        box-shadow: 0 0 0 1px #2563eb !important;
    }
    
    /* Sidebar Label Styling (Match Reference) */
    [data-testid="stWidgetLabel"] p {
        color: #1e40af !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
    }
    
    /* Premium Header */
    .hero-container {
        padding: 1rem 0rem;
        margin-bottom: 0rem;
    }
    
    .hero-title {
        font-size: 2.75rem;
        font-weight: 800;
        color: #1e40af;
        letter-spacing: -0.01em;
        margin-bottom: 0.75rem;
    }
    
    /* Invisible Sync Input - Positioned far off screen but still 'available' to DOM */
    div[data-testid="stTextInput"]:has(input[placeholder="sync_bridge_v7"]) {
        position: fixed;
        left: -100vw;
        top: -100vh;
        z-index: -9999;
        opacity: 0;
        pointer-events: none;
    }
</style>
""", unsafe_allow_html=True)

# Data Loading with Caching
@st.cache_data
def load_catalogue_data():
    # Use absolute path relative to this script's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "data", "catalogue.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"Warning: Data file not found at {json_path}")
    return []

data = load_catalogue_data()

# --- Shortlist Session State ---
if 'shortlist' not in st.session_state:
    st.session_state.shortlist = set() # Store Part Numbers for uniqueness

if 'view_shortlist' not in st.session_state:
    st.session_state.view_shortlist = False
if "sync_counter" not in st.session_state:
    st.session_state.sync_counter = 0

# Helper for Base64 Thumbnails (Fixes all Cloud/Local pathing issues)
def get_base64_img(thumb_path):
    if not thumb_path: return None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Handle cases where path might be 'thumbnails/foo.jpg' or just 'foo.jpg'
        fname = os.path.basename(thumb_path)
        abs_path = os.path.join(base_dir, "static", "thumbnails", fname)
        
        if os.path.exists(abs_path):
            with open(abs_path, "rb") as f:
                data = base64.b64encode(f.read()).decode()
                return f"data:image/jpeg;base64,{data}"
    except Exception:
        pass
    return None

# --- Shortlist Sync Bridge (V7 - Ultra Robust) ---
sync_key = f"sync_v7_{st.session_state.sync_counter}"
# Using a unique placeholder is the most reliable way for JS to find the input
sync_val = st.text_input("sync_bridge", placeholder="sync_bridge_v7", key=sync_key, label_visibility="collapsed")

if sync_val and "|" in sync_val:
    try:
        part = sync_val.split("|")[0]
        if part in st.session_state.shortlist:
            st.session_state.shortlist.remove(part)
            st.toast(f"Removed from shortlist: {part}", icon="🗑️")
        else:
            st.session_state.shortlist.add(part)
            st.toast(f"Added to shortlist: {part}", icon="⭐")
        
        # Increment counter to ROTATE KEY for next time (handled by Streamlit's natural rerun)
        st.session_state.sync_counter += 1
    except Exception:
        pass

# Sidebar - Filtering
st.sidebar.title("")
selected_market = st.sidebar.selectbox("CHANNEL", ["Northcape", "Overstock", "Wayfair", "Home Depot"])

st.sidebar.divider()

# Cascaded Filter Logic (Turbo Speed)
def get_options(column, filtered_df):
    unique = filtered_df[column].unique().tolist()
    # Filter out nan, None, and empty strings strictly
    valid_options = [str(x) for x in unique if pd.notna(x) and x != "" and str(x).lower() != "nan"]
    return ["All"] + sorted(list(set(valid_options)))

df = pd.DataFrame(data)

# Channel to Count Column Mapping
channel_to_count = {
    "Northcape": "NC Image Count",
    "Overstock": "OS Image Count",
    "Wayfair": "WF Image Count",
    "Home Depot": "HD Image Count"
}

# Filter by Channel (Image Count > 0)
count_col = channel_to_count.get(selected_market)
if count_col and count_col in df.columns:
    # Force numeric conversion for reliability
    df[count_col] = pd.to_numeric(df[count_col], errors='coerce').fillna(0)
    df = df[df[count_col] > 0]

# Safety check for empty data or missing columns
if df.empty or "Collection Type" not in df.columns:
    st.error("⚠️ Catalogue data is missing or corrupted. Please run the update script.")
    st.sidebar.error("Data Load Error")
    if not df.empty:
        st.write("Columns found:", df.columns.tolist())
    st.stop()

# Filtering State
# Dynamic Type options based on data
type_options = get_options("Type", df)
selected_types = st.sidebar.multiselect("Type", type_options[1:], help="Select multiple product types") # Skip "All" for multiselect
filtered_df = df[df["Type"].isin(selected_types)] if selected_types else df

# The original 'Collection Type' contains the sheet/series names (2001, 6400, etc.)
series_options = get_options("Collection Type", filtered_df)
selected_series = st.sidebar.multiselect("Series", series_options[1:], help="Select multiple series")
if selected_series:
    filtered_df = filtered_df[filtered_df["Collection Type"].isin(selected_series)]

collection_options = get_options("Collection", filtered_df)
selected_collections = st.sidebar.multiselect("Collection", collection_options[1:], help="Select multiple collections")
if selected_collections:
    filtered_df = filtered_df[filtered_df["Collection"].isin(selected_collections)]

# Furniture specific filters
arm_opts = get_options("Arm/Table-Top", filtered_df)
if len(arm_opts) > 1:
    selected_arms = st.sidebar.multiselect("Arm/Table-Top", arm_opts[1:])
    if selected_arms:
        filtered_df = filtered_df[filtered_df["Arm/Table-Top"].isin(selected_arms)]

product_opts = get_options("Product", filtered_df)
if len(product_opts) > 1:
    selected_products = st.sidebar.multiselect("Product", product_opts[1:])
    if selected_products:
        filtered_df = filtered_df[filtered_df["Product"].isin(selected_products)]

panel_opts = get_options("Panel", filtered_df)
if len(panel_opts) > 1:
    selected_panels = st.sidebar.multiselect("Panel", panel_opts[1:])
    if selected_panels:
        filtered_df = filtered_df[filtered_df["Panel"].isin(selected_panels)]

color_opts = get_options("Color", filtered_df)
selected_colors = st.sidebar.multiselect("Color", color_opts[1:])
if selected_colors:
    filtered_df = filtered_df[filtered_df["Color"].isin(selected_colors)]

# --- Shortlist Management ---
st.sidebar.divider()
st.sidebar.markdown(f"### ⭐ Shortlist ({len(st.session_state.shortlist)})")

# View Shortlist Only Toggle
view_mode = st.sidebar.toggle("View Shortlist Only", value=st.session_state.view_shortlist)
st.session_state.view_shortlist = view_mode

if st.session_state.view_shortlist:
    filtered_df = filtered_df[filtered_df["Part Number"].isin(st.session_state.shortlist)]

# Shortlist All Visible Button
if not filtered_df.empty:
    if st.sidebar.button("Shortlist All Visible", use_container_width=True):
        visible_parts = set(filtered_df["Part Number"].astype(str).tolist())
        st.session_state.shortlist.update(visible_parts)
        st.rerun()

# Clear Shortlist Button
if st.sidebar.button("Clear All", use_container_width=True):
    st.session_state.shortlist = set()
    st.rerun()

# --- Export Section ---
if len(st.session_state.shortlist) > 0:
    st.sidebar.divider()
    st.sidebar.markdown("### 📥 Export Shortlist")
    export_format = st.sidebar.selectbox("Choose Format", ["Excel (.xlsx)", "CSV", "PDF Gallery", "Text Summary"])
    
    shortlist_data = df[df["Part Number"].isin(st.session_state.shortlist)]
    
    # Reorder columns as requested by user
    cols = shortlist_data.columns.tolist()
    ordered_cols = []
    
    # Simple prioritized list for the first few columns
    # We want: Part Number, Collection, Arm/Table-Top, Product, Panel, Color, Type...
    priority = ["Part Number", "Collection", "Arm/Table-Top", "Product", "Panel", "Color", "Type"]
    for p in priority:
        if p in cols:
            ordered_cols.append(p)
            cols.remove(p)
    
    # Add remaining columns
    ordered_cols.extend(cols)
    shortlist_data = shortlist_data[ordered_cols]
    
    if export_format == "CSV":
        csv_data = shortlist_data.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button("Download CSV", data=csv_data, file_name="NC_Shortlist.csv", mime="text/csv")
    elif export_format == "Text Summary":
        txt_data = "\n".join(shortlist_data["Part Number"].tolist())
        st.sidebar.download_button("Download Text", data=txt_data, file_name="NC_Shortlist.txt", mime="text/plain")
    elif export_format == "Excel (.xlsx)":
        # Note: Requires openpyxl
        try:
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                shortlist_data.to_excel(writer, index=False)
            st.sidebar.download_button("Download Excel", data=output.getvalue(), file_name="NC_Shortlist.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.sidebar.error("Excel Export failed. Please ensure 'openpyxl' is installed.")
    elif export_format == "PDF Gallery":
        try:
            from fpdf import FPDF
            
            class PDF(FPDF):
                def header(self):
                    self.set_font('helvetica', 'B', 22)
                    self.set_text_color(30, 64, 175) # Premium Blue
                    self.cell(0, 15, 'NORTHCAPE CATALOGUE', 0, 1, 'C')
                    self.set_draw_color(226, 232, 240) # Slate-200
                    self.line(10, 25, 200, 25)
                    self.ln(10)
                    
                def footer(self):
                    self.set_y(-15)
                    self.set_font('helvetica', 'I', 8)
                    self.set_text_color(148, 163, 184)
                    self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
            
            pdf = PDF()
            pdf.set_auto_page_break(auto=False, margin=0)
            pdf.add_page()
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            thumb_dir = os.path.join(base_dir, "static", "thumbnails")
            
            # 3x3 Grid Settings (A4 is ~210x297mm)
            margin = 10
            gutter = 5
            col_width = 60
            row_height = 85 # Fits 3 rows (~255mm + margins)
            
            items_per_page = 9
            current_col = 0
            current_row = 0
            
            for i, (_, item) in enumerate(shortlist_data.iterrows()):
                # New page every 9 items
                if i > 0 and i % 9 == 0:
                    pdf.add_page()
                    current_col = 0
                    current_row = 0
                
                # x = margin + (current_col * (col_width + gutter))
                # y = 30 + (current_row * row_height) # Start below header
                
                cell_x = margin + (current_col * (col_width + gutter))
                cell_y = 30 + (current_row * row_height)
                
                # 1. Image (Now FIRST and Zoomed)
                thumb_path = item.get('Local_Thumbnail')
                img_y_offset = cell_y
                if thumb_path:
                    fname = os.path.basename(thumb_path)
                    abs_thumb = os.path.join(thumb_dir, fname)
                    if os.path.exists(abs_thumb):
                        # 125% zoom: Original was col_width-10 (50), now ~62.5
                        # But col_width is 60, so we'll center it and use 58 to avoid gutter overlap
                        img_w = 58 
                        img_x = cell_x + (col_width - img_w) / 2
                        pdf.image(abs_thumb, x=img_x, y=cell_y, w=img_w)
                        img_y_offset += 48 # Increased offset to prevent overlap (original was 42)
                
                # 2. Part Number (Multi-cell)
                pdf.set_xy(cell_x, img_y_offset + 2)
                pdf.set_font('helvetica', 'B', 8)
                pdf.set_text_color(15, 23, 42)
                pdf.multi_cell(col_width, 4, str(item['Part Number']), ln=0, align='C')
                
                details_y = pdf.get_y() + 1
                
                # 3. Details (Conditional Ordering)
                pdf.set_font('helvetica', '', 7)
                st_type = str(item.get('Type', '')).strip()
                product_val = str(item.get('Product', '')).lower()
                is_table = 'table' in product_val
                
                if st_type == "Cushion":
                    # Cushions: Type, Collection, Color
                    fields = [
                        ("Type", item.get('Type')),
                        ("Collection", item.get('Collection')),
                        ("Color", item.get('Color'))
                    ]
                else:
                    # Furniture/Default: Type, Product, Arm, Panel, Color
                    fields = [
                        ("Type", item.get('Type')),
                        ("Product", item.get('Product')),
                        ("Arm/Table-Top", item.get('Arm/Table-Top')),
                        ("Panel", item.get('Panel'))
                    ]
                    if not is_table:
                        fields.append(("Color", item.get('Color')))
                    # Collection is secondary for furniture
                    fields.append(("Collection", item.get('Collection')))
                
                pdf.set_xy(cell_x, details_y)
                details_text = ""
                for label, val in fields:
                    if pd.notna(val) and str(val).strip() and str(val).lower() != 'nan':
                        details_text += f"{label}: {val}\n"
                
                # Centered block with left-aligned labels
                block_width = 50
                indent = (col_width - block_width) / 2
                pdf.set_x(cell_x + indent)
                
                pdf.set_text_color(100, 116, 139)
                pdf.multi_cell(block_width, 3.5, details_text, ln=0, align='L')
                
                # Move to next column/row
                current_col += 1
                if current_col >= 3:
                    current_col = 0
                    current_row += 1

            pdf_data = bytes(pdf.output())
            st.sidebar.download_button("Download PDF", data=pdf_data, file_name="NorthCape_Catalogue.pdf", mime="application/pdf")
            
            # --- PDF Preview Section ---
            st.sidebar.divider()
            st.sidebar.markdown("### 👁️ PDF Preview")
            if st.sidebar.button("Show Preview"):
                base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                st.toast("PDF Preview Generated Below!", icon="📄")
        except Exception as e:
            st.sidebar.error(f"PDF Error: {str(e)}")

# Main Content - Premium Header
st.markdown("""
<div class="hero-container">
    <div class="hero-title">NorthCape Image Library</div>
</div>
""", unsafe_allow_html=True)

# Search Bar (Match Reference)
search_query = st.text_input("", placeholder="🔍 Search Part Number, Collection, Color...")
if search_query:
    q = search_query.lower()
    # Search across all relevant text-based columns
    searchable_cols = [c for c in filtered_df.columns if not c.endswith("Image") and c != "Local_Thumbnail" and c != "Color_Link" and c != "Image_List"]
    mask = filtered_df[searchable_cols].apply(
        lambda row: row.astype(str).str.lower().str.contains(q).any(), axis=1
    )
    filtered_df = filtered_df[mask]

st.caption(f"Showing {len(filtered_df)} records")

# Pagination
items_per_page = 25 # Increased for dynamic layout (multiple of 5)
total_pages = max(1, (len(filtered_df) - 1) // items_per_page + 1)
page = st.sidebar.number_input("Page", min_value=1, max_value=total_pages, value=1)
start_idx = (page - 1) * items_per_page
end_idx = start_idx + items_per_page

market_col_prefix = {
    "Northcape": "Northcape Image",
    "Overstock": "Overstock Image",
    "Wayfair": "Wayfair Image",
    "Home Depot": "Home Depot Image"
}[selected_market]

paged_data = filtered_df.iloc[start_idx:end_idx]

# Start of the responsive grid
grid_html = '<div class="card-grid">'

# Define which fields to show in the card footer based on Type
# If Furniture: Product, Color, Arm/Table-Top, Panel
# If Cushions: Color, and potentially others if they exist
# Actually, let's just show all non-technical fields that have data
TECHNICAL_FIELDS = [
    "Thumbnail", "Dropbox Folder Path", "Part Number", "Type", "Collection", 
    "Collection Type", "Last Modified", "NC Image Count", "OS Image Count", 
    "WF Image Count", "HD Image Count", "Local_Thumbnail", "Image_List", "Color_Link", "Part Number_Link"
]

for i, (_, item) in enumerate(paged_data.iterrows()):
    # Prepare all available thumbnails for this item
    image_list = item.get("Image_List", [])
    if not image_list and item.get("Local_Thumbnail"):
        image_list = [item["Local_Thumbnail"]]
        
    # Get base64 for the top 3 images for instant swapping
    b64_images = []
    for thumb_path in image_list[:3]:
        b64 = get_base64_img(thumb_path)
        if b64: b64_images.append(b64)
    
    # Fallback to primary if empty
    if not b64_images:
        primary_b64 = get_base64_img(item.get("Local_Thumbnail"))
        if primary_b64: b64_images = [primary_b64]
    
    img_src = b64_images[0] if b64_images else ""
    
    # Check if item is shortlisted
    is_shortlisted = item["Part Number"] in st.session_state.shortlist
    shortlist_class = "active" if is_shortlisted else ""
    shortlist_icon = "⭐" if is_shortlisted else "☆"

    # Store list as Base64-encoded JSON to avoid any HTML attribute mangling
    b64_json_str = json.dumps(b64_images)
    b64_data_attr = base64.b64encode(b64_json_str.encode()).decode()

    # Card Content Logic (Conditionally hide empty/nan values)
    def get_val(key):
        val = item.get(key)
        return str(val) if pd.notna(val) and str(val).lower() != "nan" and str(val).strip() != "" else None

    # Determine fields to display dynamically
    display_fields = []
    product_val_card = str(item.get('Product', '')).lower()
    is_table_card = 'table' in product_val_card
    
    for key in item.keys():
        if key not in TECHNICAL_FIELDS and not any(x in key for x in ["Northcape Image", "Overstock Image", "Wayfair Image", "Home Depot Image"]):
            # Special check for Color on Tables
            if key == "Color" and is_table_card:
                continue
            val = get_val(key)
            if val:
                display_fields.append((key, val))

    def row_html(label, val):
        if not val: return ""
        # Handle special color link if it's the color row
        final_val = val
        if label == "Color" and pd.notna(item.get('Color_Link')):
             final_val = f'<a href="{item["Color_Link"]}" target="_blank" class="color-link">{val}</a>'
        return f'<div class="detail-row"><span class="detail-label">{label}</span><span class="detail-value">{final_val}</span></div>'

    # Image Count Badges Logic
    image_stats_html = ""
    for label, col in [("NC", "NC Image Count"), ("OS", "OS Image Count"), ("WF", "WF Image Count"), ("HD", "HD Image Count")]:
        count = item.get(col, 0)
        if pd.notna(count) and count > 0:
            image_stats_html += f'<div class="detail-row"><span class="detail-label">{label} Images</span><span class="detail-value">{int(count)}</span></div>'

    # Swap Button HTML (only if more than 1 image)
    swap_html = ""
    if len(b64_images) > 1:
        # Use a data-target and explicit pointer-events for reliability
        swap_html = f'<div class="swap-btn" data-swap-target="img-{i}" title="Next Image" style="cursor: pointer; pointer-events: auto;">🔄</div>'

    # Build detail rows for fields
    detail_rows_html = "".join([row_html(lbl, v) for lbl, v in display_fields])

    # Build card HTML with unique ID for image and data-urls for swapping
    card_html = (
        f'<div class="product-card" style="position: relative;">'
            f'<div class="shortlist-btn {shortlist_class}" data-part="{item["Part Number"]}" title="Add to Shortlist">{shortlist_icon}</div>'
            f'<div class="card-header">'
                f'<div class="badge">{item["Collection Type"]}</div>'
                f'<div class="part-number">{item["Part Number"]}</div>'
                f'<div class="collection-text">{item["Collection"]}</div>'
            f'</div>'
            f'<div class="image-container">'
                f'<img id="img-{i}" src="{img_src}" alt="Product" data-urls-b64="{b64_data_attr}" data-idx="0">'
                f'{swap_html}'
            f'</div>'
            f'<div class="card-footer">'
                f'{detail_rows_html}'
                f'<div style="margin-top: 8px; border-top: 1px solid #f1f5f9; padding-top: 8px;">'
                    f'{image_stats_html}'
                f'</div>'
            f'</div>'
        f'</div>'
    )
    grid_html += card_html

grid_html += '</div>'

# 1. Inject the Grid HTML
st.markdown(grid_html, unsafe_allow_html=True)

# 2. Inject the Image Swapper Script
# This uses an iframe-to-parent hack to bypass sanitization
# It attaches a capture-phase listener to the parent document
js_swap_html = """
<script>
(function() {
    const parentDoc = window.parent.document;
    
    // 1. Image Swapper Handler
    const handler = function(e) {
        const btn = e.target.closest('.swap-btn');
        if (!btn) return;
        
        e.preventDefault();
        e.stopPropagation();
        
        const targetId = btn.getAttribute('data-swap-target');
        const img = parentDoc.getElementById(targetId);
        if (!img) return;
        
        try {
            const b64Data = img.getAttribute('data-urls-b64');
            const urls = JSON.parse(atob(b64Data));
            if (!urls || urls.length < 2) return;
            
            let idx = parseInt(img.getAttribute('data-idx')) || 0;
            idx = (idx + 1) % urls.length;
            
            img.src = urls[idx];
            img.setAttribute('data-idx', idx);
        } catch (err) {
            console.error("Swap Error:", err);
        }
    };
    
    // 2. Shortlist Toggle Handler (V7 - Event Aggression)
    const shortlistHandler = function(e) {
        const btn = e.target.closest('.shortlist-btn');
        if (!btn) return;
        
        const part = btn.getAttribute('data-part');
        console.log("NC Checklist: Star Toggled for", part);
        
        // Find input by unique placeholder
        let targetInput = parentDoc.querySelector('input[placeholder="sync_bridge_v7"]');
        
        if (targetInput) {
            btn.style.backgroundColor = '#fef08a'; // Immediate feedback
            btn.style.transform = 'scale(0.8)';
            
            const syncValue = part + "|" + Date.now();
            
            // 1. Focus the input
            targetInput.focus();
            
            // 2. Set value via native setter (React compliance)
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            setter.call(targetInput, syncValue);
            
            // 3. Dispatch events to trigger change detection
            targetInput.dispatchEvent(new Event('input', { bubbles: true }));
            targetInput.dispatchEvent(new Event('change', { bubbles: true }));
            
            // 4. Force submit via Enter key
            const enterEv = new KeyboardEvent('keydown', {
                bubbles: true, cancelable: true, keyCode: 13, key: 'Enter', code: 'Enter'
            });
            targetInput.dispatchEvent(enterEv);
            
            // 5. Blur to finalize
            targetInput.blur();
            
            console.log("NC Checklist: V7 Bridge Sent Toggle Signal");
            
            setTimeout(() => {
                btn.style.backgroundColor = '';
                btn.style.transform = '';
            }, 500);
        } else {
            console.error("NC Checklist Error: V7 Sync Input not found in DOM");
        }
    };
    
    // 3. Persistent Connection via V7 Flag
    if (parentDoc._nc_v7_active) return;
    parentDoc._nc_v7_active = true;

    parentDoc.addEventListener('click', handler, true);
    parentDoc.addEventListener('click', shortlistHandler, true);
    console.log("NC Checklist: V7 Listeners Active");
})();
</script>
"""
components.html(js_swap_html, height=0)
