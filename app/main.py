import streamlit as st
import pandas as pd

st.set_page_config(page_title="Price Grabber", layout="wide")
st.title("💸 Price Grabber: Competitor Price Scraper")

# --- CSS for tight vertical spacing and perfectly centered Run Scraper button/text ---
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] button[kind="secondary"] {
        display: block;
        margin-left: auto;
        margin-right: auto;
        left: 0;
        right: 0;
        width: 20%;
        min-width: 140px;
        max-width: 260px;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] {
        display: flex;
        justify-content: center !important;
        align-items: center !important;
        width: 100%;
        margin-left: 0 !important;
        margin-right: 0 !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }
    /* Make sidebar slider label bigger and bolder */
    section[data-testid="stSidebar"] div[data-testid="stSliderLabel"] {
        font-size: 1.28em !important;
        font-weight: 700 !important;
        color: #fff !important;
        letter-spacing: 0.01em;
        margin-bottom: 0.25em !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



fuzzy_threshold = st.sidebar.slider("Fuzzy match threshold (%)", 70, 100, 85)

# --- Perfectly centered Run Scraper button ---
with st.sidebar:
    st.markdown('<div class="centered-btn-container">', unsafe_allow_html=True)
    run_btn = st.sidebar.button("Run Scraper")

    st.markdown('</div>', unsafe_allow_html=True)

uploaded = st.file_uploader("Upload your ERP products CSV", type="csv")
if not uploaded:
    st.info("Please upload a CSV file to begin.")
    st.stop()

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

st.subheader("Preview of your data (translated)")
st.dataframe(df, use_container_width=True)

categories = df["Category"].dropna().unique().tolist()

st.sidebar.subheader("Category Scrape & Pricing Options")
cat_options = {}
strategy_options = [
    "None",
    "Match cheapest competitor",
    "Undercut cheapest by %",
    "Fixed margin above cost"
]

for idx, cat in enumerate(categories):
    scrape = st.sidebar.toggle(
        label=f"{cat}",
        value=True,
        key=f"toggle_{cat}",
        help="Include/exclude this category"
    )
    if scrape:
        col1, col2 = st.sidebar.columns(2, gap="small")
        with col1:
            strategy = st.selectbox(
                "Strategy",
                options=strategy_options,
                key=f"strategy_{cat}"
            )
        with col2:
            min_margin = st.number_input(
                "Min Margin %",
                min_value=0.0, max_value=100.0, value=20.0, step=0.5,
                key=f"margin_{cat}"
            )
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

if run_btn:
    st.success("Ready to run with these parameters:")
    st.write("Category settings:", cat_options)
    st.write(f"Fuzzy match threshold: {fuzzy_threshold}")
