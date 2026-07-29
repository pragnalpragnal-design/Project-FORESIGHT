"""
Project FORESIGHT — Page 1: Executive Dashboard
All KPIs and charts are computed dynamically from final_features_dataset.csv
and respond live to the sidebar filters.
"""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (
    COL,
    PLOTLY_TEMPLATE,
    apply_filters,
    compute_executive_kpis,
    inject_global_css,
    kpi_card,
    load_data,
    render_data_missing_notice,
    render_global_filters,
)

st.set_page_config(page_title="Executive Dashboard | FORESIGHT", page_icon="📈", layout="wide")
inject_global_css()

st.title("📈 Executive Dashboard")
st.caption("Live overview of sales performance and inventory health.")

# ---------------------------------------------------------
# Load data + filters
# ---------------------------------------------------------
df_raw = load_data()

with st.sidebar:
    st.markdown("## 📈 Executive Dashboard")
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

# ---------------------------------------------------------
# KPI ROW 1
# ---------------------------------------------------------
kpis = compute_executive_kpis(df)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(kpi_card("Total Units Sold", f"{kpis['total_units_sold']:,.0f}", "#2563EB"), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("Average Demand", f"{kpis['avg_demand']:,.2f}", "#22C55E"), unsafe_allow_html=True)
with c3:
    st.markdown(kpi_card("Healthy Inventory %", f"{kpis['healthy_pct']:.1f}%", "#22C55E"), unsafe_allow_html=True)
with c4:
    st.markdown(kpi_card("Low Inventory %", f"{kpis['low_pct']:.1f}%", "#F59E0B"), unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)
with c5:
    st.markdown(kpi_card("Critical Inventory %", f"{kpis['critical_pct']:.1f}%", "#EF4444"), unsafe_allow_html=True)
with c6:
    st.markdown(kpi_card("Avg Opening Stock", f"{kpis['avg_opening_stock']:,.1f}", "#2563EB"), unsafe_allow_html=True)
with c7:
    st.markdown(kpi_card("Avg Closing Stock", f"{kpis['avg_closing_stock']:,.1f}", "#2563EB"), unsafe_allow_html=True)
with c8:
    st.markdown(kpi_card("Number of SKUs", f"{kpis['num_skus']:,}", "#F59E0B"), unsafe_allow_html=True)

# ---------------------------------------------------------
# SALES TRENDS
# ---------------------------------------------------------
st.markdown('<div class="section-header">📊 Sales Trends</div>', unsafe_allow_html=True)

trend_col1, trend_col2 = st.columns(2)

with trend_col1:
    st.markdown("**Monthly Sales Trend**")
    if COL["date"] in df.columns and COL["demand"] in df.columns:
        monthly = (
            df.assign(_month=df[COL["date"]].dt.to_period("M").astype(str))
            .groupby("_month")[COL["demand"]]
            .sum()
            .reset_index()
            .sort_values("_month")
        )
        fig = px.line(
            monthly, x="_month", y=COL["demand"], markers=True,
            template=PLOTLY_TEMPLATE, labels={"_month": "Month", COL["demand"]: "Units Sold"},
        )
        fig.update_traces(line_color="#2563EB")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'date' and 'demand' columns.")

with trend_col2:
    st.markdown("**Weekly Sales Trend**")
    if COL["date"] in df.columns and COL["demand"] in df.columns:
        weekly = (
            df.assign(_week=df[COL["date"]].dt.to_period("W").astype(str))
            .groupby("_week")[COL["demand"]]
            .sum()
            .reset_index()
            .sort_values("_week")
        )
        fig = px.line(
            weekly, x="_week", y=COL["demand"], markers=True,
            template=PLOTLY_TEMPLATE, labels={"_week": "Week", COL["demand"]: "Units Sold"},
        )
        fig.update_traces(line_color="#22C55E")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'date' and 'demand' columns.")

# ---------------------------------------------------------
# PROMOTION EFFECTIVENESS + INVENTORY DISTRIBUTION
# ---------------------------------------------------------
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.markdown("**Promotion Effectiveness**")
    if COL["promotion"] in df.columns and COL["demand"] in df.columns:
        promo_group = df.groupby(COL["promotion"])[COL["demand"]].mean().reset_index()
        fig = px.bar(
            promo_group, x=COL["promotion"], y=COL["demand"],
            template=PLOTLY_TEMPLATE, color=COL["promotion"],
            labels={COL["demand"]: "Avg Demand", COL["promotion"]: "Promotion"},
            color_discrete_sequence=["#94A3B8", "#2563EB"],
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'promotion' and 'demand' columns.")

with row2_col2:
    st.markdown("**Inventory Distribution**")
    if COL["inventory_status"] in df.columns:
        status_counts = df[COL["inventory_status"]].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig = px.pie(
            status_counts, names="status", values="count", hole=0.45,
            template=PLOTLY_TEMPLATE,
            color="status",
            color_discrete_map={
                "Healthy": "#22C55E",
                "Low Stock": "#F59E0B",
                "Overstock": "#2563EB",
                "Stockout": "#EF4444",
            },
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'inventory_status' column.")

# ---------------------------------------------------------
# TOP 10 SELLING PRODUCTS + OPENING VS CLOSING STOCK
# ---------------------------------------------------------
row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.markdown("**Top 10 Selling Products**")
    if COL["sku"] in df.columns and COL["demand"] in df.columns:
        top10 = (
            df.groupby(COL["sku"])[COL["demand"]]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .reset_index()
        )
        fig = px.bar(
            top10, x=COL["demand"], y=COL["sku"], orientation="h",
            template=PLOTLY_TEMPLATE, color=COL["demand"],
            color_continuous_scale=["#93C5FD", "#2563EB"],
            labels={COL["demand"]: "Total Units Sold", COL["sku"]: "SKU"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'sku' and 'demand' columns.")

with row3_col2:
    st.markdown("**Opening vs Closing Stock**")
    if COL["date"] in df.columns and COL["opening_stock"] in df.columns and COL["closing_stock"] in df.columns:
        stock_trend = (
            df.assign(_month=df[COL["date"]].dt.to_period("M").astype(str))
            .groupby("_month")[[COL["opening_stock"], COL["closing_stock"]]]
            .mean()
            .reset_index()
            .sort_values("_month")
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=stock_trend["_month"], y=stock_trend[COL["opening_stock"]],
            name="Opening Stock", line=dict(color="#2563EB"),
        ))
        fig.add_trace(go.Scatter(
            x=stock_trend["_month"], y=stock_trend[COL["closing_stock"]],
            name="Closing Stock", line=dict(color="#F59E0B"),
        ))
        fig.update_layout(template=PLOTLY_TEMPLATE, xaxis_title="Month", yaxis_title="Stock Level")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Requires 'date', 'opening_stock', 'closing_stock' columns.")

# ---------------------------------------------------------
# RECENT TRANSACTIONS TABLE
# ---------------------------------------------------------
st.markdown('<div class="section-header">🧾 Recent Transactions</div>', unsafe_allow_html=True)

sort_col = COL["date"] if COL["date"] in df.columns else df.columns[0]
recent = df.sort_values(sort_col, ascending=False).head(25)
st.dataframe(recent, use_container_width=True, height=350)