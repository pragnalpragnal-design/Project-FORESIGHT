import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="Project FORESIGHT",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------
# CUSTOM CSS
# -----------------------------------------------------
st.markdown("""
<style>

html, body, [class*="css"]{
    font-family:'Segoe UI';
}

.main{
    background:#f4f7fb;
}

[data-testid="stSidebar"]{
    background:#111827;
}

[data-testid="stSidebar"] *{
    color:white;
}

.metric-card{
    background:white;
    padding:20px;
    border-radius:15px;
    box-shadow:0px 5px 15px rgba(0,0,0,0.1);
}

.block-container{
    padding-top:2rem;
}

hr{
    margin-top:25px;
    margin-bottom:25px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# LOAD DATA
# -----------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("../data/processed/final_features_dataset.csv")

df = load_data()

# -----------------------------------------------------
# LOAD MODEL
# -----------------------------------------------------
@st.cache_resource
def load_model():
    model = joblib.load("../models/demand_forecasting_model.pkl")
    sku_encoder = joblib.load("../models/sku_encoder.pkl")
    inventory_encoder = joblib.load("../models/inventory_encoder.pkl")
    return model, sku_encoder, inventory_encoder

model, sku_encoder, inventory_encoder = load_model()

# -----------------------------------------------------
# SIDEBAR
# -----------------------------------------------------
st.sidebar.image(
    "https://img.icons8.com/color/96/artificial-intelligence.png",
    width=80
)

st.sidebar.title("Project FORESIGHT")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "🤖 AI Forecast",
        "📦 Inventory",
        "📊 Business Insights"
    ]
)

st.sidebar.markdown("---")

selected_month = st.sidebar.selectbox(
    "Select Month",
    sorted(df["month"].unique())
)

filtered_df = df[df["month"] == selected_month]

st.sidebar.markdown("---")

st.sidebar.success("Model Performance")

st.sidebar.metric(
    "R² Score",
    "85.29%"
)

st.sidebar.metric(
    "MAE",
    "0.201"
)

st.sidebar.metric(
    "RMSE",
    "0.534"
)

# -----------------------------------------------------
# HEADER
# -----------------------------------------------------
st.title("📈 Project FORESIGHT")

st.markdown("""
### AI Powered Demand Forecasting & Inventory Management Dashboard

Monitor sales trends, inventory health, promotions and AI demand forecasts using Machine Learning.
""")

st.markdown("---")

# -----------------------------------------------------
# KPI SECTION
# -----------------------------------------------------
kpi1,kpi2,kpi3,kpi4 = st.columns(4)

kpi1.metric(
    "📦 Total Records",
    f"{len(df):,}"
)

kpi2.metric(
    "🛒 Units Sold",
    f"{int(df['units_sold'].sum()):,}"
)

kpi3.metric(
    "🏷 Unique SKUs",
    f"{df['sku_id'].nunique():,}"
)

healthy = (
    (df["inventory_status"]=="Healthy")
    .sum()
)

kpi4.metric(
    "✅ Healthy Inventory",
    f"{healthy:,}"
)

st.markdown("---")

# -----------------------------------------------------
# DATA PREVIEW
# -----------------------------------------------------
st.subheader("📋 Dataset Preview")

st.dataframe(
    filtered_df.head(20),
    width="stretch"
)

st.markdown("---")
st.markdown("---")

# =====================================================
# SALES ANALYTICS
# =====================================================

st.header("📊 Sales Analytics")

col1, col2 = st.columns(2)

# -----------------------------
# Monthly Sales Trend
# -----------------------------
with col1:

    monthly_sales = (
        filtered_df
        .groupby("month")["units_sold"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        monthly_sales,
        x="month",
        y="units_sold",
        markers=True,
        title="Monthly Sales Trend",
        template="plotly_white"
    )

    fig.update_layout(
        height=430,
        title_x=0.25,
        xaxis_title="Month",
        yaxis_title="Units Sold"
    )

    st.plotly_chart(fig, width="stretch")

# -----------------------------
# Promotion Analysis
# -----------------------------
with col2:

    promo = (
        filtered_df
        .groupby("promo_flag")["units_sold"]
        .mean()
        .reset_index()
    )

    promo["promo_flag"] = promo["promo_flag"].replace({
        0:"No Promotion",
        1:"Promotion"
    })

    fig = px.bar(
        promo,
        x="promo_flag",
        y="units_sold",
        color="promo_flag",
        text_auto=".2f",
        title="Average Sales During Promotions",
        template="plotly_white"
    )

    fig.update_layout(
        height=430,
        showlegend=False
    )

    st.plotly_chart(fig, width="stretch")

st.markdown("---")

# =====================================================
# INVENTORY ANALYTICS
# =====================================================

st.header("📦 Inventory Analytics")

col3, col4 = st.columns(2)

# -----------------------------
# Inventory Donut Chart
# -----------------------------
with col3:

    inventory = (
        filtered_df["inventory_status"]
        .value_counts()
        .reset_index()
    )

    inventory.columns = [
        "Inventory Status",
        "Count"
    ]

    fig = px.pie(
        inventory,
        values="Count",
        names="Inventory Status",
        hole=0.55,
        title="Inventory Distribution"
    )

    fig.update_layout(
        height=430
    )

    st.plotly_chart(fig, width="stretch")

# -----------------------------
# Opening vs Closing Stock
# -----------------------------
with col4:

    stock = pd.DataFrame({
        "Stock Type":[
            "Opening Stock",
            "Closing Stock"
        ],
        "Stock":[
            filtered_df["opening_stock"].sum(),
            filtered_df["closing_stock"].sum()
        ]
    })

    fig = px.bar(
        stock,
        x="Stock Type",
        y="Stock",
        color="Stock Type",
        text_auto=True,
        title="Opening vs Closing Stock",
        template="plotly_white"
    )

    fig.update_layout(
        height=430,
        showlegend=False
    )

    st.plotly_chart(fig, width="stretch")

st.markdown("---")

# =====================================================
# WEEKLY SALES
# =====================================================

st.header("📅 Weekly Sales Pattern")

weekday = (
    filtered_df
    .groupby("day_of_week")["units_sold"]
    .sum()
    .reset_index()
)

weekday["day_of_week"] = weekday["day_of_week"].replace({
    1:"Mon",
    2:"Tue",
    3:"Wed",
    4:"Thu",
    5:"Fri",
    6:"Sat",
    7:"Sun"
})

fig = px.area(
    weekday,
    x="day_of_week",
    y="units_sold",
    title="Weekly Sales Pattern",
    template="plotly_white"
)

fig.update_layout(
    height=420
)

st.plotly_chart(
    fig,
    width="stretch"
)

st.markdown("---")

# =====================================================
# TOP SELLING PRODUCTS
# =====================================================

st.header("🔥 Top Selling Products")

top_products = (
    filtered_df
    .groupby("sku_id")["units_sold"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig = px.bar(
    top_products,
    x="sku_id",
    y="units_sold",
    color="units_sold",
    text_auto=True,
    title="Top 10 Selling SKUs",
    template="plotly_white"
)

fig.update_layout(
    height=520,
    xaxis_title="SKU",
    yaxis_title="Units Sold"
)

st.plotly_chart(
    fig,
    width="stretch"
)

st.markdown("---")
# =====================================================
# AI DEMAND FORECAST
# =====================================================

st.header("🤖 AI Demand Forecast")

# Create a copy
prediction_df = filtered_df.copy()

# Encode using saved encoders
prediction_df["sku_id"] = sku_encoder.transform(
    prediction_df["sku_id"].astype(str)
)

prediction_df["inventory_status"] = inventory_encoder.transform(
    prediction_df["inventory_status"].astype(str)
)

# EXACT FEATURES USED DURING TRAINING
feature_columns = [
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
    "rolling_mean_30"
]

X_predict = prediction_df[feature_columns]

prediction_df["Predicted_Demand"] = model.predict(X_predict)

forecast_df = filtered_df.copy()
forecast_df["Predicted_Demand"] = prediction_df["Predicted_Demand"]
# =====================================================
# BUSINESS INSIGHTS
# =====================================================

st.header("📊 Executive Business Insights")

col1, col2 = st.columns(2)

with col1:

    st.info("""
### 📌 Key Insights

✔️ AI model predicts future demand using historical sales.

✔️ Promotions increase average product sales.

✔️ Inventory monitoring helps reduce stock-outs.

✔️ Low-stock products are automatically identified.

✔️ Dashboard updates instantly with month selection.

✔️ Forecasts can support procurement planning.
""")

with col2:

    st.success("""
### 🚀 Recommendations

• Increase stock for high-demand products.

• Reduce excess inventory for slow-moving items.

• Run promotions during low-demand periods.

• Monitor weekly sales patterns.

• Use AI forecasts before replenishment.

• Download reports for management review.
""")

st.markdown("---")

# =====================================================
# FEATURE IMPORTANCE
# =====================================================

st.header("🧠 Machine Learning Feature Importance")

importance = pd.DataFrame({
    "Feature": X_predict.columns,
    "Importance": model.feature_importances_
})

importance = importance.sort_values(
    by="Importance",
    ascending=False
)

fig = px.bar(
    importance,
    x="Importance",
    y="Feature",
    orientation="h",
    color="Importance",
    title="Random Forest Feature Importance",
    template="plotly_white"
)

fig.update_layout(height=500)

st.plotly_chart(
    fig,
    width="stretch"
)

st.markdown("---")

# =====================================================
# PROJECT SUMMARY
# =====================================================

st.header("📋 Project Summary")

summary_col1, summary_col2, summary_col3 = st.columns(3)

summary_col1.metric(
    "📈 Forecast Accuracy",
    "85.29%"
)

summary_col2.metric(
    "🤖 ML Algorithm",
    "Random Forest"
)

summary_col3.metric(
    "📦 Records Analysed",
    f"{len(df):,}"
)

st.markdown("---")

# =====================================================
# ABOUT PROJECT
# =====================================================

with st.expander("ℹ️ About Project FORESIGHT", expanded=False):

    st.markdown("""
### Project FORESIGHT

Project FORESIGHT is an AI-powered demand forecasting and inventory management system developed using Machine Learning.

### Technologies Used

- Python
- Pandas
- Scikit-learn
- Streamlit
- Plotly
- Joblib

### Machine Learning Model

- Random Forest Regressor

### Features

- 📊 Interactive Dashboard
- 🤖 AI Demand Prediction
- 📦 Inventory Monitoring
- 📈 Sales Analytics
- 📥 Download Forecast Report
- 🔍 SKU-level Analysis
""")

st.markdown("---")

# =====================================================
# FOOTER
# =====================================================

st.markdown(
"""
<div style="text-align:center;padding:20px;background:#111827;border-radius:12px;color:white;">

<h3>📈 Project FORESIGHT</h3>

<p>
AI Powered Demand Forecasting & Inventory Management Dashboard
</p>

<p>
Developed using Streamlit • Plotly • Random Forest Machine Learning
</p>

<hr>

<p>
Built for Internship Project Demonstration
</p>

</div>
""",
unsafe_allow_html=True
)