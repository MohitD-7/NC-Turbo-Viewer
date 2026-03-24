import streamlit as st
import json
import os
import pandas as pd
import base64
import hashlib
import streamlit.components.v1 as components

# Page Configuration
st.set_page_config(
    page_title="NorthCape Turbo Catalogue",
    page_icon="🛋️",
    layout="wide",
    initial_sidebar_state="auto"  # Auto-collapses on mobile (<768px)
)

# --- Authentication System ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_authentication():
    return st.session_state.get('authenticated', False)

def get_user_role():
    return st.session_state.get('user_role', None)

def login_page():
    # Native Static Serving with Cache-Busting: 
    # We append the file's modification time as a version (?v=...) 
    # This forces the browser to discard its cache and load the new 14.9MB image instantly.
    static_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "LP-Banner.jpg")
    v_time = int(os.path.getmtime(static_path)) if os.path.exists(static_path) else 0
    bg_img = f'url("app/static/LP-Banner.jpg?v={v_time}")'

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        [data-testid="stToolbar"] {{visibility: hidden !important;}}
        [data-testid="stSidebar"] {{display: none !important;}}
        [data-testid="stDecoration"] {{display: none !important;}}

        /* Background image — always fills the screen */
        .stApp {{
            font-family: 'Inter', sans-serif;
            background-image: {bg_img} !important;
            background-size: cover !important;
            background-position: center center !important;
            background-repeat: no-repeat !important;
            background-attachment: fixed !important;
            background-color: #1a2332 !important;
            min-height: 100vh !important;
            overflow-y: auto;
            transition: background-position 0.3s ease-out !important;
        }}

        @keyframes fadeSlideUp {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}

        /* Card container — geometrically centred */
        .block-container {{
            max-width: 575px !important; /* Increased by 15% from 500px */
            width: 100% !important;
            position: absolute !important;
            top: 42% !important; /* Move card 2% higher */
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            padding: 0 !important;
            z-index: 1;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
        }}

        /* Form always fills its container width */
        [data-testid="stForm"] {{
            width: 100% !important;
            box-sizing: border-box !important;
        }}

        /* --- FINAL POLISHED FROSTED GLASS --- */
        [data-testid="stForm"] {{
            /* Keep it transparent so the now-bright background shines through */
            background: rgba(255, 255, 255, 0.55) !important; 
            
            /* High blur to create the "frost," but no heavy color filters needed now */
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px) !important;
            
            /* Add a subtle inner-glow to make the glass feel like it has depth */
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.15), 
                        inset 0 0 0 1px rgba(255, 255, 255, 0.5) !important;
            
            /* Sharp, thin border to define the edge */
            border: 1px solid rgba(255, 255, 255, 0.8) !important;
            
            border-radius: 20px !important;
            padding: 1.15rem 2.3rem !important;
            animation: fadeSlideUp 0.6s ease-out;
        }}

        /* Hide column gap lines if any */
        [data-testid="stForm"] [data-testid="stHorizontalBlock"] {{
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 1.5rem !important; /* Reduced gap for a tighter look */
            align-items: flex-start !important; /* Align left and right columns to the top */
            justify-content: center !important;
        }}
        [data-testid="stForm"] [data-testid="stHorizontalBlock"] > div {{
            flex: 1 1 0% !important;
            min-width: 0 !important;
        }}

        /* Left branding panel - Desktop 2-column look */
        .login-brand-panel {{
            display: flex;
            flex-direction: column;
            justify-content: flex-start; /* Push all items to top */
            align-items: center; /* Center aligned */
            text-align: center; /* Center aligned */
            padding-top: 0.5rem !important; /* Tiny top breathing room */
            padding-right: 1.5rem !important; /* Gives breathing room to the divider line */
            border-right: 1px solid #A0ABC0; /* Faded brand-coordinated blue */
            min-height: unset !important; /* Don't stretch vertically */
        }}
        .login-brand-panel h1 {{
            color: #1a3b7a;
            font-size: 3.2rem; /* Increased from 2.8rem (~15%) */
            font-weight: 900;
            letter-spacing: 0.02em;
            /* text-transform: uppercase; removed to show exact casing */
            white-space: nowrap;
            margin: 0 auto 0.1rem auto !important; /* Top center aligned, very small bottom margin */
            line-height: 1.0; /* Tighter line height to cut invisible padding */
            display: block !important;
            text-align: center !important; /* Ensure string is exactly centered */
        }}
        /* Hide Streamlit header action (link) icons */
        [data-testid="stHeaderActionElements"], .st-header-action {{
            display: none !important;
        }}
        .login-brand-panel .subtitle {{
            color: #1e293b;
            font-size: 0.9rem;
            font-weight: 700; /* Increased weight for crispness */
            letter-spacing: 0.2em;
            text-transform: uppercase;
            margin: 0;
            text-shadow: none;
        }}
        .login-brand-panel .divider {{
            width: 200px;
            height: 2px;
            background: #1a3b7a; /* Brand Navy Blue */
            margin: 0.1rem auto 0.3rem auto; /* Very tight spacing around divider */
            border-radius: 1px;
            opacity: 1;
        }}
        .login-brand-panel .tagline {{
            color: #1e293b;
            opacity: 0.8;
            font-size: 0.8rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            margin-top: 0.1rem;
        }}

        /* --- UNIFIED FULL-WIDTH INPUTS --- */
        
        /* Force outer container to take full width */
        [data-testid="stForm"] [data-testid="stTextInput"] {{
            width: 100% !important;
            box-sizing: border-box !important;
        }}

        /* Target the actual white input box wrapper (fixes unequal lengths) */
        [data-testid="stForm"] [data-testid="stTextInput"] div[data-baseweb="input"] {{
            width: 100% !important;
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 8px !important;
            overflow: hidden !important; /* Keeps corners clean */
            padding: 0 !important; /* Removes default Streamlit padding */
        }}

        /* The text you actually type */
        [data-testid="stForm"] [data-testid="stTextInput"] input {{
            background-color: transparent !important; /* Let white wrapper show through */
            color: #1e293b !important;
            padding: 0.75rem 1rem !important;
            width: 100% !important;
            box-sizing: border-box !important;
            border: none !important;
        }}

        /* STRIP the grey background from Streamlit's eye icon container */
        [data-testid="stForm"] [data-testid="stTextInput"] div[data-baseweb="input"] > div {{
            background-color: transparent !important; 
        }}

        /* Style the eye button itself */
        [data-testid="stForm"] [data-testid="stTextInput"] button {{
            background-color: transparent !important;
            border: none !important;
            padding-right: 0.8rem !important;
            color: #64748b !important; /* Neutral grey for the eye icon */
            box-shadow: none !important;
        }}

        /* Clean focus state (blue highlight when clicking into box) */
        [data-testid="stForm"] [data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {{
            border-color: #1a3b7a !important;
            box-shadow: 0 0 0 2px rgba(26, 59, 122, 0.15) !important;
        }}

        /* Hide "Press Enter to submit" */
        [data-testid="stForm"] [data-testid="InputInstructions"] {{
            display: none !important;
        }}

        /* Labels */
        [data-testid="stForm"] label {{
            color: #0f172a !important; /* Deepest slate */
            font-weight: 700 !important;
            font-size: 0.85rem !important;
            letter-spacing: 0.02em !important;
            text-shadow: none !important;
        }}

        /* Submit button — brand blue */
        [data-testid="stForm"] [data-testid="stFormSubmitButton"] button {{
            background: #1a3b7a !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.75rem 1.5rem !important;
            font-weight: 700 !important;
            font-size: 0.95rem !important;
            letter-spacing: 0.02em !important;
            transition: all 0.2s !important;
            margin-top: 0.5rem !important;
        }}
        [data-testid="stForm"] [data-testid="stFormSubmitButton"] button:hover {{
            background: #243f8a !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }}

        /* Error messages */
        [data-testid="stForm"] .stAlert {{
            background: rgba(255, 255, 255, 0.15) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            border-radius: 10px !important;
            color: white !important;
        }}

        /* ── Mobile: stack brand panel + inputs vertically ── */
        @media (max-width: 768px) {{

            /* Mobile fixes to restore relative positioning for scrolling */
            .block-container {{
                position: relative !important;
                top: auto !important;
                left: auto !important;
                transform: none !important;
                max-width: 440px !important; /* Increased by 15% from 380px */
                margin-left: auto !important;
                margin-right: auto !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 0.5rem !important;
                padding-bottom: 0.5rem !important;
            }}

            /* Compact card padding — vertically slim on mobile */
            [data-testid="stForm"] {{
                padding: 0.6rem 1.25rem !important;
            }}

            /* Override Streamlit's internal CSS grid to force single-column stacking */
            [data-testid="stForm"] [data-testid="stHorizontalBlock"] {{
                display: grid !important;
                grid-template-columns: 1fr !important;
                flex-direction: column !important; /* fallback */
                gap: 0.4rem !important;
            }}

            /* Each column takes full grid row */
            [data-testid="stForm"] [data-testid="stHorizontalBlock"] [data-testid="stColumn"] {{
                width: 100% !important;
                min-width: 0 !important;
                max-width: 100% !important;
            }}

            /* Brand panel: Stack elements vertically under NorthCape */
            .login-brand-panel {{
                border-right: none !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                padding-right: 0 !important;
                padding-bottom: 0.4rem !important;
                min-height: unset !important;
                flex-direction: column !important;
                align-items: center !important;
                justify-content: center !important;
                text-align: center !important;
                gap: 0.1rem !important;
            }}

            .login-brand-panel h1 {{
                font-size: 2.4rem !important; /* Increased font size for mobile */
                margin-bottom: 0.1rem !important;
                width: 100% !important;
                text-align: center !important;
            }}

            .login-brand-panel .subtitle {{
                font-size: 0.8rem !important;
            }}

            .login-brand-panel .tagline {{
                font-size: 0.7rem !important;
                margin-top: 0 !important;
            }}

            /* Hide decorative divider on mobile */
            .login-brand-panel .divider {{
                display: none !important;
            }}
        }}

        /* ── Very small phones (< 420px) ── */
        @media (max-width: 420px) {{
            [data-testid="stForm"] {{
                padding: 1.25rem 1rem !important;
                border-radius: 14px !important;
            }}

            .login-brand-panel h1 {{
                font-size: 2.0rem !important; /* Increased font size for tiny phones */
            }}
        }}
    </style>
    """, unsafe_allow_html=True)

    # Mouse-tracking parallax on background image
    components.html("""
    <script>
    (function() {
        var doc = window.parent.document;
        // Clean up catalogue handlers from previous session
        if (window.parent._nc_handlers) {
            var old = window.parent._nc_handlers;
            for (var k in old) { if (typeof old[k] === 'function') { doc.removeEventListener('click', old[k], true); doc.removeEventListener('touchstart', old[k], true); doc.removeEventListener('keydown', old[k]); } }
            window.parent._nc_handlers = null;
        }

        var app = doc.querySelector('.stApp');
        if (!app || app._parallaxActive) return;
        app._parallaxActive = true;
        doc.addEventListener('mousemove', function(e) {
            var x = (e.clientX / window.parent.innerWidth - 0.5) * 2;
            var y = (e.clientY / window.parent.innerHeight - 0.5) * 2;
            var posX = 50 - x * 3;
            var posY = 40 - y * 3;
            app.style.setProperty('background-position', posX + '% ' + posY + '%', 'important');
        });
    })();
    </script>
    """, height=0)

    with st.form("login_form"):
        left_col, right_col = st.columns([1, 1])

        with left_col:
            st.markdown("""
            <div class="login-brand-panel">
                <h1>NorthCape</h1>
                <div class="divider"></div>
                <p class="subtitle">Image Library</p>
                <p class="tagline">Premium Furniture Visuals & Assets</p>
            </div>
            """, unsafe_allow_html=True)

        with right_col:
            username = st.text_input("Username", placeholder="Username")
            password = st.text_input("Password", type="password", placeholder="Password")
            submit = st.form_submit_button("Sign In", use_container_width=True)

        if submit and username and password:
            hashed_pw = hash_password(password)

            try:
                users_config = st.secrets.get("users", {})
            except Exception:
                users_config = {}

            admin_users = list(users_config.get("admin_users", []))
            admin_passwords = list(users_config.get("admin_passwords", []))
            dealer_users = list(users_config.get("dealer_users", []))
            dealer_passwords = list(users_config.get("dealer_passwords", []))

            authenticated = False

            if username in admin_users:
                idx = admin_users.index(username)
                if idx < len(admin_passwords) and hashed_pw == admin_passwords[idx]:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "admin"
                    st.session_state.username = username
                    authenticated = True

            if not authenticated and username in dealer_users:
                idx = dealer_users.index(username)
                if idx < len(dealer_passwords) and hashed_pw == dealer_passwords[idx]:
                    st.session_state.authenticated = True
                    st.session_state.user_role = "dealer"
                    st.session_state.username = username
                    authenticated = True

            if authenticated:
                st.rerun()
            else:
                st.error("Invalid username or password")

        elif submit:
            st.warning("Please enter both username and password")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not check_authentication():
    login_page()
    st.stop()

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

    /* Hide sidebar collapse button on desktop only */
    @media (min-width: 768px) {
        [data-testid="stSidebarCollapseButton"] {display: none !important;}
    }
    
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

    /* ============================================
       MOBILE RESPONSIVE BREAKPOINTS
       ============================================ */

    /* Mobile Small (<480px) - Portrait Phones */
    @media (max-width: 479px) {
        /* Maximize screen space */
        .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            padding-top: 0.5rem !important;
        }

        /* Two column layout on phones */
        .card-grid {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 8px;
            padding-top: 0.75rem;
        }

        /* Compact cards for 2-column layout */
        .product-card {
            max-width: 100%;
            padding: 0.4rem;
        }

        /* Appropriately sized touch targets */
        .shortlist-btn {
            width: 40px !important;
            height: 40px !important;
            font-size: 1.2rem;
            top: 4px;
            right: 4px;
        }

        /* Compact typography for 2-column */
        .hero-title {
            font-size: 1.25rem;
            margin-bottom: 0.25rem;
        }

        .detail-row {
            font-size: 0.7rem;
            padding: 0.15rem 0;
            line-height: 1.2;
        }

        .part-number {
            font-size: 0.85rem;
        }

        .badge {
            font-size: 0.6rem;
            padding: 0.1rem 0.35rem;
        }

        /* Taller image ratio for mobile 2-column */
        .image-container {
            aspect-ratio: 0.9 / 1;
            margin: 0.25rem 0;
        }

        /* Disable transform on mobile */
        .product-card:hover {
            transform: none;
        }
    }

    /* Mobile Medium (480px-767px) - Landscape Phones */
    @media (min-width: 480px) and (max-width: 767px) {
        .block-container {
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
            padding-top: 0.75rem !important;
        }

        /* 2 columns with better spacing */
        .card-grid {
            grid-template-columns: repeat(2, 1fr) !important;
            gap: 12px;
        }

        /* Touch-friendly buttons */
        .shortlist-btn {
            width: 42px !important;
            height: 42px !important;
            font-size: 1.3rem;
        }

        .hero-title {
            font-size: 1.5rem;
        }

        .product-card {
            padding: 0.5rem;
        }

        .detail-row {
            font-size: 0.75rem;
        }

        .product-card:hover {
            transform: translateY(-4px);
        }
    }

    /* Tablet (768px-899px) - Bridge to Desktop */
    @media (min-width: 768px) and (max-width: 899px) {
        .block-container {
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
        }

        /* 2-3 columns auto-fit */
        .card-grid {
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)) !important;
            gap: 20px;
        }

        /* Slightly larger than desktop touch targets */
        .shortlist-btn {
            width: 40px !important;
            height: 40px !important;
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
    
    /* Image Container & Carousel */
    .image-container {
        position: relative;
    }

    .carousel-controls {
        position: absolute;
        bottom: 8px;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 8px;
        opacity: 0;
        transition: opacity 0.2s;
    }

    .product-card:hover .carousel-controls {
        opacity: 1;
    }

    .carousel-arrow {
        background: rgba(255, 255, 255, 0.95);
        width: 28px;
        height: 28px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1rem;
        font-weight: 700;
        color: #334155;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.15s;
        user-select: none;
        -webkit-user-select: none;
    }

    .carousel-arrow:hover {
        background: white;
        transform: scale(1.1);
        border-color: #3b82f6;
        color: #3b82f6;
    }

    .image-counter {
        background: rgba(255, 255, 255, 0.95);
        padding: 3px 8px;
        border-radius: 10px;
        font-size: 0.65rem;
        font-weight: 600;
        color: #64748b;
        border: 1px solid #e2e8f0;
    }

    .carousel-dots {
        position: absolute;
        bottom: 42px;
        left: 0;
        right: 0;
        display: flex;
        justify-content: center;
        gap: 4px;
        opacity: 0;
        transition: opacity 0.2s;
    }

    .product-card:hover .carousel-dots {
        opacity: 1;
    }

    .carousel-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        cursor: pointer;
        transition: background 0.2s, transform 0.15s;
    }

    .carousel-dot:hover {
        transform: scale(1.3);
    }

    /* Legacy swap-btn hidden (replaced by carousel) */
    .swap-btn {
        display: none;
    }

    /* Slide-in Detail Panel (Google Photos style) */
    .detail-panel {
        position: fixed;
        top: 0;
        right: 0;
        width: 35vw;
        height: 100vh;
        background: white;
        z-index: 99999;
        transform: translateX(100%);
        transition: transform 0.3s ease-out;
        box-shadow: -8px 0 30px rgba(0, 0, 0, 0.15);
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }

    .detail-panel.active {
        transform: translateX(0);
    }

    /* Backdrop — no blocking, just visual hint */
    .detail-backdrop {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: none;
        z-index: -1;
        pointer-events: none;
    }

    .detail-backdrop.active {
        display: block;
    }

    .detail-panel-close {
        position: absolute;
        top: 12px;
        right: 12px;
        width: 36px;
        height: 36px;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 50%;
        border: 1px solid #e2e8f0;
        font-size: 1.3rem;
        cursor: pointer;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        z-index: 10;
        color: #64748b;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s;
    }

    .detail-panel-close:hover {
        background: white;
        transform: scale(1.1);
        color: #0f172a;
    }

    /* Image section — top portion */
    .detail-panel-image {
        flex: 0 0 52%;
        background: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
        border-bottom: 1px solid #e2e8f0;
    }

    .detail-panel-image img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }

    .dp-nav {
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        background: rgba(255, 255, 255, 0.95);
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 1.3rem;
        font-weight: 700;
        color: #334155;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
        transition: all 0.15s;
        z-index: 5;
        opacity: 0;
    }

    .detail-panel-image:hover .dp-nav {
        opacity: 1;
    }

    .dp-nav:hover {
        background: white;
        transform: translateY(-50%) scale(1.1);
        border-color: #3b82f6;
        color: #3b82f6;
    }

    .dp-nav.prev { left: 16px; }
    .dp-nav.next { right: 16px; }

    .dp-counter {
        position: absolute;
        bottom: 12px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.95);
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #64748b;
        border: 1px solid #e2e8f0;
    }

    .dp-dots {
        position: absolute;
        bottom: 40px;
        left: 0;
        right: 0;
        display: flex;
        justify-content: center;
        gap: 5px;
    }

    .dp-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        cursor: pointer;
        transition: background 0.2s, transform 0.15s;
    }

    .dp-dot:hover {
        transform: scale(1.4);
    }

    /* Info section — bottom portion (no scroll on desktop) */
    .detail-panel-info {
        flex: 1;
        overflow: hidden;
        padding: 0.85rem 1.25rem;
    }

    .dp-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
        margin-bottom: 0.25rem;
    }

    .dp-part-number {
        font-size: 1.1rem;
        font-weight: 800;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.02em;
    }

    .dp-star-btn {
        width: 36px;
        height: 36px;
        min-width: 36px;
        border-radius: 50%;
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        cursor: pointer;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.15s;
    }

    .dp-star-btn:hover {
        background: #fef3c7;
        border-color: #fbbf24;
        transform: scale(1.1);
    }

    .dp-star-btn.active {
        background: #fef3c7;
        border-color: #fbbf24;
    }

    .dp-collection-label {
        color: #64748b;
        font-size: 0.8rem;
        margin-bottom: 0.35rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .dp-badge {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        color: #1e40af;
        padding: 0.15rem 0.5rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
    }

    .dp-divider {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 0.3rem 0;
    }

    .dp-detail-row {
        display: flex;
        justify-content: space-between;
        padding: 0.2rem 0;
        font-size: 0.78rem;
    }

    .dp-detail-label {
        color: #94a3b8;
        font-weight: 500;
    }

    .dp-detail-value {
        color: #334155;
        font-weight: 600;
        text-align: right;
    }

    .dp-actions {
        display: flex;
        gap: 8px;
        margin-top: 1rem;
    }

    .dp-action-btn {
        flex: 1;
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        color: #334155;
        font-size: 0.8rem;
        font-weight: 600;
        cursor: pointer;
        text-align: center;
        transition: all 0.15s;
        text-decoration: none;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
    }

    .dp-action-btn:hover {
        background: #e2e8f0;
        border-color: #cbd5e1;
    }

    .dp-action-btn.active {
        background: #fef3c7;
        border-color: #fbbf24;
        color: #92400e;
    }

    /* Mobile: full-screen overlay */
    @media (max-width: 768px) {
        .detail-panel {
            width: 100vw;
        }
        .detail-panel-image {
            flex: 0 0 50%;
        }
        .detail-panel-info {
            overflow-y: auto;
        }
        .dp-nav {
            opacity: 1;
        }
        .carousel-controls {
            opacity: 1;
        }
        .carousel-dots {
            opacity: 1;
        }
    }

    /* Tablet: slightly wider panel */
    @media (min-width: 769px) and (max-width: 1200px) {
        .detail-panel {
            width: 45vw;
        }
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

    /* ============================================
       TOUCH DEVICE OPTIMIZATIONS
       ============================================ */

    /* Touch Device Enhancements */
    @media (hover: none) and (pointer: coarse) {
        /* Visual touch feedback */
        .shortlist-btn:active {
            transform: scale(0.85) !important;
            background: #fef08a !important;
        }

        .carousel-arrow:active {
            transform: scale(0.85) !important;
            background: #dbeafe !important;
        }

        /* Disable hover effects on touch devices */
        .product-card:hover .image-container img {
            transform: scale(1);
        }

        .product-card:hover {
            transform: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            border-color: #e2e8f0;
        }

        /* Prevent double-tap zoom on buttons */
        .shortlist-btn, .carousel-arrow, .carousel-dot {
            touch-action: manipulation;
            -webkit-user-select: none;
            user-select: none;
        }
    }

    /* ============================================
       MOBILE APP EXPERIENCE (Bottom Navigation)
       ============================================ */
    @media (max-width: 767px) {
        /* Hide sidebar initially on mobile */
        [data-testid="stSidebar"] {
            position: fixed !important;
            left: 0 !important;
            top: 60px !important;
            bottom: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            z-index: 2000 !important;
            background: white !important;
            transform: translateY(100%) !important;
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow-y: auto !important;
            border-top-left-radius: 16px !important;
            border-top-right-radius: 16px !important;
        }

        /* Show sidebar when modal is open */
        .filter-modal.open ~ [data-testid="stSidebar"],
        body.filters-open [data-testid="stSidebar"] {
            transform: translateY(0) !important;
        }

        /* Hamburger Filter Button - Bottom Left */
        .mobile-filter-btn {
            position: fixed;
            bottom: 20px;
            left: 16px;
            width: 56px;
            height: 56px;
            border-radius: 28px;
            background: #3b82f6;
            color: white;
            border: none;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: 300;
            cursor: pointer;
            z-index: 999;
            transition: all 0.3s;
        }

        .mobile-filter-btn:active {
            transform: scale(0.9);
            background: #2563eb;
        }

        /* Backdrop for filters - only top bar */
        .filter-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 60px;
            background: rgba(0, 0, 0, 0.5);
            z-index: 2001;
            display: none;
            align-items: center;
            justify-content: center;
        }

        .filter-backdrop.open {
            display: flex;
        }

        .filter-close-btn {
            background: rgba(255, 255, 255, 0.95);
            color: #64748b;
            border: none;
            padding: 6px 12px;
            border-radius: 16px;
            font-size: 0.8rem;
            font-weight: 500;
            cursor: pointer;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
        }

        .filter-close-btn:active {
            transform: scale(0.95);
        }

        /* Swipe handle for pull-down gesture */
        [data-testid="stSidebar"]::before {
            content: '';
            display: block;
            width: 40px;
            height: 4px;
            background: #cbd5e1;
            border-radius: 2px;
            margin: 12px auto 8px;
        }

        /* Thinner scrollbar */
        ::-webkit-scrollbar {
            width: 4px;
        }
    }

    /* Desktop: Ensure sidebar is visible and fixed on left */
    @media (min-width: 768px) {
        .mobile-filter-btn,
        .filter-modal,
        .filter-backdrop {
            display: none !important;
        }

        /* Reset sidebar to default desktop behavior with FIXED WIDTH */
        [data-testid="stSidebar"] {
            position: relative !important;
            transform: none !important;
            width: 21rem !important;
            min-width: 21rem !important;
            max-width: 21rem !important;
            z-index: auto !important;
            top: auto !important;
            bottom: auto !important;
            left: auto !important;
            border-radius: 0 !important;
        }

        /* Fix sidebar width and make multiselect wrap */
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            width: 100% !important;
            overflow-x: hidden !important;
        }

        /* Force multiselect items to wrap - target all possible containers */
        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="select"] > div > div,
        [data-testid="stSidebar"] [data-baseweb="select"] span[data-baseweb="tag"]:first-child {
            flex-wrap: wrap !important;
            display: flex !important;
        }

        /* Control tag sizing */
        [data-testid="stSidebar"] [data-baseweb="tag"] {
            max-width: calc(100% - 20px) !important;
            margin: 2px !important;
        }

        /* Force the multiselect value container to wrap */
        [data-testid="stSidebar"] div[class*="ValueContainer"] {
            flex-wrap: wrap !important;
            max-width: 100% !important;
        }

        /* Ensure multiselect container doesn't expand sidebar */
        [data-testid="stSidebar"] div[data-baseweb="select"],
        [data-testid="stSidebar"] div[class*="multiValue"] {
            max-width: 100% !important;
            overflow: visible !important;
        }

        /* Hide swipe handle on desktop */
        [data-testid="stSidebar"]::before {
            display: none !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Data Loading with Caching - Auto busts when file changes
@st.cache_data
def load_catalogue_data(file_mtime):
    # Use absolute path relative to this script's directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "data", "catalogue.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"Warning: Data file not found at {json_path}")
    return []

base_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(base_dir, "data", "catalogue.json")
mtime = os.path.getmtime(json_path) if os.path.exists(json_path) else 0
data = load_catalogue_data(mtime)

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
        parts_str = sync_val.split("|")[0]
        parts = [p.strip() for p in parts_str.split(",") if p.strip()]
        for part in parts:
            if part in st.session_state.shortlist:
                st.session_state.shortlist.remove(part)
            else:
                st.session_state.shortlist.add(part)

        # Increment counter to ROTATE KEY for next time (handled by Streamlit's natural rerun)
        st.session_state.sync_counter += 1
    except Exception:
        pass

# Sidebar - Filtering
st.sidebar.title("")

user_role = get_user_role()

# Added back per user request
st.sidebar.markdown(f"<div style='color: #0f172a; font-weight: 700; font-size: 1.15rem; padding-bottom: 2px;'>Hi, {st.session_state.get('username', '')}</div>", unsafe_allow_html=True)

st.sidebar.divider()

# Channel selection: role-based
if user_role == "dealer":
    # Dealers only see North Cape products - no channel selector shown
    selected_channels = ["Northcape"]
    channel_logic = "OR"
else:
    all_channels = ["Northcape", "Overstock", "Wayfair", "Home Depot"]
    show_all = st.sidebar.checkbox("All Channels", value=True, key="all_channels_toggle")

    if show_all:
        selected_channels = ["All"]
    else:
        selected_channels = st.sidebar.multiselect("CHANNEL", all_channels, default=[all_channels[0]])
        if len(selected_channels) > 1:
            channel_logic = st.sidebar.radio("Match", ["OR - any selected channel", "AND - all selected channels"], horizontal=True, key="channel_logic")
        else:
            channel_logic = "OR"

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
    "Overstock": "BY Image Count",
    "Wayfair": "WF Image Count",
    "Home Depot": "HD Image Count"
}

# If "All" is selected, treat as no channel filter
if "All" not in selected_channels and selected_channels:
    use_and = len(selected_channels) > 1 and channel_logic.startswith("AND")
    # Start with True for AND, False for OR
    channel_mask = pd.Series(use_and, index=df.index)
    for ch in selected_channels:
        count_col = channel_to_count.get(ch)
        if count_col and count_col in df.columns:
            df[count_col] = pd.to_numeric(df[count_col], errors='coerce').fillna(0)
            if use_and:
                channel_mask = channel_mask & (df[count_col] > 0)
            else:
                channel_mask = channel_mask | (df[count_col] > 0)
    df = df[channel_mask]

# Dealer restriction: ensure only NC products visible
if user_role == "dealer":
    df["NC Image Count"] = pd.to_numeric(df["NC Image Count"], errors='coerce').fillna(0)
    df = df[df["NC Image Count"] > 0]

# Safety check for empty data or missing columns
if df.empty or "Collection Type" not in df.columns:
    st.error("⚠️ Catalogue data is missing or corrupted. Please run the update script.")
    st.sidebar.error("Data Load Error")
    if not df.empty:
        st.write("Columns found:", df.columns.tolist())
    st.stop()

# Dynamic Type options based on data
type_options = get_options("Type", df)
selected_types = st.sidebar.multiselect("Category", type_options[1:], help="Select multiple product categories") # Skip "All" for multiselect
filtered_df = df[df["Type"].isin(selected_types)] if selected_types else df

# The original 'Collection Type' contains the sheet/series names (2001, 6400, etc.)
# Series dropdown removed as requested by the client

collection_options = get_options("Collection", filtered_df)
selected_collections = st.sidebar.multiselect("Collections", collection_options[1:], help="Select multiple collections")
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

# --- Favorites List Management ---
st.sidebar.divider()
st.sidebar.markdown(f"### ⭐ Favorites List ({len(st.session_state.shortlist)})")

# View Favorites List Only Toggle
view_mode = st.sidebar.toggle("View Favorites Only", value=st.session_state.view_shortlist)
st.session_state.view_shortlist = view_mode

if st.session_state.view_shortlist:
    filtered_df = filtered_df[filtered_df["Part Number"].isin(st.session_state.shortlist)]

# Favorites List All Visible Button
if not filtered_df.empty:
    if st.sidebar.button("Add All Visible to Favorites", use_container_width=True):
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
    st.sidebar.markdown("### 📥 Export Favorites List")
    export_format = st.sidebar.selectbox("Choose Format", ["Excel (.xlsx)", "PDF Gallery"])

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

    if export_format == "Excel (.xlsx)":
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

# --- Upload Excel: Enrich Part Numbers with Catalogue Data ---
st.sidebar.divider()
st.sidebar.markdown("### 📤 Upload Part Numbers")
uploaded_file = st.sidebar.file_uploader(
    "Upload Excel with Part Numbers in the first column",
    type=["xlsx"],
    key="part_upload",
    label_visibility="collapsed"
)

if uploaded_file is not None:
    try:
        import io as _io
        uploaded_df = pd.read_excel(uploaded_file, engine='openpyxl')

        if uploaded_df.empty or uploaded_df.shape[1] == 0:
            st.sidebar.error("Uploaded file is empty.")
        else:
            # Read part numbers from first column (whatever the header is)
            first_col_name = uploaded_df.columns[0]
            part_numbers = uploaded_df[first_col_name].dropna().astype(str).str.strip().tolist()

            # Match against catalogue
            matched = df[df["Part Number"].isin(part_numbers)]

            # Reorder columns with priority
            cols = matched.columns.tolist()
            ordered = []
            prio = ["Part Number", "Collection", "Arm/Table-Top", "Product", "Panel", "Color", "Type"]
            for p in prio:
                if p in cols:
                    ordered.append(p)
                    cols.remove(p)
            ordered.extend(cols)
            matched = matched[ordered]

            found = len(matched)
            not_found = [pn for pn in part_numbers if pn not in matched["Part Number"].values]

            st.sidebar.success(f"Matched **{found}** of {len(part_numbers)} part numbers")
            if not_found:
                with st.sidebar.expander(f"{len(not_found)} not found"):
                    st.sidebar.caption("\n".join(not_found[:50]))
                    if len(not_found) > 50:
                        st.sidebar.caption(f"...and {len(not_found) - 50} more")

            if found > 0:
                output_buf = _io.BytesIO()
                with pd.ExcelWriter(output_buf, engine='openpyxl') as writer:
                    matched.to_excel(writer, index=False, sheet_name="Enriched Data")
                st.sidebar.download_button(
                    f"Download Enriched Excel ({found} items)",
                    data=output_buf.getvalue(),
                    file_name="NC_Enriched_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    except Exception as e:
        st.sidebar.error(f"Upload Error: {str(e)}")

# Main Content - Premium Header
# Anchor to target the exact columns block
# Header styling is now fully handled dynamically via JavaScript below to ensure compatibility
# across all Streamlit container rendering updates.

# Add anchor for Back to Top button
st.markdown('<div id="top-anchor"></div>', unsafe_allow_html=True)

header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown("""
    <div class="hero-container" style="padding: 0 !important; margin: 0 !important; display: flex; align-items: center;">
        <div class="hero-title" style="margin: 0 !important; line-height: 1.1;">NorthCape Image Library</div>
    </div>
    """, unsafe_allow_html=True)
with header_col2:
    if st.button("Logout"):
        for key in ['authenticated', 'user_role', 'username']:
            st.session_state.pop(key, None)
        components.html("<script>if(window.parent._nc_header_observer) window.parent._nc_header_observer.disconnect(); window.parent._nc_handlers = null; window.parent._shortlistQueue = [];</script>", height=0)
        st.rerun()

    components.html("""
    <script>
    (function() {
        var pDoc = window.parent.document;
        var applyTweaks = function() {
            var btns = pDoc.querySelectorAll('button');
            btns.forEach(b => {
                if(b.innerText.includes('Logout') && !b.classList.contains('nc-btn-styled')) {
                    b.classList.add('nc-btn-styled');
                    b.style.cssText = "border: 1px solid #3b82f6 !important; border-radius: 50px !important; color: #1e40af !important; background-color: transparent !important; padding: 0 16px !important; height: 32px !important; min-height: 32px !important; width: auto !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; font-weight: 600 !important; font-size: 0.8rem !important; transition: all 0.2s !important;";
                    b.onmouseover = function() { b.style.backgroundColor='#eff6ff'; b.style.borderColor='#1e40af'; };
                    b.onmouseout = function() { b.style.backgroundColor='transparent'; b.style.borderColor='#3b82f6'; };
                    if(b.parentElement) {
                        b.parentElement.style.cssText = "display: flex !important; justify-content: flex-end !important; width: 100% !important;";
                        if(b.parentElement.parentElement) b.parentElement.parentElement.style.cssText = "display: flex !important; justify-content: flex-end !important; width: 100% !important;";
                    }
                }
            });
            var titles = pDoc.querySelectorAll('.hero-title');
            titles.forEach(t => {
                var row = t.closest('div[data-testid="stHorizontalBlock"]');
                if (row && !row.classList.contains('nc-row-aligned')) {
                    row.classList.add('nc-row-aligned');
                    row.style.alignItems = 'center';
                }
            });
        };
        applyTweaks();
        if (!window.parent._nc_header_observer) {
            var obs = new MutationObserver(applyTweaks);
            obs.observe(pDoc.body, { childList: true, subtree: true });
            window.parent._nc_header_observer = obs;
        }
    })();
    </script>
    """, height=0)
# Mobile Filter Button and Backdrop - HTML (visible in page)
mobile_filter_html = """
<button class="mobile-filter-btn" id="mobile-filter-button">
    ☰
</button>

<div class="filter-backdrop" id="filter-backdrop">
    <button class="filter-close-btn" id="close-filters">× Close</button>
</div>
"""
st.markdown(mobile_filter_html, unsafe_allow_html=True)

# JavaScript for filter toggle (in separate component with height=0)
mobile_filter_js = """
<script>
(function() {
    const parentDoc = window.parent.document;

    function toggleFilters() {
        const backdrop = parentDoc.querySelector('#filter-backdrop');
        const body = parentDoc.body;

        if (backdrop && body) {
            // Toggle classes
            backdrop.classList.toggle('open');
            body.classList.toggle('filters-open');
        }
    }

    // Attach event listeners
    const filterBtn = parentDoc.querySelector('#mobile-filter-button');
    const closeBtn = parentDoc.querySelector('#close-filters');
    const backdrop = parentDoc.querySelector('#filter-backdrop');

    if (filterBtn) {
        filterBtn.addEventListener('click', toggleFilters);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent backdrop click from also firing
            toggleFilters();
        });
    }

    if (backdrop) {
        backdrop.addEventListener('click', function(e) {
            // Only close if clicking backdrop itself, not the button
            if (e.target === backdrop) {
                toggleFilters();
            }
        });
    }

    // Swipe-down gesture to close filters (only from top area)
    const sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
    if (sidebar) {
        let startY = 0;
        let startX = 0;
        let currentY = 0;
        let isDragging = false;
        let hasStartedDrag = false;

        sidebar.addEventListener('touchstart', function(e) {
            if (parentDoc.body.classList.contains('filters-open')) {
                startY = e.touches[0].clientY;
                startX = e.touches[0].clientX;
                currentY = startY;
                isDragging = false;
                hasStartedDrag = false;

                // Only enable swipe from top 80px of sidebar
                const rect = sidebar.getBoundingClientRect();
                const touchYRelative = startY - rect.top;
                if (touchYRelative > 80) {
                    // Don't enable swipe, user is touching content area
                    return;
                }
            }
        });

        sidebar.addEventListener('touchmove', function(e) {
            if (!parentDoc.body.classList.contains('filters-open')) return;

            currentY = e.touches[0].clientY;
            const diffY = currentY - startY;
            const diffX = Math.abs(e.touches[0].clientX - startX);

            // Only start dragging if moved >15px down and <10px horizontally
            if (!hasStartedDrag && diffY > 15 && diffX < 10) {
                hasStartedDrag = true;
                isDragging = true;
            }

            if (isDragging && diffY > 0) {
                e.preventDefault();
                sidebar.style.transform = `translateY(${diffY}px)`;
            }
        }, { passive: false });

        sidebar.addEventListener('touchend', function(e) {
            if (!isDragging) {
                sidebar.style.transform = '';
                return;
            }

            isDragging = false;
            hasStartedDrag = false;

            const diff = currentY - startY;

            // If dragged more than 100px, close the filters
            if (diff > 100) {
                toggleFilters();
            }

            // Reset transform
            sidebar.style.transform = '';
        });
    }
})();
</script>
"""
components.html(mobile_filter_js, height=0)

# Search Bar (Match Reference)
search_query = st.text_input("Search Catalogue", placeholder="🔍 Search Part Number, Collections, Color...", label_visibility="collapsed")
if search_query:
    q = search_query.lower()
    # Search across all relevant text-based columns
    searchable_cols = [c for c in filtered_df.columns if not c.endswith("Image") and c != "Local_Thumbnail" and c != "Color_Link" and c != "Image_List"]
    mask = filtered_df[searchable_cols].apply(
        lambda row: row.astype(str).str.lower().str.contains(q).any(), axis=1
    )
    filtered_df = filtered_df[mask]

st.caption(f"Showing {len(filtered_df)} records")

# Pagination Logic - Dynamic based on viewport
# Smart defaults: Show more items to fill larger screens
# Grid auto-adjusts: 3 cols (900-1199px), 4 cols (1200-1599px), 5 cols (1600px+)
# Default to ~3 rows worth for typical 1080p+ displays
items_per_page = 40  # Accommodates 3-4 rows across common screen sizes (8-10 cards for 3-4 cols, 12-15 for 5 cols)
total_pages = max(1, (len(filtered_df) - 1) // items_per_page + 1)

if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

if st.session_state.current_page > total_pages:
    st.session_state.current_page = total_pages

start_idx = (st.session_state.current_page - 1) * items_per_page
end_idx = start_idx + items_per_page

channel_to_prefix = {
    "Northcape": "Northcape Image",
    "Overstock": "Overstock Image",
    "Wayfair": "Wayfair Image",
    "Home Depot": "Home Depot Image"
}
# Use the first non-"All" channel's prefix, or default to Northcape
first_channel = next((ch for ch in selected_channels if ch != "All"), "Northcape")
market_col_prefix = channel_to_prefix.get(first_channel, "Northcape Image")

paged_data = filtered_df.iloc[start_idx:end_idx]

# Start of the responsive grid
grid_html = '<div class="card-grid">'

# Define which fields to show in the card footer based on Type
# If Furniture: Product, Color, Arm/Table-Top, Panel
# If Cushions: Color, and potentially others if they exist
# Actually, let's just show all non-technical fields that have data
TECHNICAL_FIELDS = [
    "Thumbnail", "Dropbox Folder Path", "Part Number", "Type", "Collection", 
    "Collection Type", "Last Modified", "NC Image Count", "OS Image Count", "BY Image Count",
    "WF Image Count", "HD Image Count", "Local_Thumbnail", "Image_List", "Color_Link", "Part Number_Link"
]

for i, (_, item) in enumerate(paged_data.iterrows()):
    # Prepare all available thumbnails for this item
    image_list = item.get("Image_List", [])
    if not image_list and item.get("Local_Thumbnail"):
        image_list = [item["Local_Thumbnail"]]
        
    # Get base64 for all available images (up to 5)
    b64_images = []
    for thumb_path in image_list[:5]:
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
        
        # Clean specific labels: only keep what's after the first '-'
        if label.lower() in ["arm/table-top", "arm/table top", "panel"] and "-" in str(val):
            final_val = str(val).split("-", 1)[1].strip()
            
        return f'<div class="detail-row"><span class="detail-label">{label}</span><span class="detail-value">{final_val}</span></div>'

    # Image Count Badges Logic (dealers only see NC)
    image_stats_html = ""
    badge_channels = [("NC", "NC Image Count")] if user_role == "dealer" else [("NC", "NC Image Count"), ("BY", "BY Image Count"), ("WF", "WF Image Count"), ("HD", "HD Image Count")]
    for label, col in badge_channels:
        count = item.get(col, 0)
        if pd.notna(count) and count > 0:
            image_stats_html += f'<div class="detail-row"><span class="detail-label">{label} Images</span><span class="detail-value">{int(count)}</span></div>'

    # Carousel HTML (only if more than 1 image)
    carousel_html = ""
    if len(b64_images) > 1:
        dots_html = "".join([
            f'<div class="carousel-dot" data-target="img-{i}" data-idx="{idx}" style="background: {"#3b82f6" if idx == 0 else "#cbd5e1"};"></div>'
            for idx in range(len(b64_images))
        ])
        carousel_html = (
            f'<div class="carousel-dots">{dots_html}</div>'
            f'<div class="carousel-controls">'
                f'<div class="carousel-arrow carousel-prev" data-target="img-{i}">&#8249;</div>'
                f'<div class="image-counter" id="counter-{i}">1/{len(b64_images)}</div>'
                f'<div class="carousel-arrow carousel-next" data-target="img-{i}">&#8250;</div>'
            f'</div>'
        )

    # Build detail rows for fields
    detail_rows_html = "".join([row_html(lbl, v) for lbl, v in display_fields])

    # Build card HTML with unique ID for image and data-urls for carousel
    card_html = (
        f'<div class="product-card" style="position: relative;">'
            f'<div class="shortlist-btn {shortlist_class}" data-part="{item["Part Number"]}" title="Add to Favorites">{shortlist_icon}</div>'
            f'<div class="card-header">'
                f'<div class="badge">{item["Type"]}</div>'
                f'<div class="part-number">{item["Part Number"]}</div>'
                f'<div class="collection-text">{item["Collection"]}</div>'
            f'</div>'
            f'<div class="image-container">'
                f'<img id="img-{i}" src="{img_src}" alt="Product" data-urls-b64="{b64_data_attr}" data-idx="0" data-total="{len(b64_images)}" style="cursor: pointer;">'
                f'{carousel_html}'
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

# Slide-in Detail Panel HTML
detail_panel_html = """
<div class="detail-backdrop" id="detail-backdrop"></div>
<div class="detail-panel" id="detail-panel">
    <div class="detail-panel-close" id="detail-panel-close">&times;</div>
    <div class="detail-panel-image">
        <div class="dp-nav prev" id="dp-prev">&#8249;</div>
        <img id="dp-img" src="" alt="Product Detail">
        <div class="dp-nav next" id="dp-next">&#8250;</div>
        <div class="dp-dots" id="dp-dots"></div>
        <div class="dp-counter" id="dp-counter"></div>
    </div>
    <div class="detail-panel-info" id="dp-info"></div>
</div>
"""

# 1. Inject the Grid HTML + Detail Panel
st.markdown(grid_html + detail_panel_html, unsafe_allow_html=True)

# 2. Inject Carousel + Detail Panel + Shortlist Script
js_html = """
<script>
(function() {
    var parentDoc = window.parent.document;

    // --- CLEANUP OLD HANDLERS (prevents duplicates & stale listeners) ---
    if (window.parent._nc_handlers) {
        var old = window.parent._nc_handlers;
        parentDoc.removeEventListener('click', old.carousel, true);
        parentDoc.removeEventListener('click', old.dot, true);
        parentDoc.removeEventListener('click', old.panelOpen, true);
        parentDoc.removeEventListener('click', old.panelControl, true);
        parentDoc.removeEventListener('click', old.shortlist, true);
        parentDoc.removeEventListener('keydown', old.keyboard);
        parentDoc.removeEventListener('touchstart', old.carousel, true);
        parentDoc.removeEventListener('touchstart', old.dot, true);
        parentDoc.removeEventListener('touchstart', old.shortlist, true);
    }

    // --- Shortlist queue (persists across reruns) ---
    if (!window.parent._shortlistQueue) window.parent._shortlistQueue = [];

    function flushShortlist() {
        var queue = window.parent._shortlistQueue;
        if (!queue || queue.length === 0) return;
        var targetInput = parentDoc.querySelector('input[placeholder="sync_bridge_v7"]');
        if (!targetInput) return;

        var syncValue = queue.join(',') + '|' + Date.now();
        window.parent._shortlistQueue = [];

        targetInput.focus();
        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(targetInput, syncValue);
        targetInput.dispatchEvent(new Event('input', { bubbles: true }));
        targetInput.dispatchEvent(new Event('change', { bubbles: true }));
        targetInput.dispatchEvent(new KeyboardEvent('keydown', {
            bubbles: true, cancelable: true, keyCode: 13, key: 'Enter', code: 'Enter'
        }));
        targetInput.blur();
    }

    function queueShortlist(part) {
        // XOR: if already queued (toggled back), remove it; otherwise add
        var q = window.parent._shortlistQueue;
        var idx = q.indexOf(part);
        if (idx > -1) { q.splice(idx, 1); } else { q.push(part); }

        // Debounce: flush after 700ms of no activity
        clearTimeout(window.parent._shortlistTimer);
        window.parent._shortlistTimer = setTimeout(flushShortlist, 700);
    }

    // --- Helper: navigate image on a card ---
    function navigateCard(img, newIdx) {
        try {
            var b64Data = img.getAttribute('data-urls-b64');
            var urls = JSON.parse(atob(b64Data));
            if (!urls || urls.length < 2) return;

            var idx = ((newIdx % urls.length) + urls.length) % urls.length;
            img.src = urls[idx];
            img.setAttribute('data-idx', idx);

            var imgId = img.id;
            var num = imgId.replace('img-', '');
            var counter = parentDoc.getElementById('counter-' + num);
            if (counter) counter.textContent = (idx + 1) + '/' + urls.length;

            var dots = parentDoc.querySelectorAll('.carousel-dot[data-target="' + imgId + '"]');
            dots.forEach(function(dot, i) {
                dot.style.background = i === idx ? '#3b82f6' : '#cbd5e1';
            });
        } catch (err) { /* ignore */ }
    }

    // --- 1. Carousel Arrow Handler ---
    var carouselHandler = function(e) {
        var arrow = e.target.closest('.carousel-arrow');
        if (!arrow) return;
        e.preventDefault();
        e.stopPropagation();
        var targetId = arrow.getAttribute('data-target');
        var img = parentDoc.getElementById(targetId);
        if (!img) return;
        var idx = parseInt(img.getAttribute('data-idx')) || 0;
        navigateCard(img, arrow.classList.contains('carousel-prev') ? idx - 1 : idx + 1);
    };

    // --- 2. Dot Click Handler ---
    var dotHandler = function(e) {
        var dot = e.target.closest('.carousel-dot');
        if (!dot) return;
        e.preventDefault();
        e.stopPropagation();
        var img = parentDoc.getElementById(dot.getAttribute('data-target'));
        if (img) navigateCard(img, parseInt(dot.getAttribute('data-idx')));
    };

    // --- 3. Slide-in Detail Panel ---
    var panelUrls = [];
    var panelIdx = 0;

    function updatePanelDots() {
        var c = parentDoc.getElementById('dp-dots');
        if (!c) return;
        var h = '';
        for (var i = 0; i < panelUrls.length; i++) {
            h += '<div class="dp-dot" data-dp-idx="' + i + '" style="background:' + (i === panelIdx ? '#3b82f6' : '#cbd5e1') + ';"></div>';
        }
        c.innerHTML = h;
    }

    function updatePanelImage() {
        var dpImg = parentDoc.getElementById('dp-img');
        var dpCounter = parentDoc.getElementById('dp-counter');
        if (dpImg) dpImg.src = panelUrls[panelIdx];
        if (dpCounter) dpCounter.textContent = (panelIdx + 1) + '/' + panelUrls.length;
        updatePanelDots();
    }

    function openPanel(img) {
        try {
            panelUrls = JSON.parse(atob(img.getAttribute('data-urls-b64')));
            panelIdx = parseInt(img.getAttribute('data-idx')) || 0;
        } catch (err) {
            panelUrls = [img.src];
            panelIdx = 0;
        }

        var panel = parentDoc.getElementById('detail-panel');
        var backdrop = parentDoc.getElementById('detail-backdrop');
        var dpImg = parentDoc.getElementById('dp-img');
        var dpInfo = parentDoc.getElementById('dp-info');
        if (!panel || !dpImg) return;

        dpImg.src = panelUrls[panelIdx];
        updatePanelDots();
        var dpCounter = parentDoc.getElementById('dp-counter');
        if (dpCounter) dpCounter.textContent = (panelIdx + 1) + '/' + panelUrls.length;

        var card = img.closest('.product-card');
        if (card && dpInfo) {
            var partNum = card.querySelector('.part-number');
            var collection = card.querySelector('.collection-text');
            var badge = card.querySelector('.badge');
            var shortlistBtn = card.querySelector('.shortlist-btn');
            var isShortlisted = shortlistBtn && shortlistBtn.classList.contains('active');
            var partValue = shortlistBtn ? shortlistBtn.getAttribute('data-part') : '';

            var rows = card.querySelectorAll('.card-footer .detail-row');
            var rowsHtml = '';
            rows.forEach(function(row) {
                var label = row.querySelector('.detail-label');
                var value = row.querySelector('.detail-value');
                if (label && value) {
                    rowsHtml += '<div class="dp-detail-row"><span class="dp-detail-label">' + label.innerHTML + '</span><span class="dp-detail-value">' + value.innerHTML + '</span></div>';
                }
            });

            dpInfo.innerHTML =
                '<div class="dp-header-row">' +
                    '<div class="dp-part-number">' + (partNum ? partNum.textContent : '') + '</div>' +
                    '<div class="dp-star-btn ' + (isShortlisted ? 'active' : '') + '" id="dp-shortlist-btn" data-part="' + partValue + '">' +
                        (isShortlisted ? '&#11088;' : '&#9734;') +
                    '</div>' +
                '</div>' +
                '<div class="dp-collection-label">' +
                    '<span class="dp-badge">' + (badge ? badge.textContent : '') + '</span> ' +
                    (collection ? collection.textContent : '') +
                '</div>' +
                '<hr class="dp-divider">' +
                rowsHtml;
        }

        panel.classList.add('active');
        if (backdrop) backdrop.classList.add('active');

        if (window.innerWidth > 768) {
            var collapseBtn = parentDoc.querySelector('[data-testid="stSidebarCollapseButton"] button, [data-testid="collapsedControl"] button');
            var sidebar = parentDoc.querySelector('[data-testid="stSidebar"]');
            if (sidebar && sidebar.getAttribute('aria-expanded') === 'true' && collapseBtn) {
                collapseBtn.click();
            }
        }
    }

    function closePanel() {
        var panel = parentDoc.getElementById('detail-panel');
        var backdrop = parentDoc.getElementById('detail-backdrop');
        if (panel) panel.classList.remove('active');
        if (backdrop) backdrop.classList.remove('active');
    }

    function panelNavigate(dir) {
        if (panelUrls.length < 2) return;
        panelIdx = ((panelIdx + dir) % panelUrls.length + panelUrls.length) % panelUrls.length;
        updatePanelImage();
    }

    var panelOpenHandler = function(e) {
        if (e.target.closest('.carousel-arrow') || e.target.closest('.carousel-dot') ||
            e.target.closest('.shortlist-btn') || e.target.closest('.detail-panel') ||
            e.target.closest('.detail-backdrop')) return;
        var img = e.target.closest('.image-container img');
        if (!img) return;
        e.preventDefault();
        e.stopPropagation();
        openPanel(img);
    };

    var panelControlHandler = function(e) {
        if (e.target.closest('#detail-panel-close')) { closePanel(); return; }

        var prevBtn = e.target.closest('#dp-prev');
        if (prevBtn) { e.stopPropagation(); panelNavigate(-1); return; }
        var nextBtn = e.target.closest('#dp-next');
        if (nextBtn) { e.stopPropagation(); panelNavigate(1); return; }

        var dpDot = e.target.closest('.dp-dot');
        if (dpDot) {
            e.stopPropagation();
            var idx = parseInt(dpDot.getAttribute('data-dp-idx'));
            if (!isNaN(idx) && idx >= 0 && idx < panelUrls.length) {
                panelIdx = idx;
                updatePanelImage();
            }
            return;
        }

        // Shortlist button in panel — uses same queue
        var dpShortlist = e.target.closest('#dp-shortlist-btn');
        if (dpShortlist) {
            e.stopPropagation();
            e.preventDefault();
            var part = dpShortlist.getAttribute('data-part');
            if (part) {
                dpShortlist.classList.toggle('active');
                dpShortlist.innerHTML = dpShortlist.classList.contains('active') ? '&#11088;' : '&#9734;';
                // Also toggle the card's star
                var cardBtn = parentDoc.querySelector('.shortlist-btn[data-part="' + part + '"]');
                if (cardBtn) {
                    cardBtn.classList.toggle('active');
                    cardBtn.innerHTML = cardBtn.classList.contains('active') ? '⭐' : '☆';
                }
                queueShortlist(part);
            }
            return;
        }

        if (e.target.id === 'detail-backdrop') { closePanel(); }
    };

    var keyboardHandler = function(e) {
        var panel = parentDoc.getElementById('detail-panel');
        if (!panel || !panel.classList.contains('active')) return;
        if (e.key === 'Escape') closePanel();
        if (e.key === 'ArrowLeft') panelNavigate(-1);
        if (e.key === 'ArrowRight') panelNavigate(1);
    };

    // --- 4. Shortlist Toggle (card grid) — instant visual + debounced sync ---
    var shortlistHandler = function(e) {
        var btn = e.target.closest('.shortlist-btn');
        if (!btn) return;
        e.preventDefault();
        e.stopPropagation();

        var part = btn.getAttribute('data-part');
        if (!part) return;

        // Immediate visual toggle
        btn.classList.toggle('active');
        btn.innerHTML = btn.classList.contains('active') ? '⭐' : '☆';

        // Pulse animation
        btn.style.transform = 'scale(0.8)';
        setTimeout(function() { btn.style.transform = ''; }, 200);

        // Queue for batch sync (debounced 700ms)
        queueShortlist(part);
    };

    // --- Register all handlers (capture phase) ---
    parentDoc.addEventListener('click', carouselHandler, true);
    parentDoc.addEventListener('click', dotHandler, true);
    parentDoc.addEventListener('click', panelOpenHandler, true);
    parentDoc.addEventListener('click', panelControlHandler, true);
    parentDoc.addEventListener('click', shortlistHandler, true);
    parentDoc.addEventListener('keydown', keyboardHandler);
    parentDoc.addEventListener('touchstart', carouselHandler, true);
    parentDoc.addEventListener('touchstart', dotHandler, true);
    parentDoc.addEventListener('touchstart', shortlistHandler, true);

    // Store references for cleanup on next rerun
    window.parent._nc_handlers = {
        carousel: carouselHandler,
        dot: dotHandler,
        panelOpen: panelOpenHandler,
        panelControl: panelControlHandler,
        shortlist: shortlistHandler,
        keyboard: keyboardHandler
    };

    console.log('NC Catalogue: V10 Listeners Active');
})();
</script>
"""
components.html(js_html, height=0)

# Bottom Center Pagination (Modern) 
st.markdown("<br><hr style='border: none; border-top: 1px solid #e2e8f0; margin: 10px 0 20px 0;'>", unsafe_allow_html=True)
st.markdown("""
<style>
/* Style the pagination buttons */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
</style>
""", unsafe_allow_html=True)

pag_container = st.container()
with pag_container:
    pc_left, pc_prev, pc_mid, pc_next, pc_right = st.columns([2, 1, 1.5, 1, 2])

    with pc_prev:
        if st.button("⬅️ Previous", disabled=(st.session_state.current_page <= 1), use_container_width=True):
            st.session_state.current_page -= 1
            st.rerun()

    with pc_mid:
        st.markdown(f"<div style='text-align: center; padding-top: 8px; font-weight: 600; color: #475569;'>Page {st.session_state.current_page} of {total_pages}</div>", unsafe_allow_html=True)

    with pc_next:
        if st.button("Next ➡️", disabled=(st.session_state.current_page >= total_pages), use_container_width=True):
            st.session_state.current_page += 1
            st.rerun()

    with pc_right:
        # Back to Top button - aligned to extreme right (matching Logout position)
        st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center;">
            <button id="back-to-top-btn" style="padding:8px 16px;
                   background:white;
                   color:#1e40af;
                   border:2px solid #1e40af;
                   border-radius:8px;
                   font-size:14px;
                   font-weight:600;
                   cursor:pointer;
                   box-shadow:0 2px 8px rgba(30,64,175,0.15);
                   transition:all 0.3s;
                   outline:none;
                   white-space:nowrap;">
                Back to Top
            </button>
        </div>
        <style>
        #back-to-top-btn:hover {
            background:#1e40af !important;
            color:white !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(30,64,175,0.3) !important;
        }
        </style>
        """, unsafe_allow_html=True)

# Add JavaScript functionality for Back to Top button
back_to_top_script = """
<script>
(function() {
    var btn = window.parent.document.getElementById('back-to-top-btn');
    if (btn && !btn.getAttribute('data-listener-added')) {
        btn.setAttribute('data-listener-added', 'true');
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();

            // Try to find and scroll to the anchor
            var anchor = window.parent.document.getElementById('top-anchor');
            if (anchor) {
                anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                // Fallback: scroll the main app container
                var app = window.parent.document.querySelector('.stApp');
                if (app) {
                    app.scrollTo({ top: 0, behavior: 'smooth' });
                } else {
                    // Last resort
                    window.parent.scrollTo({ top: 0, behavior: 'smooth' });
                }
            }
        });
    }
})();
</script>
"""
components.html(back_to_top_script, height=0)
