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

    /* IRONCLAD: Hide the entire Streamlit Header AND SideBar */
    header[data-testid="stHeader"], 
    section[data-testid="stSidebar"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* REMOVE BRANDING: Hide Menu and Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none !important;}
    
    /* Adjust Main Content to take full width since sidebar is hidden */
    .stMain {
        margin-left: 0 !important;
    }
    
    /* FALL-SAFE: Target specific elements if they escape the header hide */
    [data-testid="stStatusWidget"],
    .viewerBadge_container__1QSob,
    button[title="View on GitHub"], 
    button[title="Fork this app"] {
        display: none !important;
    }

    /* IRONCLAD FIXED LEFT PANEL - SEPARATE ENTITY */
    /* Target the first column and FIX it to the viewport */
    [data-testid="column"]:nth-of-type(1) {
        position: fixed !important;
        top: 0 !important;
        left: 0 !important;
        width: 20% !important; /* Fixed width for the sidebar */
        height: 100vh !important;
        background: white !important;
        padding: 2rem 1.5rem !important;
        border-right: 1px solid #e2e8f0 !important;
        z-index: 1000 !important;
        overflow-y: auto !important;
    }
    
    /* Ensure the vertical block inside the fixed column takes full width */
    [data-testid="column"]:nth-of-type(1) [data-testid="stVerticalBlock"] {
        width: 100% !important;
    }
    
    /* OFFSET THE MAIN CONTENT AREA - Prevent overlap */
    [data-testid="column"]:nth-of-type(2) {
        margin-left: 22% !important; /* Slightly more than sidebar width for spacing */
        width: 78% !important;
        padding-top: 1rem !important;
    }

    /* Remove the default sidebar entirely from DOM visibility */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
</style>

<script>
// Ironclad fail-safe to keep branding hidden
const ironcladClean = () => {
    const selectors = ['header[data-testid="stHeader"]', 'section[data-testid="stSidebar"]', 'button[title="View on GitHub"]', 'button[title="Fork this app"]', '.stDeployButton'];
    selectors.forEach(s => {
        const els = document.querySelectorAll(s);
        els.forEach(el => { el.style.display = 'none'; el.style.visibility = 'hidden'; });
    });
};
setInterval(ironcladClean, 500);
</script>
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

# Create Main Columns ([1, 4] ratio for permanent left filters)
left_col, right_col = st.columns([1, 4], gap="large")

# Cascaded Filter Logic (Turbo Speed)
def get_options(column, filtered_df):
    unique = filtered_df[column].unique().tolist()
    return ["All"] + sorted([str(x) for x in unique if x])

with left_col:
    st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)
    # Market Selector
    selected_market = st.selectbox("CHANNEL", ["Northcape", "Overstock", "Wayfair", "Home Depot"])
    
    df = pd.DataFrame(data)
    
    # Safety check for empty data or missing columns
    if df.empty or "Collection Type" not in df.columns:
        st.error("⚠️ Catalogue data is missing or corrupted.")
        st.stop()

    # Filtering State
    col_type = st.selectbox("COLLECTION TYPE", get_options("Collection Type", df))
    filtered_df = df[df["Collection Type"] == col_type] if col_type != "All" else df
    
    col_name = st.selectbox("COLLECTION", get_options("Collection", filtered_df))
    if col_name != "All":
        filtered_df = filtered_df[filtered_df["Collection"] == col_name]
    
    arm = st.selectbox("ARM/TABLE-TOP", get_options("Arm/Table-Top", filtered_df))
    if arm != "All":
        filtered_df = filtered_df[filtered_df["Arm/Table-Top"] == arm]
    
    product = st.selectbox("PRODUCT", get_options("Product", filtered_df))
    if product != "All":
        filtered_df = filtered_df[filtered_df["Product"] == product]
    
    color = st.selectbox("COLOR", get_options("Color", filtered_df))
    if color != "All":
        filtered_df = filtered_df[filtered_df["Color"] == color]
        
    # Pagination in left column
    items_per_page = 25
    total_pages = max(1, (len(filtered_df) - 1) // items_per_page + 1)
    page = st.number_input("PAGE", min_value=1, max_value=total_pages, value=1)
    
    st.markdown(f'<div style="color: #64748b; font-size: 0.8rem; padding-top: 1rem;">Showing {len(filtered_df)} records</div>', unsafe_allow_html=True)

with right_col:
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

    market_col_prefix = {
        "Northcape": "Northcape Image",
        "Overstock": "Overstock Image",
        "Wayfair": "Wayfair Image",
        "Home Depot": "Home Depot Image"
    }[selected_market]
    
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paged_data = filtered_df.iloc[start_idx:end_idx]
    
    # Start of the responsive grid
    grid_html = '<div class="card-grid">'
    
    for i, (_, item) in enumerate(paged_data.iterrows()):
        # Indestructible Image Loading: Try Local -> Fallback to Dropbox
        dropbox_src = ""
        for j in range(1, 16):
            url_key = f"{market_col_prefix} {j}"
            if pd.notna(item.get(url_key)) and item[url_key]:
                dropbox_src = str(item[url_key]).replace("dl=0", "raw=1").replace("dl=1", "raw=1")
                break
                
        img_src = ""
        local_thumb = item.get("Local_Thumbnail")
        if pd.notna(local_thumb) and local_thumb:
            thumb_filename = os.path.basename(str(local_thumb))
            # Use relative path for maximum compatibility
            img_src = f"app/static/thumbnails/{thumb_filename}"
        else:
            img_src = dropbox_src
    
        # Fail-safe handler: If local image fails, swap to dropbox instantly
        onerror_attr = f'onerror="this.onerror=null;this.src=\'{dropbox_src}\';"' if dropbox_src else ""
    
        # Card Content
        color_display = f'<a href="{item["Color_Link"]}" target="_blank" class="color-link">{item["Color"]}</a>' if pd.notna(item.get('Color_Link')) else item["Color"]
        
        panel_html = ""
        if pd.notna(item.get('Panel')) and item['Panel']:
            panel_html = f'<div class="detail-row"><span class="detail-label">Panel</span><span class="detail-value">{item["Panel"]}</span></div>'
    
        # Build card HTML without any leading whitespace to avoid markdown code blocks
        card_html = (
            f'<div class="product-card">'
                f'<div class="card-header">'
                    f'<div class="badge">{item["Collection Type"]}</div>'
                    f'<div class="part-number">{item["Part Number"]}</div>'
                    f'<div class="collection-text">{item["Collection"]}</div>'
                f'</div>'
                f'<div class="image-container">'
                    f'<img src="{img_src}" {onerror_attr} alt="Product">'
                f'</div>'
                f'<div class="card-footer">'
                    f'<div class="detail-row"><span class="detail-label">Type</span><span class="detail-value">{item["Type"]}</span></div>'
                    f'<div class="detail-row"><span class="detail-label">Product</span><span class="detail-value">{item["Product"]}</span></div>'
                    f'<div class="detail-row"><span class="detail-label">Color</span><span class="detail-value">{color_display}</span></div>'
                    f'<div class="detail-row"><span class="detail-label">Arm</span><span class="detail-value">{item.get("Arm/Table-Top", "N/A")}</span></div>'
                    f'{panel_html}'
                f'</div>'
            f'</div>'
        )
        grid_html += card_html
    
    grid_html += '</div>'
    st.markdown(grid_html, unsafe_allow_html=True)
