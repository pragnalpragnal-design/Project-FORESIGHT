"""
Project FORESIGHT — shared utilities
-------------------------------------
Central place for:
  - file paths
  - column-name mapping (EDIT THIS to match your real dataset)
  - cached data / model / encoder loaders
  - filter helpers
  - KPI calculations
  - shared CSS / styling helpers

Every page (app.py + pages/*.py) imports from this file so there is
ONE place to fix column names or paths if your dataset differs.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

# =========================================================
# 1. FILE PATHS
# Anchored to this file's own location (not the current working
# directory), so it works no matter where `streamlit run` is
# launched from. Adjust the sub-paths below if your folders differ.
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "processed" / "final_features_dataset.csv"
MODEL_PATH = BASE_DIR / "models" / "demand_forecasting_model.pkl"
SKU_ENCODER_PATH = BASE_DIR / "models" / "sku_encoder.pkl"
INVENTORY_ENCODER_PATH = BASE_DIR / "models" / "inventory_encoder.pkl"

# =========================================================
# 2. COLUMN NAME MAPPING  ->  EDIT THESE if your CSV uses
#    different column names. Every function below reads
#    columns through this dict, never hardcoded strings,
#    so renaming here is enough to re-point the whole app.
# =========================================================
COL = {
    "date": "date",
    "sku": "sku_id",                    # raw label, e.g. FOODS_1_001_CA_1
    "sku_encoded": "sku_encoded",       # not in raw CSV; built on-the-fly via sku_encoder at predict time
    "demand": "units_sold",             # target
    "promotion": "promo_flag",          # 0/1
    "opening_stock": "opening_stock",
    "closing_stock": "closing_stock",
    "inventory_status": "inventory_status",         # raw label e.g. Healthy / Low Stock
    "inventory_status_encoded": "inventory_status_encoded",  # not in raw CSV; built on-the-fly at predict time
    "holiday": "is_holiday",            # 0/1
    "month": "month",
    "day_of_week": "day_of_week",
    "lag_1": "lag_1",
    "lag_7": "lag_7",
    "lag_30": "lag_30",
    "rolling_mean_7": "rolling_mean_7",
    "rolling_mean_30": "rolling_mean_30",
}

# Feature order expected by the trained model — this MUST exactly match
# model.feature_names_in_ (both names and order). Confirmed from the
# training error: the model was trained on a dataframe where sku_id and
# inventory_status were label-encoded IN PLACE (same column names, values
# replaced with the encoded integers) rather than renamed to *_encoded.
MODEL_FEATURES = [
    "sku_id",
    "promo_flag",
    "day_of_week",
    "month",
    "is_holiday",
    "opening_stock",
    "closing_stock",
    "inventory_status",
    "lag_1",
    "lag_7",
    "lag_30",
    "rolling_mean_7",
    "rolling_mean_30",
]

# =========================================================
# 3. THEME / COLOR PALETTE
# =========================================================
COLOR_BLUE = "#2563EB"
COLOR_GREEN = "#22C55E"
COLOR_ORANGE = "#F59E0B"
COLOR_RED = "#EF4444"
COLOR_BG = "#F8FAFC"
COLOR_SIDEBAR = "#111827"

PLOTLY_TEMPLATE = "plotly_white"


# =========================================================
# 4. CACHED LOADERS  (all fail gracefully -> return None + message)
# =========================================================
@st.cache_data(show_spinner=False)
def load_data(path: Path = DATA_PATH) -> pd.DataFrame | None:
    """Load the feature dataset. Returns None if the file is missing/broken."""
    if not Path(path).exists():
        return None
    try:
        df = pd.read_csv(path)
    except Exception:
        return None

    # Parse date column if present
    if COL["date"] in df.columns:
        df[COL["date"]] = pd.to_datetime(df[COL["date"]], errors="coerce")

    return df


@st.cache_resource(show_spinner=False)
def load_model(path: Path = MODEL_PATH):
    """Load the trained Random Forest model. Returns None if missing/broken."""
    if not Path(path).exists():
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


@st.cache_resource(show_spinner=False)
def load_encoders(sku_path: Path = SKU_ENCODER_PATH, inv_path: Path = INVENTORY_ENCODER_PATH):
    """Load the saved LabelEncoders. Returns (sku_encoder, inventory_encoder), either may be None."""
    sku_enc = None
    inv_enc = None
    try:
        if Path(sku_path).exists():
            sku_enc = joblib.load(sku_path)
    except Exception:
        sku_enc = None
    try:
        if Path(inv_path).exists():
            inv_enc = joblib.load(inv_path)
    except Exception:
        inv_enc = None
    return sku_enc, inv_enc


def safe_encode(encoder, value):
    """
    Encode a single value with a LabelEncoder, handling unseen labels gracefully.
    Returns (encoded_value_or_None, ok_flag, message).
    """
    if encoder is None:
        return None, False, "Encoder not available."
    try:
        encoded = encoder.transform([value])[0]
        return int(encoded), True, ""
    except ValueError:
        return None, False, f"'{value}' was not seen during training (unknown category)."
    except Exception as e:
        return None, False, f"Encoding error: {e}"


# =========================================================
# 5. FILTER HELPERS
# =========================================================
def get_filter_options(df: pd.DataFrame) -> dict:
    """Build option lists for sidebar filters from the loaded dataframe."""
    options = {"months": [], "skus": [], "inventory_status": [], "promotion": []}
    if df is None:
        return options

    if COL["month"] in df.columns:
        options["months"] = sorted(df[COL["month"]].dropna().unique().tolist())
    elif COL["date"] in df.columns:
        options["months"] = sorted(df[COL["date"]].dt.to_period("M").astype(str).dropna().unique().tolist())

    if COL["sku"] in df.columns:
        options["skus"] = sorted(df[COL["sku"]].dropna().unique().tolist())

    if COL["inventory_status"] in df.columns:
        options["inventory_status"] = sorted(df[COL["inventory_status"]].dropna().unique().tolist())

    if COL["promotion"] in df.columns:
        options["promotion"] = sorted(df[COL["promotion"]].dropna().unique().tolist())

    return options


def apply_filters(
    df: pd.DataFrame,
    months=None,
    skus=None,
    inventory_status=None,
    promotion=None,
) -> pd.DataFrame:
    """Apply the global sidebar filters to a copy of the dataframe."""
    if df is None:
        return df

    filtered = df.copy()

    if months:
        if COL["month"] in filtered.columns:
            filtered = filtered[filtered[COL["month"]].isin(months)]
        elif COL["date"] in filtered.columns:
            month_strs = filtered[COL["date"]].dt.to_period("M").astype(str)
            filtered = filtered[month_strs.isin(months)]

    if skus and COL["sku"] in filtered.columns:
        filtered = filtered[filtered[COL["sku"]].isin(skus)]

    if inventory_status and COL["inventory_status"] in filtered.columns:
        filtered = filtered[filtered[COL["inventory_status"]].isin(inventory_status)]

    if promotion and COL["promotion"] in filtered.columns:
        filtered = filtered[filtered[COL["promotion"]].isin(promotion)]

    return filtered


# =========================================================
# 6. KPI CALCULATIONS  (all derived dynamically from df)
# =========================================================
def safe_mean(series: pd.Series):
    return float(series.mean()) if series is not None and len(series) else 0.0


def safe_sum(series: pd.Series):
    return float(series.sum()) if series is not None and len(series) else 0.0


def compute_executive_kpis(df: pd.DataFrame) -> dict:
    """Compute all Executive Dashboard KPIs from the (already filtered) dataframe."""
    kpis = {
        "total_units_sold": 0.0,
        "avg_demand": 0.0,
        "healthy_pct": 0.0,
        "low_pct": 0.0,
        "critical_pct": 0.0,
        "avg_opening_stock": 0.0,
        "avg_closing_stock": 0.0,
        "num_skus": 0,
    }
    if df is None or df.empty:
        return kpis

    if COL["demand"] in df.columns:
        kpis["total_units_sold"] = safe_sum(df[COL["demand"]])
        kpis["avg_demand"] = safe_mean(df[COL["demand"]])

    if COL["inventory_status"] in df.columns and len(df):
        status_counts = df[COL["inventory_status"]].value_counts(normalize=True) * 100
        kpis["healthy_pct"] = float(status_counts.get("Healthy", 0.0))
        kpis["low_pct"] = float(status_counts.get("Low Stock", 0.0))
        # "Critical" is treated as Stockout for this dashboard
        kpis["critical_pct"] = float(status_counts.get("Stockout", 0.0))

    if COL["opening_stock"] in df.columns:
        kpis["avg_opening_stock"] = safe_mean(df[COL["opening_stock"]])

    if COL["closing_stock"] in df.columns:
        kpis["avg_closing_stock"] = safe_mean(df[COL["closing_stock"]])

    if COL["sku"] in df.columns:
        kpis["num_skus"] = int(df[COL["sku"]].nunique())

    return kpis


# =========================================================
# 7. SHARED CSS
# =========================================================
def inject_global_css():
    st.markdown(
        f"""
        <style>
            .stApp {{ background-color: {COLOR_BG}; }}
            html, body, [class*="css"] {{ font-family: 'Segoe UI', 'Inter', sans-serif; }}

            section[data-testid="stSidebar"] {{ background-color: {COLOR_SIDEBAR}; }}
            section[data-testid="stSidebar"] * {{ color: #E5E7EB !important; }}

            .section-header {{
                font-size: 1.5rem;
                font-weight: 700;
                color: #111827;
                margin: 1.8rem 0 1rem 0;
                border-left: 5px solid {COLOR_BLUE};
                padding-left: 12px;
            }}

            .kpi-card {{
                border-radius: 16px;
                padding: 1.2rem;
                text-align: center;
                color: white;
                box-shadow: 0 6px 18px rgba(0,0,0,0.12);
                margin-bottom: 1rem;
                transition: transform 0.15s ease;
            }}
            .kpi-card:hover {{ transform: translateY(-4px); }}
            .kpi-value {{ font-size: 1.7rem; font-weight: 800; margin-bottom: 0.15rem; }}
            .kpi-label {{ font-size: 0.85rem; opacity: 0.92; font-weight: 500; }}

            .fc-card {{
                background: white;
                border-radius: 16px;
                padding: 1.4rem;
                box-shadow: 0 4px 14px rgba(0,0,0,0.06);
                border: 1px solid #EEF2F7;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
                margin-bottom: 1rem;
            }}
            .fc-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 12px 28px rgba(0,0,0,0.12);
            }}

            .warning-box {{
                background: #FEF3C7;
                border: 1px solid {COLOR_ORANGE};
                border-radius: 12px;
                padding: 1rem;
                color: #92400E;
                margin-bottom: 1rem;
            }}
            .missing-file-box {{
                background: #FEE2E2;
                border: 1px solid {COLOR_RED};
                border-radius: 12px;
                padding: 1rem;
                color: #7F1D1D;
                margin-bottom: 1rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, color: str) -> str:
    return f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, {color} 0%, {color}CC 100%);">
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
    </div>
    """


def render_data_missing_notice(what: str = "dataset"):
    st.markdown(
        f"""
        <div class="missing-file-box">
            ⚠️ Could not find the {what}. Charts and KPIs below are showing empty state.
            Check the file paths at the top of <b>utils.py</b>
            (<code>DATA_PATH</code>, <code>MODEL_PATH</code>, <code>SKU_ENCODER_PATH</code>,
            <code>INVENTORY_ENCODER_PATH</code>) and make sure they point to your real files.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_model_info():
    st.markdown("#### 🤖 Model Info")
    model = load_model()
    st.markdown(f"**Algorithm:** Random Forest Regressor")
    st.markdown(f"**Status:** {'✅ Loaded' if model is not None else '⚠️ Not found'}")


# =========================================================
# 8. SHARED SIDEBAR FILTER PANEL
# =========================================================
def render_global_filters(df: pd.DataFrame) -> dict:
    """
    Renders the shared sidebar filter panel (Month, SKU, Inventory Status,
    Promotion, Reset button) and returns the selected values as a dict.
    Selections are kept in st.session_state so they persist across pages.
    """
    options = get_filter_options(df)

    st.sidebar.markdown("### 🔎 Global Filters")

    if st.sidebar.button("🔄 Reset Filters", width="stretch"):
        for key in ["flt_months", "flt_skus", "flt_status", "flt_promo"]:
            st.session_state.pop(key, None)
        st.rerun()

    months = st.sidebar.multiselect(
        "Month", options=options["months"], key="flt_months",
        help="Leave empty to include all months",
    )
    skus = st.sidebar.multiselect(
        "SKU", options=options["skus"], key="flt_skus",
        help="Leave empty to include all SKUs",
    )
    status = st.sidebar.multiselect(
        "Inventory Status", options=options["inventory_status"], key="flt_status",
        help="Leave empty to include all statuses",
    )
    promo = st.sidebar.multiselect(
        "Promotion", options=options["promotion"], key="flt_promo",
        help="Leave empty to include all",
    )

    st.sidebar.markdown("---")
    render_sidebar_model_info()

    return {"months": months, "skus": skus, "inventory_status": status, "promotion": promo}


CURRENT_YEAR = datetime.now().year