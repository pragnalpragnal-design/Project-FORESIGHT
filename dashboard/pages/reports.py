"""
Project FORESIGHT — Page 5: Reports
Downloadable Forecast, Inventory, and Business Insights reports (CSV/Excel),
plus SKU search and report filtering.
"""

import io

import pandas as pd
import streamlit as st

from utils import COL, apply_filters, inject_global_css, load_data, render_data_missing_notice, render_global_filters

st.set_page_config(page_title="Reports | FORESIGHT", page_icon="📋", layout="wide")
inject_global_css()

st.title("📋 Reports")
st.caption("Download forecast, inventory, and business insight reports.")

df_raw = load_data()

with st.sidebar:
    st.markdown("## 📋 Reports")
    filters = render_global_filters(df_raw)

if df_raw is None:
    render_data_missing_notice("dataset (final_features_dataset.csv)")
    st.stop()

df = apply_filters(
    df_raw,
    months=filters["months"],
    skus=filters["skus"],
    inventory_status=filters["inventory_status"],
    promotion=filters["promotion"],
)

if df.empty:
    st.warning("No rows match the current filter selection. Try resetting filters.")
    st.stop()


def to_excel_bytes(dataframe: pd.DataFrame) -> bytes:
    """Convert a dataframe to an in-memory Excel file."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Report")
    return buffer.getvalue()


# ---------------------------------------------------------
# SEARCH / FILTER
# ---------------------------------------------------------
st.markdown('<div class="section-header">🔍 Search &amp; Filter Reports</div>', unsafe_allow_html=True)

search_col1, search_col2 = st.columns([2, 1])
with search_col1:
    search_sku = st.text_input("Search SKU (partial match supported)", "")
with search_col2:
    row_limit = st.number_input("Max rows to show", min_value=10, max_value=5000, value=100, step=10)

filtered_report_df = df.copy()
if search_sku and COL["sku"] in filtered_report_df.columns:
    filtered_report_df = filtered_report_df[
        filtered_report_df[COL["sku"]].astype(str).str.contains(search_sku, case=False, na=False)
    ]

st.dataframe(filtered_report_df.head(int(row_limit)), use_container_width=True, height=350)

# ---------------------------------------------------------
# DOWNLOAD SECTIONS
# ---------------------------------------------------------
st.markdown('<div class="section-header">⬇️ Downloadable Reports</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

# --- Forecast Report: prediction history from this session (AI Forecast page) ---
with col1:
    st.markdown("**Forecast Report**")
    pred_history = st.session_state.get("prediction_history", [])
    if pred_history:
        forecast_df = pd.DataFrame(pred_history)
        st.download_button(
            "Download Forecast (CSV)",
            data=forecast_df.to_csv(index=False).encode("utf-8"),
            file_name="forecast_report.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download Forecast (Excel)",
            data=to_excel_bytes(forecast_df),
            file_name="forecast_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.info("No forecasts generated yet — visit the AI Forecast page first.")

# --- Inventory Report ---
with col2:
    st.markdown("**Inventory Report**")
    inv_cols = [c for c in [COL["sku"], COL["inventory_status"], COL["opening_stock"], COL["closing_stock"]] if c in df.columns]
    if inv_cols:
        inventory_report_df = filtered_report_df[inv_cols]
        st.download_button(
            "Download Inventory (CSV)",
            data=inventory_report_df.to_csv(index=False).encode("utf-8"),
            file_name="inventory_report.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download Inventory (Excel)",
            data=to_excel_bytes(inventory_report_df),
            file_name="inventory_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.info("Required inventory columns not found in dataset.")

# --- Business Insights Report ---
with col3:
    st.markdown("**Business Insights Report**")
    if COL["sku"] in df.columns and COL["demand"] in df.columns:
        insights_df = df.groupby(COL["sku"]).agg(
            total_demand=(COL["demand"], "sum"),
            avg_demand=(COL["demand"], "mean"),
        ).reset_index().sort_values("total_demand", ascending=False)

        st.download_button(
            "Download Insights (CSV)",
            data=insights_df.to_csv(index=False).encode("utf-8"),
            file_name="business_insights_report.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.download_button(
            "Download Insights (Excel)",
            data=to_excel_bytes(insights_df),
            file_name="business_insights_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.info("Required columns ('sku', 'demand') not found in dataset.")