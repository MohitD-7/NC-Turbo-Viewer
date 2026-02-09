import streamlit as st
import json
import os
import pandas as pd

# Page Configuration
st.set_page_config(
    page_title="NorthCape Turbo Catalogue",
    page_icon="🛋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
        gap: 20px;
        width: 100%;
        padding-top: 1rem;
    }
    
    /* Cap at 5 columns if the screen is large or zoom is low */
    @media (min-width: 1600px) {
        .card-grid {
            grid-template-columns: repeat(5, 1fr);
        }
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
        background: #f8fafc;
        border-radius: 12px;
        aspect-ratio: 1.2 / 1;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    
    .image-container img {
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
        transition: transform 0.5s ease;
    }
    
    .product-card:hover .image-container img {
        transform: scale(1.08);
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
def load_data():
    # Use absolute path relative to this script's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "data", "catalogue.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"Warning: Data file not found at {json_path}")
    return []

data = load_data()

# Sidebar - Filtering
st.sidebar.title("")
selected_market = st.sidebar.selectbox("CHANNEL", ["Northcape", "Overstock", "Wayfair", "Home Depot"])

st.sidebar.divider()

# Cascaded Filter Logic (Turbo Speed)
def get_options(column, filtered_df):
    unique = filtered_df[column].unique().tolist()
    return ["All"] + sorted([str(x) for x in unique if x])

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
    df = df[df[count_col] > 0]

# Safety check for empty data or missing columns
if df.empty or "Collection Type" not in df.columns:
    st.error("⚠️ Catalogue data is missing or corrupted. Please run the update script.")
    st.sidebar.error("Data Load Error")
    st.stop()

# Filtering State
col_type = st.sidebar.selectbox("Collection Type", get_options("Collection Type", df))
filtered_df = df[df["Collection Type"] == col_type] if col_type != "All" else df

col_name = st.sidebar.selectbox("Collection", get_options("Collection", filtered_df))
if col_name != "All":
    filtered_df = filtered_df[filtered_df["Collection"] == col_name]

arm = st.sidebar.selectbox("Arm/Table-Top", get_options("Arm/Table-Top", filtered_df))
if arm != "All":
    filtered_df = filtered_df[filtered_df["Arm/Table-Top"] == arm]

product = st.sidebar.selectbox("Product", get_options("Product", filtered_df))
if product != "All":
    filtered_df = filtered_df[filtered_df["Product"] == product]

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
    searchable_cols = [c for c in filtered_df.columns if not c.endswith("Image") and c != "Local_Thumbnail" and c != "Color_Link"]
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

for i, (_, item) in enumerate(paged_data.iterrows()):
    # Optimized Image Priority
    img_src = ""
    local_thumb = item.get("Local_Thumbnail")
    
    if pd.notna(local_thumb) and local_thumb:
        thumb_filename = os.path.basename(str(local_thumb))
        # Use cloud-friendly GitHub Raw URLs for the hosted version, local paths for local dev
        if os.environ.get("STREAMLIT_SHARING_MODE") or os.environ.get("STREAMLIT_SERVER_GATHER_USAGE_STATS") == "false":
            img_src = f"https://raw.githubusercontent.com/MohitD-7/NC-Turbo-Viewer/main/static/thumbnails/{thumb_filename}"
        else:
            img_src = f"static/thumbnails/{thumb_filename}"
    
    # Fallback URL if local fails
    if not img_src:
        for j in range(1, 16):
            url_key = f"{market_col_prefix} {j}"
            if pd.notna(item.get(url_key)) and item[url_key]:
                img_src = str(item[url_key]).replace("dl=0", "raw=1").replace("dl=1", "raw=1")
                break

    # Card Content
    color_display = f'<a href="{item["Color_Link"]}" target="_blank" class="color-link">{item["Color"]}</a>' if pd.notna(item.get('Color_Link')) else item["Color"]
    
    panel_html = ""
    if pd.notna(item.get('Panel')) and item['Panel']:
        panel_html = f'<div class="detail-row"><span class="detail-label">Panel</span><span class="detail-value">{item["Panel"]}</span></div>'

    # Image Count Badges Logic
    image_stats_html = ""
    for label, col in [("NC", "NC Image Count"), ("OS", "OS Image Count"), ("WF", "WF Image Count"), ("HD", "HD Image Count")]:
        count = item.get(col, 0)
        if pd.notna(count) and count > 0:
            image_stats_html += f'<div class="detail-row"><span class="detail-label">{label} Images</span><span class="detail-value">{int(count)}</span></div>'

    # Build card HTML without any leading whitespace to avoid markdown code blocks
    card_html = (
        f'<div class="product-card">'
            f'<div class="card-header">'
                f'<div class="badge">{item["Collection Type"]}</div>'
                f'<div class="part-number">{item["Part Number"]}</div>'
                f'<div class="collection-text">{item["Collection"]}</div>'
            f'</div>'
            f'<div class="image-container">'
                f'<img src="{img_src}" alt="Product">'
            f'</div>'
            f'<div class="card-footer">'
                f'<div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">{item["Type"]}</span></div>'
                f'<div class="detail-row"><span class="detail-label">Product</span><span class="detail-value">{item["Product"]}</span></div>'
                f'<div class="detail-row"><span class="detail-label">Color</span><span class="detail-value">{color_display}</span></div>'
                f'<div class="detail-row"><span class="detail-label">Arm/Table-Top</span><span class="detail-value">{item.get("Arm/Table-Top", "N/A")}</span></div>'
                f'{panel_html}'
                f'<div style="margin-top: 8px; border-top: 1px solid #f1f5f9; padding-top: 8px;">'
                    f'{image_stats_html}'
                f'</div>'
            f'</div>'
        f'</div>'
    )
    grid_html += card_html

grid_html += '</div>'
st.markdown(grid_html, unsafe_allow_html=True)
