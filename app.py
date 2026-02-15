import streamlit as st
import pandas as pd
import datetime
from engine import fetch_and_rank
from database import init_db, save_article, get_saved_articles, remove_saved_article, add_source, get_sources

# --- INITIALIZE DATABASE ---
init_db()

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Strategic Knowledge Dashboard", layout="wide", initial_sidebar_state="collapsed")

# --- SESSION STATE ---
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "saved_links" not in st.session_state:
    st.session_state.saved_links = set(get_saved_articles()["link"].tolist())

# --- CUSTOM CSS (Terminal Elite v4.1 - Refined) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    @import url('https://cdn.jsdelivr.net/npm/lucide-static@0.321.0/font/lucide.min.css');

    :root {
        --terminal-bg: #0B111D;
        --terminal-surface: #1E293B;
        --terminal-accent: #3B82F6;
        --terminal-border: #334155;
        --terminal-text: #F1F5F9;
        --terminal-muted: #94A3B8;
    }

    html, body, [class*="st-"] {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        background-color: var(--terminal-bg);
        color: var(--terminal-text);
    }

    /* Streamlit UI Reset */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stHeader"] {display: none;}
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* TOP HEADER BAR */
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 25px;
        background: var(--terminal-bg);
        border-bottom: 1px solid var(--terminal-border);
        position: sticky;
        top: 0;
        z-index: 1000;
    }
    .header-left { display: flex; align-items: center; gap: 20px; }
    .icon-btn { color: var(--terminal-text); font-size: 1.1rem; cursor: pointer; opacity: 0.8; transition: opacity 0.2s; }
    .sync-pill {
        background: var(--terminal-surface);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        border: 1px solid var(--terminal-border);
        cursor: pointer;
        color: var(--terminal-text);
        text-decoration: none;
    }

    /* Aggressive Spacing Reset */
    [data-testid="stVerticalBlock"] > div {
        gap: 0px !important;
    }
    .stSelectbox { margin-bottom: -15px !important; }

    /* FILTER & COMPACT BUTTONS */
    .filter-section {
        padding: 0px 25px 10px 25px;
        position: relative;
        z-index: 1001; /* Ensure filters are above table pull-up */
    }
    
    /* UNIFIED TERMINAL TABLE */
    .terminal-container {
        padding: 0 0 100px 0;
        margin-top: -30px !important; /* Reduced pull-up to prevent overlap */
        position: relative;
        z-index: 1;
    }
    .terminal-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }
    .terminal-table th {
        text-align: left;
        padding: 6px 25px; /* Minimal padding */
        color: var(--terminal-muted);
        font-weight: 600;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-bottom: 2px solid var(--terminal-border);
        background: rgba(15, 23, 42, 0.95);
    }
    .terminal-table td {
        padding: 6px 25px; /* Minimal padding */
        border-bottom: 1px solid var(--terminal-border);
        font-size: 13px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .tr-row:hover {
        background: rgba(59, 130, 246, 0.08);
    }
    
    .status-dot {
        width: 7px; height: 7px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    .status-active { background: #3B82F6; }
    .status-new { background: #10B981; }
    
    .action-link {
        color: var(--terminal-accent);
        text-decoration: none;
        font-weight: 500;
        cursor: pointer;
    }
    .save-btn {
        background: none;
        border: none;
        color: var(--terminal-muted);
        cursor: pointer;
        font-size: 1rem;
        transition: color 0.2s;
    }
    .save-btn:hover { color: var(--terminal-accent); }
    .save-btn.active { color: #F59E0B; }

    /* BOTTOM NAVIGATION */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: var(--terminal-bg);
        border-top: 1px solid var(--terminal-border);
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding: 10px 0;
        z-index: 1001;
    }
    .nav-btn {
        background: none;
        border: none;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 4px;
        color: var(--terminal-muted);
        font-size: 10px;
        cursor: pointer;
        padding: 5px 15px;
        transition: all 0.2s;
    }
    .nav-btn.active { color: var(--terminal-accent); }
    .nav-btn i { font-size: 1.2rem; }

</style>
""", unsafe_allow_html=True)

# --- NAVIGATION INJECTOR ---
# Since Streamlit buttons triggers reruns, we use them inside the bottom nav mockup
def set_page(page_name):
    st.session_state.current_page = page_name
    st.rerun()

# --- DATA FETCHING ---
@st.cache_data(ttl=14400)
def get_data():
    try:
        sources_df = pd.read_csv("sources.csv")
        return fetch_and_rank(sources_df)
    except:
        return pd.DataFrame()

# --- COMPONENTS ---

def render_header(title):
    st.markdown(f"""
    <div class="header-bar">
        <div class="header-left">
            <i class="lucide-search icon-btn"></i>
            <span style="font-weight: 600; font-size: 1.1rem;">{title}</span>
        </div>
        <div class="header-right" style="display: flex; align-items: center; gap: 20px;">
            <div class="sync-pill" onclick="window.location.reload()">Sync Feeds</div>
            <div style="width: 30px; height: 30px; background: var(--terminal-surface); border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid var(--terminal-border);">
                <i class="lucide-user" style="font-size: 0.9rem; color: var(--terminal-muted);"></i>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_bottom_nav():
    cols = st.columns(5)
    pages = ["Dashboard", "Sources", "Saved", "Alerts", "Settings"]
    icons = ["layout-grid", "globe", "bookmark", "bell", "settings"]
    
    # We use a trick: absolute positioned buttons under the visual footer
    st.markdown('<div class="bottom-nav">', unsafe_allow_html=True)
    for i, page in enumerate(pages):
        with cols[i]:
            is_active = st.session_state.current_page == page
            color = "var(--terminal-accent)" if is_active else "var(--terminal-muted)"
            if st.button(f"{page}", key=f"nav_{page}", use_container_width=True):
                set_page(page)
    st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: DASHBOARD ---
if st.session_state.current_page == "Dashboard":
    render_header("Intelligence Repository")
    df = get_data()
    
    # Filters Row (Ultra-Surgical Spacing)
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    col1, col2, col3, col_exp = st.columns([1, 1, 2, 1])
    
    with col1:
        st.markdown("<small style='color: var(--terminal-muted); font-size: 10px; margin-bottom: -5px;'>COUNTRY</small>", unsafe_allow_html=True)
        region = st.selectbox("Country", ["All"] + sorted(df["Region"].unique().tolist()) if not df.empty else ["All"], label_visibility="collapsed")
    with col2:
        st.markdown("<small style='color: var(--terminal-muted); font-size: 10px; margin-bottom: -5px;'>AREA</small>", unsafe_allow_html=True)
        topic = st.selectbox("Area", ["All"] + sorted(df["Topic"].unique().tolist()) if not df.empty else ["All"], label_visibility="collapsed")
    with col_exp:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Quick Export",
            data=csv_data,
            file_name=f"intelligence_export_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    if not df.empty:
        f_df = df.copy()
        if region != "All": f_df = f_df[f_df["Region"] == region]
        if topic != "All": f_df = f_df[f_df["Topic"] == topic]
        
        # MONOLITHIC TABLE ENGINE (Surgical Alignment & Interactive Buttons)
        st.markdown('<div class="terminal-container">', unsafe_allow_html=True)
        
        # We use a 2-column layout to keep stars functional while maintaining monolithic alignment for the rest
        col_buttons, col_table_content = st.columns([0.04, 0.96])
        
        with col_buttons:
            st.markdown("<div style='height: 35px;'></div>", unsafe_allow_html=True) # Header offset
            for i, row in f_df.iterrows():
                is_saved = row['Link'] in st.session_state.saved_links
                icon = "⭐" if is_saved else "☆"
                if st.button(icon, key=f"dash_save_{i}", help="Toggle Save"):
                    if is_saved:
                        remove_saved_article(row['Link'])
                        st.session_state.saved_links.remove(row['Link'])
                    else:
                        save_article(row)
                        st.session_state.saved_links.add(row['Link'])
                    st.rerun()

        with col_table_content:
            table_header = """<table class="terminal-table" style="table-layout: fixed; width: 100%;">
                <thead><tr>
                    <th style="width: 12%;">Firm</th>
                    <th style="width: 10%;">Country</th>
                    <th style="width: 15%;">Area</th>
                    <th style="width: 53%;">Publication</th>
                    <th style="width: 10%;">Status</th>
                </tr></thead><tbody>"""
            
            rows_html = ""
            for idx, row in f_df.iterrows():
                link = row['Link']
                status_dot = "status-new" if row['Impact'] > 82 else "status-active"
                status_txt = "New" if row['Impact'] > 82 else "Active"
                
                # Height must match Streamlit button height (approx 38px with tight padding)
                rows_html += f"""<tr class="tr-row" style="height: 38px;">
                    <td style="width: 12%;">{row['Firm']}</td>
                    <td style="width: 10%; color: var(--terminal-muted);">{row['Region']}</td>
                    <td style="width: 15%;">{row['Topic']}</td>
                    <td style="width: 53%; white-space: normal;">
                        <a href="{link}" target="_blank" style="text-decoration: none; color: inherit; font-weight: 500;">
                            {row['Headline']}
                        </a>
                    </td>
                    <td style="width: 10%;">
                        <span class="status-dot {status_dot}"></span>
                        <span style="font-weight: 500;">{status_txt}</span>
                    </td>
                </tr>"""
            
            table_footer = "</tbody></table></div>"
            full_table = (table_header + rows_html + table_footer).strip()
            st.markdown(full_table, unsafe_allow_html=True)
        
        # Functional Save Logic (Simplified for Streamlit: using a secondary button column for now or individual save buttons)
        # To make it feel interactive, we'll add a 'Save All Visible' or eventually per-row components if needed.
        # For now, let's just make the Dashboard functional.

# --- PAGE: SAVED ---
elif st.session_state.current_page == "Saved":
    render_header("Knowledge Hub (Saved)")
    saved_df = get_saved_articles()
    
    if not saved_df.empty:
        st.markdown('<div class="terminal-container">', unsafe_allow_html=True)
        st.markdown(f"""
        <table class="terminal-table">
            <thead>
                <tr>
                    <th style="width: 5%; text-align: center;"></th>
                    <th style="width: 15%;">Firm</th>
                    <th style="width: 15%;">Area</th>
                    <th style="width: 65%;">Publication</th>
                </tr>
            </thead>
            <tbody>
        """, unsafe_allow_html=True)
        
        for idx, row in saved_df.iterrows():
            link = row['link']
            row_col_save, row_col_content = st.columns([0.05, 0.95])
            
            with row_col_save:
                if st.button("🗑️", key=f"del_{idx}", help="Remove from Hub"):
                    remove_saved_article(link)
                    st.session_state.saved_links.remove(link)
                    st.rerun()

            with row_col_content:
                st.markdown(f"""
                <table class="terminal-table" style="margin-top: -45px; border: none;">
                <tr class="tr-row" style="border: none;">
                    <td style="width: 15%; border: none;">{row['firm']}</td>
                    <td style="width: 15%; border: none;">{row['topic']}</td>
                    <td style="width: 70%; border: none;">
                        <a href="{link}" target="_blank" style="text-decoration: none; color: inherit;">
                            {row['headline']}
                        </a>
                    </td>
                </tr>
                </table>
                """, unsafe_allow_html=True)
        st.markdown("</tbody></table></div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='padding: 100px; text-align: center; color: var(--terminal-muted);'>No saved research yet. Star items in the Dashboard to persist them here.</div>", unsafe_allow_html=True)

# --- PAGE: SOURCES ---
elif st.session_state.current_page == "Sources":
    render_header("Knowledge Sources")
    sources = get_sources()
    st.subheader("Add Custom Source")
    with st.form("add_source"):
        s_name = st.text_input("Source Name")
        s_domain = st.text_input("Domain (e.g., mckinsey.com)")
        s_cat = st.selectbox("Category", ["Consulting", "Finance", "Tech", "Gov"])
        if st.form_submit_button("Initialize Sync"):
            if add_source(s_name, s_domain, s_cat):
                st.success("Source linked.")
            else:
                st.error("Domain already exists.")

# --- FOOTER ---
render_bottom_nav()
