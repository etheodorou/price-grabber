import streamlit as st
import pandas as pd

st.set_page_config(page_title="Price Grabber", layout="wide")

# --- CSS for centering, buttons, sections, etc ---
st.markdown("""
    <style>
    .main-title-center {
        text-align: center !important;
        font-size: 2.5em !important;
        font-weight: 700;
        margin-top: 0.6em;
        margin-bottom: 0.3em;
        color: white;
    }
    .sidebar-section-title {
        font-size: 1.17em;
        font-weight: 700;
        margin: 1.3em 0 0.5em 0;
        padding-top: 0.6em;
        color: #f0f0f0;
        letter-spacing: 0.01em;
    }
    .sidebar-section-div {
        border-bottom: 2px solid #333;
        margin: 1.3em 0 1.0em 0;
    }
    .sidebar-subtle-section {
        background: #232429cc;
        padding: 0.75em 1em 1em 1em;
        border-radius: 10px;
        margin-bottom: 1.2em;
        margin-top: 0.2em;
    }
    .reset-btn-center {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0.5em 0 0.8em 0;
        width: 100%;
    }
    .main-file-prompt {
        text-align: center;
        font-size: 1.35em;
        margin-top: 2.7em;
        color: #d4d4d4;
    }
    </style>
""", unsafe_allow_html=True)

# --- Main Centered Title ---
st.markdown(
    '<div class="main-title-center">💸 Price Grabber: Competitor Price Scraper</div>',
    unsafe_allow_html=True
)

# --- Session State Init ---
for k in ["brands_all_selected", "cat_all_selected", "reset"]:
    if k not in st.session_state:
        st.session_state[k] = False

# --- SIDEBAR LAYOUT ---
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">1️⃣ ERP CSV Upload</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload your ERP products CSV", type="csv")
    
    # --- Move Reset All button here, with visual separation ---
    st.markdown('<div class="reset-btn-center">', unsafe_allow_html=True)
    reset_clicked = st.button("🔄 Reset All", key="reset_all", help="Reset all selections", type="secondary")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

# --- Main area: show prompt until file is uploaded ---
if not uploaded:
    st.markdown(
        '<div class="main-file-prompt">⬆️ Upload file to see file preview</div>',
        unsafe_allow_html=True
    )
    st.stop()

# --- Fuzzy slider appears ONLY after upload ---
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">2️⃣ Matching Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtle-section">', unsafe_allow_html=True)
    fuzzy_threshold = st.slider("Fuzzy match threshold (%)", 70, 100, 85)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

# --- Dataframe Loading/Validation ---
column_map = {
    "Κατασκευαστής": "Brand",
    "Κωδικός Κατασκευαστή": "Sku",
    "Κατηγορία": "Category",
    "Περιγραφή": "Name",
    "Κόστος": "Cost",
    "Λιανική": "Retail",
    "Εκπτωση": "Disc",
    "Τελική": "Final",
    "No Vat": "No Vat",
    "Μεικτό": "Margin"
}

df = pd.read_csv(uploaded)
missing_cols = [col for col in column_map.keys() if col not in df.columns]
if missing_cols:
    st.error(f"One or more expected columns are missing from your CSV! Missing: {missing_cols}")
    st.write("Expected columns:", list(column_map.keys()))
    st.stop()
df = df.rename(columns=column_map)

# --- Reset logic ---
if reset_clicked:
    for key in list(st.session_state.keys()):
        if key.startswith("toggle_brand_") or key.startswith("toggle_") or key.endswith("_scrape") or key.startswith("website_select_all_"):
            del st.session_state[key]
    st.session_state['brands_all_selected'] = False
    st.session_state['cat_all_selected'] = False
    st.experimental_rerun()

# --- Brands Section ---
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">3️⃣ Filter Brands</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtle-section">', unsafe_allow_html=True)
    brands = sorted(df["Brand"].dropna().unique())
    all_on = st.session_state["brands_all_selected"]
    btn_txt = "Select All Brands" if not all_on else "Deselect All Brands"
    if st.button(btn_txt, key="select_all_brands", help="Select or deselect all brands", type="secondary"):
        st.session_state["brands_all_selected"] = not st.session_state["brands_all_selected"]
        for brand in brands:
            st.session_state[f"toggle_brand_{brand}"] = st.session_state["brands_all_selected"]
    brand_states = {}
    for i, brand in enumerate(brands):
        state = st.session_state.get(f"toggle_brand_{brand}", False)
        brand_states[brand] = st.checkbox(
            label=brand, value=state, key=f"toggle_brand_{brand}"
        )
    enabled_brands = {b for b, v in brand_states.items() if v}
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

# --- Categories Section ---
categories = (
    df[df["Brand"].isin(enabled_brands)]["Category"].dropna().unique().tolist()
)
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">4️⃣ Category Scrape & Pricing</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtle-section">', unsafe_allow_html=True)
    if categories:
        btn_txt = "Select All Categories" if not st.session_state["cat_all_selected"] else "Deselect All Categories"
        if st.button(btn_txt, key="select_all_categories", help="Select or deselect all categories", type="secondary"):
            st.session_state["cat_all_selected"] = not st.session_state["cat_all_selected"]
            for cat in categories:
                st.session_state[f"toggle_{cat}"] = st.session_state["cat_all_selected"]
    all_websites = ["PN", "TTP", "TW", "ET", "TP", "TPR"]
    strategy_options = [
        "None",
        "Match cheapest competitor",
        "Undercut cheapest by %",
        "Fixed margin above cost"
    ]
    # --- Organize categories: enabled on top ---
    cat_blocks = []
    for cat in categories:
        state = st.session_state.get(f"toggle_{cat}", False)
        cat_blocks.append((state, cat))
    cat_blocks = sorted(cat_blocks, key=lambda x: not x[0])  # enabled first
    active_cats = [cat for enabled, cat in cat_blocks if enabled]
    inactive_cats = [cat for enabled, cat in cat_blocks if not enabled]
    cat_options = {}
    selected_sites = {}
    for i, cat in enumerate(active_cats + inactive_cats):
        enabled = st.session_state.get(f"toggle_{cat}", False)
        toggle_row = st.columns([0.13, 0.87])
        with toggle_row[0]:
            st.toggle(
                label="",
                value=enabled,
                key=f"toggle_{cat}",
                help="Include/exclude this category"
            )
        with toggle_row[1]:
            st.markdown(f"**{cat}**")
        if enabled:
            strategy = st.selectbox(
                "Strategy",
                options=strategy_options,
                key=f"strategy_{cat}"
            )
            min_margin = st.number_input(
                "Min Margin %",
                min_value=0.0, max_value=100.0, value=20.0, step=0.5,
                key=f"margin_{cat}"
            )
            st.markdown("<div class='website-label'>Websites to scrape:</div>", unsafe_allow_html=True)
            if st.button(
                f"Select All Websites ({cat})" if not st.session_state.get(f"website_select_all_{cat}", False) else f"Deselect All Websites ({cat})",
                key=f"select_all_websites_{cat}", type="secondary"
            ):
                st.session_state[f"website_select_all_{cat}"] = not st.session_state.get(f"website_select_all_{cat}", False)
                for site in all_websites:
                    st.session_state[f"{cat}_{site}_scrape"] = st.session_state[f"website_select_all_{cat}"]
            cat_selected_sites = []
            for site in all_websites:
                s = st.session_state.get(f"{cat}_{site}_scrape", False)
                checked = st.checkbox(
                    label=site, value=s, key=f"{cat}_{site}_scrape"
                )
                if checked:
                    cat_selected_sites.append(site)
            selected_sites[cat] = cat_selected_sites
            cat_options[cat] = {
                "scrape": True,
                "strategy": strategy,
                "min_margin": min_margin
            }
        else:
            cat_options[cat] = {
                "scrape": False,
                "strategy": None,
                "min_margin": None
            }
            selected_sites[cat] = []
        if enabled and i < len(active_cats) - 1:
            st.markdown('<hr style="border:none;border-top:1.7px solid #888;margin:0.7em 0 0.15em 0;">', unsafe_allow_html=True)
        elif not enabled and i == len(active_cats) - 1 and inactive_cats:
            st.markdown('<hr style="border:none;border-top:4px solid #444;margin:1.1em 0 0.5em 0;">', unsafe_allow_html=True)
            st.markdown('<div style="color:#bbb;font-size:1.05em;font-weight:600;text-align:center;margin-bottom:0.15em;margin-top:0.15em;">Inactive categories</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

    # --- READY TO RUN BUTTON ---
    requirements_met = (
        len(enabled_brands) > 0
        and len(active_cats) > 0
        and any(len(selected_sites[cat]) > 0 for cat in active_cats)
    )
    st.markdown('<div style="display:flex;justify-content:center;align-items:center;width:100%;margin-bottom:0.4em;">', unsafe_allow_html=True)
    ready_btn = st.button(
        "🚀 Ready to Run", key="ready_to_run", disabled=not requirements_met, type="secondary"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# --- Main Content ---
st.subheader("Preview of your data (translated)")
st.dataframe(df, use_container_width=True)

if 'ready_btn' in locals() and ready_btn and requirements_met:
    with st.modal("Confirmation"):
        n_cats = len(active_cats)
        n_brands = len(enabled_brands)
        unique_sites = set()
        for cat in active_cats:
            unique_sites.update(selected_sites[cat])
        n_sites = len(unique_sites)
        st.write(
            f"You are about to run the price scraper for **{n_cats} category(ies)**, "
            f"**{n_brands} brand(s)**, and **{n_sites} website(s)**.\n\n"
            "Are you sure you want to proceed?"
        )
        if st.button("Yes, proceed!", key="confirm_run"):
            st.success("Running scraper...")
        if st.button("Cancel", key="cancel_run"):
            st.info("Action canceled.")
