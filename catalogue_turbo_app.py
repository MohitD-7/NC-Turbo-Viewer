import streamlit as st
import json
import os
import pandas as pd
import base64

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
col_type = st.sidebar.selectbox("Type", type_options)
filtered_df = df[df["Type"] == col_type] if col_type != "All" else df

# The original 'Collection Type' contains the sheet/series names (2001, 6400, etc.)
series = st.sidebar.selectbox("Series", get_options("Collection Type", filtered_df))
if series != "All":
    filtered_df = filtered_df[filtered_df["Collection Type"] == series]

col_name = st.sidebar.selectbox("Collection", get_options("Collection", filtered_df))
if col_name != "All":
    filtered_df = filtered_df[filtered_df["Collection"] == col_name]

# Furniture specific filters - only show if available in filtered data
arm_opts = get_options("Arm/Table-Top", filtered_df)
if len(arm_opts) > 1:
    arm = st.sidebar.selectbox("Arm/Table-Top", arm_opts)
    if arm != "All":
        filtered_df = filtered_df[filtered_df["Arm/Table-Top"] == arm]

product_opts = get_options("Product", filtered_df)
if len(product_opts) > 1:
    product = st.sidebar.selectbox("Product", product_opts)
    if product != "All":
        filtered_df = filtered_df[filtered_df["Product"] == product]

panel_opts = get_options("Panel", filtered_df)
if len(panel_opts) > 1: # Only show if there are actual options besides "All"
    panel = st.sidebar.selectbox("Panel", panel_opts)
    if panel != "All":
        filtered_df = filtered_df[filtered_df["Panel"] == panel]

color = st.sidebar.selectbox("Color", get_options("Color", filtered_df))
if color != "All":
    filtered_df = filtered_df[filtered_df["Color"] == color]

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
    
    # Store list as JSON string for JS
    b64_json = json.dumps(b64_images).replace("'", "&apos;")

    # Card Content Logic (Conditionally hide empty/nan values)
    def get_val(key):
        val = item.get(key)
        return str(val) if pd.notna(val) and str(val).lower() != "nan" and str(val).strip() != "" else None

    # Determine fields to display dynamically
    display_fields = []
    # Identify all keys in the item that are not technical or image-related
    for key in item.keys():
        if key not in TECHNICAL_FIELDS and not any(x in key for x in ["Northcape Image", "Overstock Image", "Wayfair Image", "Home Depot Image"]):
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
        # Use a data-target attribute instead of inline onclick for better reliability
        swap_html = f'<div class="swap-btn" data-swap-target="img-{i}" title="Next Image">🔄</div>'

    # Build detail rows for fields
    detail_rows_html = "".join([row_html(lbl, v) for lbl, v in display_fields])

    # Build card HTML with unique ID for image and data-urls for swapping
    card_html = (
        f'<div class="product-card">'
            f'<div class="card-header">'
                f'<div class="badge">{item["Collection Type"]}</div>'
                f'<div class="part-number">{item["Part Number"]}</div>'
                f'<div class="collection-text">{item["Collection"]}</div>'
            f'</div>'
            f'<div class="image-container">'
                f'<img id="img-{i}" src="{img_src}" alt="Product" data-urls=\'{b64_json}\' data-idx="0">'
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

# Inject JavaScript for instant image swapping
# Note: Using Event Delegation for maximum reliability in Streamlit
js_swap = """
<script>
(function() {
    // Single event listener for all swap buttons (Event Delegation)
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.swap-btn');
        if (!btn) return;
        
        const targetId = btn.getAttribute('data-swap-target');
        const img = document.getElementById(targetId);
        if (!img) return;
        
        try {
            const urls = JSON.parse(img.getAttribute('data-urls'));
            if (!urls || urls.length < 2) return;
            
            let idx = parseInt(img.getAttribute('data-idx')) || 0;
            idx = (idx + 1) % urls.length;
            
            img.src = urls[idx];
            img.setAttribute('data-idx', idx);
        } catch (err) {
            console.error("Swap error:", err);
        }
    });
})();
</script>
"""
st.markdown(grid_html + js_swap, unsafe_allow_html=True)
