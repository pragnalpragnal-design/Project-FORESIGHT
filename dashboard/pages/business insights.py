"""
Project FORESIGHT — Page 4: Business Insights
Every stat and recommendation is calculated live from the filtered data —
nothing here is hardcoded.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    COL,
    PLOTLY_TEMPLATE,
    apply_filters,
    inject_global_css,
    load_data,
    load_model,
    render_data_missing_notice,
    render_global_filters,
)

st.set_page_config(page_title="Business Insights | FORESIGHT", page_icon="📊", layout="wide")
inject_global_css()

st.title("📊 Business Insights")
st.caption("Automatically calculated trends and recommendations.")

df_raw = load_data()

with st.sidebar:
    st.markdown("## 📊 Business Insights")
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
# CALCULATED HEADLINE STATS
# ---------------------------------------------------------
st.markdown('<div class="section-header">🔑 Key Findings</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

# Highest selling month
if COL["date"] in df.columns and COL["demand"] in df.columns:
    monthly = df.assign(_month=df[COL["date"]].dt.to_period("M").astype(str)).groupby("_month")[COL["demand"]].sum()
    top_month = monthly.idxmax() if not monthly.empty else "N/A"
    top_month_value = monthly.max() if not monthly.empty else 0
else:
    top_month, top_month_value = "N/A", 0

with c1:
    st.metric("Highest Selling Month", top_month, f"{top_month_value:,.0f} units")

# Highest selling SKU
if COL["sku"] in df.columns and COL["demand"] in df.columns:
    sku_totals = df.groupby(COL["sku"])[COL["demand"]].sum()
    top_sku = sku_totals.idxmax() if not sku_totals.empty else "N/A"
    top_sku_value = sku_totals.max() if not sku_totals.empty else 0
else:
    top_sku, top_sku_value = "N/A", 0

with c2:
    st.metric("Highest Selling SKU", top_sku, f"{top_sku_value:,.0f} units")

# Average promotion lift
if COL["promotion"] in df.columns and COL["demand"] in df.columns:
    promo_means = df.groupby(COL["promotion"])[COL["demand"]].mean()
    if len(promo_means) >= 2:
        promo_vals = promo_means.sort_index()
        lift_pct = ((promo_vals.iloc[-1] - promo_vals.iloc[0]) / (promo_vals.iloc[0] + 1e-9)) * 100
    else:
        lift_pct = 0.0
else:
    lift_pct = 0.0

with c3:
    st.metric("Average Promotion Lift", f"{lift_pct:.1f}%")

# Average weekly demand
if COL["date"] in df.columns and COL["demand"] in df.columns:
    weekly = df.assign(_week=df[COL["date"]].dt.to_period("W").astype(str)).groupby("_week")[COL["demand"]].sum()
    avg_weekly = weekly.mean() if not weekly.empty else 0
else:
    avg_weekly = 0

with c4:
    st.metric("Average Weekly Demand", f"{avg_weekly:,.1f}")

# ---------------------------------------------------------
# FEATURE IMPORTANCE
# ---------------------------------------------------------
st.markdown('<div class="section-header">🌳 Feature Importance</div>', unsafe_allow_html=True)

model = load_model()
if model is not None and hasattr(model, "feature_importances_"):
    from utils import MODEL_FEATURES
    importances = pd.DataFrame({
        "feature": MODEL_FEATURES,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    fig = px.bar(
        importances, x="importance", y="feature", orientation="h",
        template=PLOTLY_TEMPLATE, color="importance",
        color_continuous_scale=["#93C5FD", "#2563EB"],
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Feature importance requires the trained model to be loaded (demand_forecasting_model.pkl).")

# ---------------------------------------------------------
# BUSINESS RECOMMENDATIONS (generated from calculated values)
# ---------------------------------------------------------
st.markdown('<div class="section-header">💡 Business Recommendations</div>', unsafe_allow_html=True)

recommendations = []

if top_sku != "N/A":
    recommendations.append(
        f"**{top_sku}** is the top-performing SKU — ensure consistent stock availability for it."
    )
if top_month != "N/A":
    recommendations.append(
        f"Demand peaked in **{top_month}** — plan procurement and staffing ahead of similar periods."
    )
if lift_pct > 5:
    recommendations.append(
        f"Promotions are driving a **{lift_pct:.1f}%** lift in average demand — consider expanding promotional campaigns."
    )
elif lift_pct < 0:
    recommendations.append(
        "Promotions currently show a negative lift on average demand — review promotion targeting and timing."
    )

if COL["inventory_status"] in df.columns:
    critical_pct = (df[COL["inventory_status"]] == "Stockout").mean() * 100
    if critical_pct > 10:
        recommendations.append(
            f"**{critical_pct:.1f}%** of records are in stockout status — prioritize replenishment for affected SKUs."
        )

if not recommendations:
    recommendations.append("Not enough data in the current filter selection to generate recommendations.")

for rec in recommendations:
    st.markdown(f"- {rec}")