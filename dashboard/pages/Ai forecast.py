"""
Project FORESIGHT — Page 2: AI Forecast
Real prediction interface. Loads the saved Random Forest model and the
saved LabelEncoders (sku_encoder.pkl, inventory_encoder.pkl) — never retrains.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils import (
    COL,
    MODEL_FEATURES,
    PLOTLY_TEMPLATE,
    inject_global_css,
    load_data,
    load_encoders,
    load_model,
    render_data_missing_notice,
    safe_encode,
)

st.set_page_config(page_title="AI Forecast | FORESIGHT", page_icon="🤖", layout="wide")
inject_global_css()

st.title("🤖 AI Forecast")
st.caption("Predict future demand using the trained Random Forest model.")

# ---------------------------------------------------------
# Load model, encoders, data
# ---------------------------------------------------------
model = load_model()
sku_encoder, inventory_encoder = load_encoders()
df_raw = load_data()

with st.sidebar:
    st.markdown("## 🤖 AI Forecast")
    st.markdown("Fill in the inputs, then click **Predict Demand**.")
    st.markdown("---")
    st.markdown("#### Model Status")
    st.markdown(f"Model: {'✅ Loaded' if model is not None else '❌ Not found'}")
    st.markdown(f"SKU Encoder: {'✅ Loaded' if sku_encoder is not None else '❌ Not found'}")
    st.markdown(f"Inventory Encoder: {'✅ Loaded' if inventory_encoder is not None else '❌ Not found'}")

if model is None:
    render_data_missing_notice("trained model (demand_forecasting_model.pkl)")
if sku_encoder is None or inventory_encoder is None:
    st.markdown(
        """
        <div class="warning-box">
            ⚠️ One or both encoders (<code>sku_encoder.pkl</code>, <code>inventory_encoder.pkl</code>)
            could not be loaded. Check <code>MODEL_PATH</code>, <code>SKU_ENCODER_PATH</code>,
            and <code>INVENTORY_ENCODER_PATH</code> in <b>utils.py</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Initialize prediction history in session state
if "prediction_history" not in st.session_state:
    st.session_state.prediction_history = []

# ---------------------------------------------------------
# INPUT FORM
# ---------------------------------------------------------
st.markdown('<div class="section-header">📝 Forecast Inputs</div>', unsafe_allow_html=True)

sku_options = list(sku_encoder.classes_) if sku_encoder is not None else []
inventory_options = list(inventory_encoder.classes_) if inventory_encoder is not None else [
    "Healthy", "Low Stock", "Overstock", "Stockout"
]

with st.form("forecast_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        sku_input = st.selectbox("SKU", options=sku_options if sku_options else ["No SKUs loaded"])
        promotion_input = st.selectbox("Promotion", options=["No", "Yes"])
        opening_stock_input = st.number_input("Opening Stock", min_value=0, value=100, step=1)
        closing_stock_input = st.number_input("Closing Stock", min_value=0, value=80, step=1)

    with col2:
        inventory_status_input = st.selectbox("Inventory Status", options=inventory_options)
        holiday_input = st.selectbox("Holiday", options=["No", "Yes"])
        month_input = st.selectbox("Month", options=list(range(1, 13)), index=6)
        day_of_week_input = st.selectbox(
            "Day of Week",
            options=list(range(0, 7)),
            format_func=lambda x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][x],
        )

    with col3:
        lag_1_input = st.number_input("Lag_1 (yesterday's demand)", min_value=0.0, value=50.0, step=1.0)
        lag_7_input = st.number_input("Lag_7 (demand 7 days ago)", min_value=0.0, value=50.0, step=1.0)
        lag_30_input = st.number_input("Lag_30 (demand 30 days ago)", min_value=0.0, value=50.0, step=1.0)
        rolling_mean_7_input = st.number_input("Rolling Mean (7-day)", min_value=0.0, value=50.0, step=1.0)
        rolling_mean_30_input = st.number_input("Rolling Mean (30-day)", min_value=0.0, value=50.0, step=1.0)

    submitted = st.form_submit_button("🔮 Predict Demand", use_container_width=True)

# ---------------------------------------------------------
# PREDICTION LOGIC
# ---------------------------------------------------------
if submitted:
    if model is None:
        st.error("Cannot predict: model file not loaded. Check MODEL_PATH in utils.py.")
    elif sku_encoder is None or inventory_encoder is None:
        st.error("Cannot predict: one or both encoders not loaded. Check encoder paths in utils.py.")
    else:
        sku_encoded, sku_ok, sku_msg = safe_encode(sku_encoder, sku_input)
        inv_encoded, inv_ok, inv_msg = safe_encode(inventory_encoder, inventory_status_input)

        if not sku_ok:
            st.error(f"SKU encoding failed: {sku_msg}")
        elif not inv_ok:
            st.error(f"Inventory Status encoding failed: {inv_msg}")
        else:
            feature_row = {
                "sku_encoded": sku_encoded,
                "promo_flag": 1 if promotion_input == "Yes" else 0,
                "opening_stock": opening_stock_input,
                "closing_stock": closing_stock_input,
                "inventory_status_encoded": inv_encoded,
                "is_holiday": 1 if holiday_input == "Yes" else 0,
                "month": month_input,
                "day_of_week": day_of_week_input,
                "lag_1": lag_1_input,
                "lag_7": lag_7_input,
                "lag_30": lag_30_input,
                "rolling_mean_7": rolling_mean_7_input,
                "rolling_mean_30": rolling_mean_30_input,
            }

            try:
                X = pd.DataFrame([[feature_row[f] for f in MODEL_FEATURES]], columns=MODEL_FEATURES)
                prediction = float(model.predict(X)[0])
            except Exception as e:
                st.error(
                    f"Prediction failed: {e}\n\n"
                    "This usually means MODEL_FEATURES in utils.py doesn't match the exact "
                    "column names/order the model was trained on — update that list to match."
                )
                prediction = None

            if prediction is not None:
                # ---- Confidence proxy from tree spread (Random Forest) ----
                confidence = None
                try:
                    tree_preds = np.array([t.predict(X)[0] for t in model.estimators_])
                    spread = tree_preds.std()
                    # Convert spread into a rough 0-100% confidence score (lower spread = higher confidence)
                    confidence = max(0.0, min(100.0, 100 - (spread / (abs(prediction) + 1e-6)) * 100))
                except Exception:
                    confidence = None

                # ---- Inventory recommendation logic ----
                if closing_stock_input < prediction:
                    stock_risk = "🔴 High Risk — likely stockout"
                    procurement_rec = "Reorder immediately, prioritize this SKU."
                elif closing_stock_input < prediction * 1.3:
                    stock_risk = "🟠 Medium Risk — stock is tight"
                    procurement_rec = "Plan a restock within the next few days."
                else:
                    stock_risk = "🟢 Low Risk — stock is sufficient"
                    procurement_rec = "No immediate action needed."

                # ---- Display results ----
                st.markdown('<div class="section-header">🎯 Prediction Result</div>', unsafe_allow_html=True)

                res_col1, res_col2 = st.columns([1, 1])

                with res_col1:
                    st.markdown(
                        f"""
                        <div class="fc-card" style="text-align:center;">
                            <div style="font-size:0.95rem; color:#6B7280;">Predicted Demand</div>
                            <div style="font-size:2.4rem; font-weight:800; color:#2563EB;">
                                {prediction:,.1f} units
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"""
                        <div class="fc-card">
                            <b>Stock Risk:</b> {stock_risk}<br>
                            <b>Procurement Recommendation:</b> {procurement_rec}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with res_col2:
                    gauge_value = confidence if confidence is not None else 50.0
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=gauge_value,
                        title={"text": "Prediction Confidence (%)"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#2563EB"},
                            "steps": [
                                {"range": [0, 40], "color": "#FEE2E2"},
                                {"range": [40, 70], "color": "#FEF3C7"},
                                {"range": [70, 100], "color": "#DCFCE7"},
                            ],
                        },
                    ))
                    fig.update_layout(template=PLOTLY_TEMPLATE, height=280)
                    st.plotly_chart(fig, use_container_width=True)

                # ---- Store prediction ----
                record = {
                    "sku": sku_input,
                    "promotion": promotion_input,
                    "opening_stock": opening_stock_input,
                    "closing_stock": closing_stock_input,
                    "inventory_status": inventory_status_input,
                    "holiday": holiday_input,
                    "month": month_input,
                    "day_of_week": day_of_week_input,
                    "predicted_demand": round(prediction, 2),
                    "confidence_pct": round(confidence, 1) if confidence is not None else None,
                    "stock_risk": stock_risk,
                }
                st.session_state.prediction_history.append(record)

# ---------------------------------------------------------
# ACTUAL VS PREDICTED (if actual data exists for this SKU)
# ---------------------------------------------------------
if df_raw is not None and COL["sku"] in df_raw.columns and COL["demand"] in df_raw.columns:
    st.markdown('<div class="section-header">📉 Actual vs Predicted (Historical)</div>', unsafe_allow_html=True)
    hist_sku = st.selectbox("View history for SKU", options=sorted(df_raw[COL["sku"]].dropna().unique().tolist()), key="hist_sku_select")
    hist_df = df_raw[df_raw[COL["sku"]] == hist_sku]
    if COL["date"] in hist_df.columns and not hist_df.empty:
        hist_df = hist_df.sort_values(COL["date"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_df[COL["date"]], y=hist_df[COL["demand"]], name="Actual Demand", line=dict(color="#22C55E")))
        fig.update_layout(template=PLOTLY_TEMPLATE, xaxis_title="Date", yaxis_title="Demand")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical rows found for this SKU / missing date column.")

# ---------------------------------------------------------
# PREDICTION HISTORY + DOWNLOAD
# ---------------------------------------------------------
st.markdown('<div class="section-header">📥 Prediction History</div>', unsafe_allow_html=True)

if st.session_state.prediction_history:
    hist_df_out = pd.DataFrame(st.session_state.prediction_history)
    st.dataframe(hist_df_out, use_container_width=True)
    csv_bytes = hist_df_out.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Predictions as CSV",
        data=csv_bytes,
        file_name="foresight_predictions.csv",
        mime="text/csv",
        use_container_width=True,
    )
else:
    st.info("No predictions made yet this session.")