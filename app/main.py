import streamlit as st
import pandas as pd

# === [00] PAGE CONFIG & GLOBAL CSS ===

all_websites = ["PN", "TTP", "TW", "ET", "TP", "TPR"]

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
.compact-btn button {
    padding: 0px 8px 0px 8px !important;
    min-width: 0 !important;
    height: 22px !important;
    font-size: 1.1em !important;
}
.center-button {
    display: flex !important;
    justify-content: center !important;
    width: 100%;
    margin: 1em 0;
}
.center-button button {
    margin: 0 auto;
}
.website-label {
    margin: 1em 0 0.5em 0;
    font-weight: 500;
    color: #e0e0e0;
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
if "enabled_categories" not in st.session_state:
    st.session_state["enabled_categories"] = []

# === [03] SIDEBAR: UPLOAD & RESET ===
with st.sidebar:
    st.markdown('<div class="sidebar-section-title" style="text-align:center;">1️⃣ ERP CSV Upload</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="sidebar-section-title" style="text-align:center;">2️⃣ Matching Settings</div>', unsafe_allow_html=True)
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
            st.session_state.pop(key, None)
    st.session_state['brands_all_selected'] = False
    st.session_state['cat_all_selected'] = False
    if "selected_websites_by_cat" in st.session_state:
        st.session_state["selected_websites_by_cat"] = {}
    for key in list(st.session_state.keys()):
        if key.startswith("bands_"):
            st.session_state.pop(key)
    st.rerun()

# === [08] SIDEBAR: BRANDS FILTER ===
with st.sidebar:
    st.markdown('<div class="sidebar-section-title" style="text-align:center;margin-bottom:1.2em;">3️⃣ Filter Brands</div>', unsafe_allow_html=True)
    brands = sorted(df["Brand"].dropna().unique())

    brand_states = [st.session_state.get(f"toggle_brand_{brand}", False) for brand in brands]
    all_brands_checked = all(brand_states) and len(brands) > 0

    st.markdown('<div class="center-button">', unsafe_allow_html=True)
    btn_txt = "Deselect All Brands" if all_brands_checked else "Select All Brands"
    if st.button(btn_txt, key="select_all_brands", help="Select or deselect all brands", type="secondary"):
        new_state = not all_brands_checked
        for brand in brands:
            st.session_state[f"toggle_brand_{brand}"] = new_state
        st.session_state["brands_all_selected"] = new_state
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    for brand in brands:
        checked = st.checkbox(
            label=f":gray[{brand}]",
            value=st.session_state.get(f"toggle_brand_{brand}", False),
            key=f"toggle_brand_{brand}"
        )

    current_states = [st.session_state.get(f"toggle_brand_{brand}", False) for brand in brands]
    st.session_state["brands_all_selected"] = all(current_states) and len(brands) > 0

    enabled_brands = {b for b in brands if st.session_state.get(f"toggle_brand_{b}", False)}
    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

# === [09] CATEGORIES & PRICE BAND LOGIC ===
categories = (
    df[df["Brand"].isin(enabled_brands)]["Category"].dropna().unique().tolist()
)

for cat in categories:
    if f"toggle_{cat}" not in st.session_state:
        st.session_state[f"toggle_{cat}"] = cat in st.session_state["enabled_categories"]
    for site in all_websites:
        if f"{cat}_{site}_scrape" not in st.session_state:
            st.session_state[f"{cat}_{site}_scrape"] = False
    if f"website_select_all_{cat}" not in st.session_state:
        st.session_state[f"website_select_all_{cat}"] = False

with st.sidebar:
    st.markdown('<div class="sidebar-section-title" style="text-align:center;margin-bottom:1.2em;">4️⃣ Category Scrape & Pricing</div>', unsafe_allow_html=True)
    st.markdown('<div class="center-button">', unsafe_allow_html=True)
    category_states = [st.session_state.get(f"toggle_{cat}", False) for cat in categories]
    all_categories_checked = all(category_states) and len(categories) > 0
    btn_txt = "Deselect All Categories" if all_categories_checked else "Select All Categories"
    if st.button(btn_txt, key="select_all_categories", help="Select or deselect all categories", type="secondary", use_container_width=False):
        new_state = not all_categories_checked
        if new_state:
            st.session_state["enabled_categories"] = categories.copy()
            for cat in categories:
                st.session_state[f"toggle_{cat}"] = True
        else:
            st.session_state["enabled_categories"] = []
            for cat in categories:
                st.session_state[f"toggle_{cat}"] = False
        st.session_state["cat_all_selected"] = new_state
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    strategy_options = [
        "None",
        "Match cheapest competitor",
        "Undercut cheapest by %",
        "Fixed margin above cost"
    ]

    cat_blocks = []
    for cat in categories:
        state = st.session_state.get(f"toggle_{cat}", False)
        cat_blocks.append((state, cat))

    first_inactive_idx = None
    for i, (enabled, _) in enumerate(cat_blocks):
        if not enabled:
            first_inactive_idx = i
            break

    for i, (enabled, cat) in enumerate(cat_blocks):
        if i == first_inactive_idx:
            st.markdown('<hr style="border:none;border-top:2px solid #444;margin:1em 0;">', unsafe_allow_html=True)

        with st.container():
            col1, col2 = st.columns([0.12, 0.88])
            with col1:
                toggled = st.toggle(
                    label=cat,
                    value=cat in st.session_state["enabled_categories"],
                    key=f"toggle_{cat}",
                    help="Enable/disable this category",
                    label_visibility="collapsed",
                )
            with col2:
                st.markdown(
                    f'<div style="text-align:left;padding-left:0.5em;"><span style="font-size:1.18em;font-weight:700;color:#18ea8a;">{cat}</span></div>',
                    unsafe_allow_html=True,
                )

            toggled_in_enabled = cat in st.session_state["enabled_categories"]
            if toggled != toggled_in_enabled:
                if toggled:
                    st.session_state["enabled_categories"].append(cat)
                else:
                    st.session_state["enabled_categories"].remove(cat)
                st.rerun()

            if toggled:
                cat_df = df[df["Category"] == cat]
                if not cat_df.empty and "Retail" in cat_df.columns:
                    cat_min = float(cat_df["Retail"].min())
                    cat_max = float(cat_df["Retail"].max())
                else:
                    cat_min = 0.0
                    cat_max = 999999.0

                col1, col2, col3, col4, col5 = st.columns([0.91, 0.91, 1.25, 0.81, 0.4], gap="small")
                with col1:
                    st.markdown("**Min**")
                with col2:
                    st.markdown("**Max**")
                with col3:
                    st.markdown("**Strategy**")
                with col4:
                    st.markdown("**Margin**")
                with col5:
                    st.markdown("")

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
                            label="Min",
                            value=float(band['min']), min_value=cat_min, max_value=cat_max, step=10.0,
                            key=f"{bands_key}_min_{idx}", label_visibility="collapsed"
                        )
                    with col2:
                        band['max'] = st.number_input(
                            label="Max",
                            value=float(band['max']), min_value=band['min'], max_value=cat_max, step=10.0,
                            key=f"{bands_key}_max_{idx}", label_visibility="collapsed"
                        )
                    with col3:
                        band['strategy'] = st.selectbox(
                            label="Strategy",
                            options=strategy_options,
                            index=strategy_options.index(band['strategy']) if band['strategy'] in strategy_options else 0,
                            key=f"{bands_key}_strategy_{idx}", label_visibility="collapsed"
                        )
                    with col4:
                        band['margin'] = st.number_input(
                            label="Margin",
                            value=float(band['margin']), min_value=0.0, max_value=100.0, step=0.5,
                            key=f"{bands_key}_margin_{idx}", label_visibility="collapsed"
                        )
                    with col5:
                        if st.button("🗑️", key=f"{bands_key}_del_{idx}"):
                            to_delete = idx

                if to_delete is not None:
                    st.session_state[bands_key].pop(to_delete)
                    st.rerun()

                st.markdown('<div style="display:flex;justify-content:center;margin-top:0.5em;">', unsafe_allow_html=True)
                if st.button("➕", key=f"{bands_key}_add", help="Add Band", use_container_width=False):
                    st.session_state[bands_key].append({'min': cat_min, 'max': cat_max, 'strategy': strategy_options[0], 'margin': 20.0})
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("<div class='website-label'>Websites to scrape:</div>", unsafe_allow_html=True)
                store_name_map = {
                    "PN": "Padel Nuestro",
                    "TTP": "Total Padel",
                    "TW": "Tennis Warehouse",
                    "ET": "e-tennis",
                    "TP": "Tennis-Point",
                    "TPR": "Tennispro"
                }
                if "selected_websites_by_cat" not in st.session_state:
                    st.session_state["selected_websites_by_cat"] = {}
                if cat not in st.session_state["selected_websites_by_cat"]:
                    st.session_state["selected_websites_by_cat"][cat] = []

                cat_selected_sites = []
                for site in all_websites:
                    checked = site in st.session_state["selected_websites_by_cat"][cat]
                    cb = st.checkbox(
                        label=f":gray[{site}]",
                        value=checked,
                        key=f"website_{cat}_{site}_scrape",
                        help=store_name_map[site]
                    )
                    if cb and site not in st.session_state["selected_websites_by_cat"][cat]:
                        st.session_state["selected_websites_by_cat"][cat].append(site)
                    elif not cb and site in st.session_state["selected_websites_by_cat"][cat]:
                        st.session_state["selected_websites_by_cat"][cat].remove(site)
                    if cb:
                        cat_selected_sites.append(site)

                all_checked = len(st.session_state["selected_websites_by_cat"][cat]) == len(all_websites)
                btn_txt = f"{'Deselect' if all_checked else 'Select'} All Websites"
                st.markdown('<div class="center-button">', unsafe_allow_html=True)
                if st.button(btn_txt, key=f"select_all_websites_{cat}"):
                    if all_checked:
                        st.session_state["selected_websites_by_cat"][cat] = []
                    else:
                        st.session_state["selected_websites_by_cat"][cat] = all_websites.copy()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                # Separator between active categories
                active_indices = [idx for idx, (is_enabled, _) in enumerate(cat_blocks) if is_enabled]
                if i in active_indices and active_indices.index(i) < len(active_indices) - 1:
                    st.markdown('<div class="sidebar-section-div"></div>', unsafe_allow_html=True)

    st.markdown('<div class="center-button">', unsafe_allow_html=True)
    requirements_met = (
        len(enabled_brands) > 0
        and len([cat for cat in categories if cat in st.session_state["enabled_categories"]]) > 0
        and any(len(st.session_state["selected_websites_by_cat"].get(cat, [])) > 0 for cat in st.session_state["enabled_categories"])
    )
    if st.button("🚀 Start Scraping", disabled=not requirements_met, use_container_width=False):
        st.success("Scraping started!")
    st.markdown('</div>', unsafe_allow_html=True)

# === [MAIN AREA: DATA PREVIEW] ===

st.subheader("Preview of your data (translated)")
st.dataframe(df, use_container_width=True)