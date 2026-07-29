"""
Project FORESIGHT — Page 3: Inventory Management
All figures derived dynamically from the filtered dataset.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (
    COL,
    PLOTLY_TEMPLATE,
    apply_filters,
    inject_global_css,
    kpi_card,
    load_data,
    render_data_missing_notice,
    render_global_filters,
)

st.set_page_config(page_title="Inventory | FORESIGHT", page_icon="📦", layout="wide")
inject_global_css()

st.title("📦 Inventory Management")
st.caption("Monitor stock health, distribution, and restocking priorities.")

df_raw = load_data()

with st.sidebar:
    st.markdown("## 📦 Inventory")
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

has_status = COL["inventory_status"] in df.columns
has_stock = COL["opening_stock"] in df.columns and COL["closing_stock"] in df.columns
has_sku = COL["sku"] in df.columns

# ---------------------------------------------------------
# KPI ROW
# ---------------------------------------------------------
if has_status:
    status_counts_pct = df[COL["inventory_status"]].value_counts(normalize=True) * 100
    healthy = float(status_counts_pct.get("Healthy", 0.0))
    low = float(status_counts_pct.get("Low Stock", 0.0))
    critical = float(status_counts_pct.get("Stockout", 0.0))
else:
    healthy = low = critical = 0.0

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(kpi_card("Healthy Inventory", f"{healthy:.1f}%", "#22C55E"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("Low Inventory", f"{low:.1f}%", "#F59E0B"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card("Critical Inventory", f"{critical:.1f}%", "#EF4444"), unsafe_allow_html=True)

# ---------------------------------------------------------
# DISTRIBUTION + GAUGE
# ---------------------------------------------------------
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.markdown('<div class="section-header">📊 Inventory Distribution</div>', unsafe_allow_html=True)
    if has_status:
        status_counts = df[COL["inventory_status"]].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(
            status_counts, names="status", values="count", hole=0.45,
            template=PLOTLY_TEMPLATE, color="status",
            color_discrete_map={
                "Healthy": "#22C55E", "Low Stock": "#F59E0B",
                "Overstock": "#2563EB", "Stockout": "#EF4444",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'inventory_status' column.")

with row1_col2:
    st.markdown('<div class="section-header">🎚️ Inventory Health Gauge</div>', unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=healthy,
        title={"text": "Healthy Inventory %"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#22C55E"},
            "steps": [
                {"range": [0, 40], "color": "#FEE2E2"},
                {"range": [40, 70], "color": "#FEF3C7"},
                {"range": [70, 100], "color": "#DCFCE7"},
            ],
        },
    ))
    fig.update_layout(template=PLOTLY_TEMPLATE, height=320)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# OPENING VS CLOSING STOCK
# ---------------------------------------------------------
st.markdown('<div class="section-header">📦 Opening vs Closing Stock</div>', unsafe_allow_html=True)
if has_stock and COL["date"] in df.columns:
    stock_trend = (
        df.assign(_month=df[COL["date"]].dt.to_period("M").astype(str))
        .groupby("_month")[[COL["opening_stock"], COL["closing_stock"]]]
        .mean()
        .reset_index()
        .sort_values("_month")
    )
    fig = go.Figure()
    fig.add_trace(go.Bar(x=stock_trend["_month"], y=stock_trend[COL["opening_stock"]], name="Opening Stock", marker_color="#2563EB"))
    fig.add_trace(go.Bar(x=stock_trend["_month"], y=stock_trend[COL["closing_stock"]], name="Closing Stock", marker_color="#F59E0B"))
    fig.update_layout(template=PLOTLY_TEMPLATE, barmode="group", xaxis_title="Month", yaxis_title="Avg Stock")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Requires 'date', 'opening_stock', 'closing_stock' columns.")

# ---------------------------------------------------------
# OVERSTOCKED / LOW STOCK PRODUCTS
# ---------------------------------------------------------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown('<div class="section-header">📈 Top Overstocked Products</div>', unsafe_allow_html=True)
    if has_sku and has_stock:
        overstock = (
            df.groupby(COL["sku"])[COL["closing_stock"]]
            .mean()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig = px.bar(
            overstock, x=COL["closing_stock"], y=COL["sku"], orientation="h",
            template=PLOTLY_TEMPLATE, color_discrete_sequence=["#2563EB"],
            labels={COL["closing_stock"]: "Avg Closing Stock", COL["sku"]: "SKU"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'sku' and 'closing_stock' columns.")

with row2_col2:
    st.markdown('<div class="section-header">📉 Top Low Stock Products</div>', unsafe_allow_html=True)
    if has_sku and has_stock:
        low_stock = (
            df.groupby(COL["sku"])[COL["closing_stock"]]
            .mean()
            .sort_values(ascending=True)
            .head(10)
            .reset_index()
        )
        fig = px.bar(
            low_stock, x=COL["closing_stock"], y=COL["sku"], orientation="h",
            template=PLOTLY_TEMPLATE, color_discrete_sequence=["#EF4444"],
            labels={COL["closing_stock"]: "Avg Closing Stock", COL["sku"]: "SKU"},
        )
        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'sku' and 'closing_stock' columns.")

# ---------------------------------------------------------
# RESTOCKING RECOMMENDATIONS + STOCK HEALTH TABLE
# ---------------------------------------------------------
st.markdown('<div class="section-header">🛒 Restocking Recommendations</div>', unsafe_allow_html=True)

if has_sku and has_stock and COL["demand"] in df.columns:
    sku_summary = df.groupby(COL["sku"]).agg(
        avg_demand=(COL["demand"], "mean"),
        avg_closing_stock=(COL["closing_stock"], "mean"),
    ).reset_index()

    def recommend(row):
        if row["avg_closing_stock"] < row["avg_demand"]:
            return "🔴 Reorder Now"
        elif row["avg_closing_stock"] < row["avg_demand"] * 1.3:
            return "🟠 Monitor Closely"
        else:
            return "🟢 Sufficient Stock"

    sku_summary["recommendation"] = sku_summary.apply(recommend, axis=1)
    sku_summary = sku_summary.sort_values("avg_demand", ascending=False)

    st.dataframe(sku_summary, use_container_width=True, height=350)
else:
    st.info("Requires 'sku', 'closing_stock', and 'demand' columns to generate recommendations.")