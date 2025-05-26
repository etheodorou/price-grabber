import streamlit as st
import pandas as pd

# === [00] PAGE CONFIG & GLOBAL CSS ===
st.set_page_config(page_title="Price Grabber", layout="wide")

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
.band-header { display: flex; align-items: center; gap: 8px; font-weight: 600; margin-bottom: 4px;}
.band-header div { text-align: center; }
.band-row { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 5px;}
.band-minmax { width: 74px !important; text-align:center; }
.band-margin { width: 66px !important; text-align:center; }
.band-del { font-size: 1.1em; color: #c74e4e; margin-left: 6px;}
.band-del:hover { color: #fff;background: #c74e4e77; border-radius:4px; }
.band-plus-btn { 
    background: #212926; border-radius: 50%; width: 22px; height: 22px; color: #18ea8a; 
    display: flex; align-items: center; justify-content: center;
    font-size: 1.05em; margin: 10px auto 8px auto; border: none; cursor: pointer;
    transition: background 0.2s, color 0.2s;
}
.band-plus-btn:hover { background: #18ea8a; color: #212926; }
.compact-btn button {
    padding: 0px 8px 0px 8px !important;
    min-width: 0 !important;
    height: 22px !important;
    font-size: 1.1em !important;
}
</style>
""", unsafe_allow_html=True)

# === [01] PAGE TITLE ===
st.markdown(
    '<div class="main-title-center">💸 Price Grabber: Competitor Price Scraper</div>',
    unsafe_allow_html=True
)

# === [02] SESSION STATE INIT ===
for k in ["brands_all_selected", "cat_all_selected", "reset"]:
    if k not in st.session_state:
        st.session_state[k] = False
if "fuzzy_threshold" not in st.session_state:
    st.session_state["fuzzy_threshold"] = 85

# === [03] SIDEBAR: UPLOAD & RESET ===
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">1️⃣ ERP CSV Upload</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload your ERP products CSV", type="csv")
    st.markdown('<div class="reset-btn-center">', unsafe_allow_html=True)
    reset_clicked = st.button("🔄 Reset All", key="reset_all", help="Reset all selections", type="secondary")
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

# === [04] MAIN AREA: PROMPT IF NO FILE ===
if not uploaded:
    st.markdown(
        '<div class="main-file-prompt">⬆️ Upload file to see file preview</div>',
        unsafe_allow_html=True
    )
    st.stop()

# === [05] SIDEBAR: FUZZY THRESHOLD SLIDER ===
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">2️⃣ Matching Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtle-section">', unsafe_allow_html=True)
    fuzzy_threshold = st.slider(
        "Fuzzy match threshold (%)",
        70, 100, 
        st.session_state.get("fuzzy_threshold", 85),
        key="fuzzy_threshold"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

# === [06] LOAD DATAFRAME & VALIDATE ===
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

# === [07] RESET LOGIC (Safe for Streamlit) ===
if reset_clicked:
    for key in list(st.session_state.keys()):
        if (
            key.startswith("toggle_brand_")
            or key.startswith("toggle_")
            or key.endswith("_scrape")
            or key.startswith("website_select_all_")
            or key.startswith("bands_")
            or key == "fuzzy_threshold"
        ):
            del st.session_state[key]
    st.session_state['brands_all_selected'] = False
    st.session_state['cat_all_selected'] = False
    st.rerun()

# === [08] SIDEBAR: BRANDS FILTER ===
with st.sidebar:
    st.markdown('<div class="sidebar-section-title">3️⃣ Filter Brands</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtle-section">', unsafe_allow_html=True)
    brands = sorted(df["Brand"].dropna().unique())

    brand_states = [st.session_state.get(f"toggle_brand_{brand}", False) for brand in brands]
    all_brands_checked = all(brand_states) and len(brands) > 0

    btn_txt = "Deselect All Brands" if all_brands_checked else "Select All Brands"
    if st.button(btn_txt, key="select_all_brands", help="Select or deselect all brands", type="secondary"):
        new_state = not all_brands_checked
        for brand in brands:
            st.session_state[f"toggle_brand_{brand}"] = new_state
        st.session_state["brands_all_selected"] = new_state
        st.rerun()

    for brand in brands:
        checked = st.checkbox(
            label=f":gray[{brand}]",
            value=st.session_state.get(f"toggle_brand_{brand}", False),
            key=f"toggle_brand_{brand}"
        )

    # --- After rendering, update all_brands_selected
    current_states = [st.session_state.get(f"toggle_brand_{brand}", False) for brand in brands]
    st.session_state["brands_all_selected"] = all(current_states) and len(brands) > 0

    enabled_brands = {b for b in brands if st.session_state.get(f"toggle_brand_{b}", False)}
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

# === [09] CATEGORIES & PRICE BAND LOGIC ===
categories = (
    df[df["Brand"].isin(enabled_brands)]["Category"].dropna().unique().tolist()
)

# --- Always initialize all toggle keys up front for every category & site ---
all_websites = ["PN", "TTP", "TW", "ET", "TP", "TPR"]
for cat in categories:
    if f"toggle_{cat}" not in st.session_state:
        st.session_state[f"toggle_{cat}"] = False
    for site in all_websites:
        if f"{cat}_{site}_scrape" not in st.session_state:
            st.session_state[f"{cat}_{site}_scrape"] = False
    if f"website_select_all_{cat}" not in st.session_state:
        st.session_state[f"website_select_all_{cat}"] = False

with st.sidebar:
    st.markdown('<div class="sidebar-section-title">4️⃣ Category Scrape & Pricing</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-subtle-section">', unsafe_allow_html=True)
    # Categories "select all/deselect all"
    category_states = [st.session_state.get(f"toggle_{cat}", False) for cat in categories]
    all_categories_checked = all(category_states) and len(categories) > 0
    btn_txt = "Deselect All Categories" if all_categories_checked else "Select All Categories"
    if st.button(btn_txt, key="select_all_categories", help="Select or deselect all categories", type="secondary"):
        new_state = not all_categories_checked
        for cat in categories:
            st.session_state[f"toggle_{cat}"] = new_state
        st.session_state["cat_all_selected"] = new_state
        st.rerun()

    strategy_options = [
        "None",
        "Match cheapest competitor",
        "Undercut cheapest by %",
        "Fixed margin above cost"
    ]

    # IMPORTANT: do NOT reorder categories, just iterate in original list order!
    cat_blocks = []
    for cat in categories:
        state = st.session_state.get(f"toggle_{cat}", False)
        cat_blocks.append((state, cat))
    # Don't sort cat_blocks at all! This is the fix.

    active_cats = [cat for enabled, cat in cat_blocks if enabled]
    inactive_cats = [cat for enabled, cat in cat_blocks if not enabled]
    cat_options = {}
    selected_sites = {}

    # Optionally: separator logic for inactive cats
    first_inactive_idx = None
    for i, (enabled, _) in enumerate(cat_blocks):
        if not enabled:
            first_inactive_idx = i
            break

    for i, (enabled, cat) in enumerate(cat_blocks):
        if i == first_inactive_idx:
            st.markdown('<hr style="border:none;border-top:2px solid #444;margin:1em 0;">', unsafe_allow_html=True)
            st.markdown('<div style="color:#bbb;font-size:1.05em;font-weight:600;text-align:center;margin-bottom:0.15em;margin-top:0.15em;">Inactive categories</div>', unsafe_allow_html=True)

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
            # --- FLEXIBLE PRICE BANDS UI (compact, centered, aligned) ---
            cat_df = df[df["Category"] == cat]
            if not cat_df.empty and "Retail" in cat_df.columns:
                cat_min = float(cat_df["Retail"].min())
                cat_max = float(cat_df["Retail"].max())
            else:
                cat_min = 0.0
                cat_max = 999999.0

            st.markdown("""
            <style>
            .band-header, .band-row { 
                display: flex; align-items: center; gap: 7px; 
            }
            .band-header { font-weight: 600; margin-bottom: 3px; }
            .band-row { 
                margin-bottom: 2px; 
                background: #202127; 
                border-radius: 6px; 
                padding: 3px 3px 1px 7px; 
                min-height: 38px;
            }
            .band-min, .band-max, .band-margin {
                width: 70px !important; 
                max-width: 75px;
                text-align: center;
            }
            .band-strategy {
                min-width: 110px; max-width: 120px; text-align: center;
            }
            .band-del {
                width: 29px; min-width: 29px; display: flex; align-items: center; justify-content: center;
            }
            .band-plus-center {
                width:100%; display: flex; justify-content: center; align-items: center; margin-top:14px;
            }
            .band-input input, .band-input select {
                font-size: 0.93em !important;
                padding: 2px 5px !important;
                height: 30px !important;
                min-width: 48px;
                max-width: 85px;
            }
            </style>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class="band-header">
                <div class="band-min">Min</div>
                <div class="band-max">Max</div>
                <div class="band-strategy">Strategy</div>
                <div class="band-margin">Margin</div>
                <div class="band-del"></div>
            </div>
            """, unsafe_allow_html=True)

            bands_key = f"bands_{cat}"
            if bands_key not in st.session_state:
                st.session_state[bands_key] = [
                    {'min': cat_min, 'max': cat_max, 'strategy': strategy_options[0], 'margin': 20.0}
                ]
            bands = st.session_state[bands_key]

            to_delete = None
            for idx, band in enumerate(bands):
                col1, col2, col3, col4, col5 = st.columns([0.91, 0.91, 1.25, 0.81, 0.4], gap="small")
                with col1:
                    band['min'] = st.number_input(
                        "", value=float(band['min']), min_value=cat_min, max_value=cat_max, step=10.0,
                        key=f"{bands_key}_min_{idx}", label_visibility="collapsed"
                    )
                with col2:
                    band['max'] = st.number_input(
                        "", value=float(band['max']), min_value=band['min'], max_value=cat_max, step=10.0,
                        key=f"{bands_key}_max_{idx}", label_visibility="collapsed"
                    )
                with col3:
                    band['strategy'] = st.selectbox(
                        "", strategy_options,
                        index=strategy_options.index(band['strategy']) if band['strategy'] in strategy_options else 0,
                        key=f"{bands_key}_strategy_{idx}", label_visibility="collapsed"
                    )
                with col4:
                    band['margin'] = st.number_input(
                        "", value=float(band['margin']), min_value=0.0, max_value=100.0, step=0.5,
                        key=f"{bands_key}_margin_{idx}", label_visibility="collapsed"
                    )
                with col5:
                    if st.button("🗑️", key=f"{bands_key}_del_{idx}"):
                        to_delete = idx

            if to_delete is not None:
                st.session_state[bands_key].pop(to_delete)
                st.rerun()

            # --- Centered add band button (no container above, margin-top for space) ---
            st.markdown('<div class="band-plus-center">', unsafe_allow_html=True)
            if st.button("➕", key=f"{bands_key}_add", help="Add Band", use_container_width=False):
                st.session_state[bands_key].append({'min': cat_min, 'max': cat_max, 'strategy': strategy_options[0], 'margin': 20.0})
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # === [11] WEBSITES & CATEGORY LOGIC (CONTINUES) ===
            st.markdown("<div class='website-label'>Websites to scrape:</div>", unsafe_allow_html=True)

            store_name_map = {
                "PN": "Padel Nuestro",
                "TTP": "Total Padel",
                "TW": "Tennis Warehouse",
                "ET": "e-tennis",
                "TP": "Tennis-Point",
                "TPR": "Tennispro"
            }

            website_states = [st.session_state.get(f"{cat}_{site}_scrape", False) for site in all_websites]
            all_checked = all(website_states) and len(all_websites) > 0

            btn_txt = f"Deselect All Websites ({cat})" if all_checked else f"Select All Websites ({cat})"
            if st.button(btn_txt, key=f"select_all_websites_{cat}", type="secondary"):
                new_state = not all_checked
                for site in all_websites:
                    st.session_state[f"{cat}_{site}_scrape"] = new_state
                st.session_state[f"website_select_all_{cat}"] = new_state
                st.rerun()

            # Vertical checkboxes with abbreviation and tooltip
            cat_selected_sites = []
            for site in all_websites:
                checked = st.checkbox(
                    label=f":gray[{site}]",
                    value=st.session_state.get(f"{cat}_{site}_scrape", False),
                    key=f"{cat}_{site}_scrape",
                    help=store_name_map[site]
                )
                if checked:
                    cat_selected_sites.append(site)

            # Update "select all websites" state variable for live button label
            if all(st.session_state.get(f"{cat}_{site}_scrape", False) for site in all_websites):
                st.session_state[f"website_select_all_{cat}"] = True
            else:
                st.session_state[f"website_select_all_{cat}"] = False

            selected_sites[cat] = cat_selected_sites
            cat_options[cat] = {
                "scrape": True,
                "bands": st.session_state[bands_key],  # <- store bands here!
            }
        else:
            cat_options[cat] = {
                "scrape": False,
                "bands": [],
            }
            selected_sites[cat] = []
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

    # === [12] READY TO RUN BUTTON ===
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

# === [13] MAIN CONTENT: DATA PREVIEW & MODAL ===
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
