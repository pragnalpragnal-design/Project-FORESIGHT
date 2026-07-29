<<<<<<< HEAD
# 📈 Project FORESIGHT

### AI-Powered Demand Forecasting & Inventory Management System

Project FORESIGHT is a Machine Learning-based inventory analytics dashboard that predicts product demand and helps businesses optimize inventory management using historical sales data.

The project combines **Python**, **Machine Learning**, **Streamlit**, and **Plotly** to provide interactive dashboards, demand forecasting, inventory monitoring, business insights, and downloadable reports.

---

# 🚀 Features

## 📊 Executive Dashboard
- Live KPI cards
- Total Units Sold
- Average Demand
- Healthy Inventory %
- Number of SKUs
- Monthly Sales Trend
- Weekly Sales Trend
- Top Selling Products
- Inventory Distribution
- Promotion Effectiveness
- Opening vs Closing Stock

---

## 🤖 AI Demand Forecast

Predict future product demand using a trained Random Forest model.

### User Inputs

- SKU
- Promotion
- Holiday
- Opening Stock
- Closing Stock
- Inventory Status
- Month
- Day of Week
- Lag 1
- Lag 7
- Lag 30
- Rolling Mean 7
- Rolling Mean 30

### Output

- Predicted Demand
- Prediction Confidence
- Stock Risk
- Procurement Recommendation

---

## 📦 Inventory Analytics

- Inventory Health
- Healthy Inventory %
- Low Stock %
- Overstock %
- Stockout %

Visualizations include

- Inventory Distribution
- Inventory Health Charts
- Critical Products
- Opening vs Closing Stock

---

## 📈 Business Insights

Automatically generates business insights from historical data.

Includes

- Highest Selling SKU
- Highest Selling Month
- Promotion Lift
- Average Weekly Demand
- Feature Importance
- AI-based Business Recommendations

---

## 📋 Reports

Generate downloadable reports.

- Forecast Report
- Inventory Report
- Business Insights Report

Export options

- CSV
- Excel

---

# 🧠 Machine Learning Model

Model Used

- Random Forest Regressor

Libraries

- Scikit-learn
- Pandas
- NumPy
- Joblib

The trained model predicts future product demand based on engineered historical features.

---

# 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| Dashboard | Streamlit |
| Charts | Plotly |
| Machine Learning | Scikit-learn |
| Data Analysis | Pandas |
| Numerical Computing | NumPy |
| Model Storage | Joblib |
| Version Control | Git & GitHub |

---

# 📂 Project Structure

```
Project-FORESIGHT/
│
├── dashboard/
│   ├── app.py
│   ├── utils.py
│   └── pages/
│       ├── dashboard.py
│       ├── Ai forecast.py
│       ├── inventory.py
│       ├── business insights.py
│       └── reports.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── models/
│   ├── demand_forecasting_model.pkl
│   ├── sku_encoder.pkl
│   └── inventory_encoder.pkl
│
├── notebooks/
│
├── src/
│
├── requirements.txt
│
└── README.md
```

---

# ⚙️ Installation

Clone the repository

```bash
git clone https://github.com/pragnalpragnal-design/Project-FORESIGHT.git
```

Go to project folder

```bash
cd Project-FORESIGHT
```

Create virtual environment

```bash
python -m venv venv
```

Activate environment

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run Streamlit

```bash
cd dashboard
streamlit run app.py
```

---

# 📊 Dataset

The project uses processed retail sales and inventory datasets containing

- Product SKU
- Daily Sales
- Opening Stock
- Closing Stock
- Promotion Information
- Holiday Information
- Inventory Status

Feature engineering creates lag variables and rolling averages for demand prediction.

---

# 🎯 Objectives

- Forecast future product demand
- Reduce stockouts
- Minimize overstocking
- Improve inventory planning
- Support data-driven business decisions

---

# 📸 Dashboard Preview


```
<img width="1366" height="720" alt="Screenshot 2026-07-29 202358" src="https://github.com/user-attachments/assets/10aef5c3-8d30-4a4e-91b9-c77b7d8b1df0" />
<img width="1366" height="720" alt="Screenshot 2026-07-29 202645" src="https://github.com/user-attachments/assets/4440fc98-f854-43e2-b7ef-4ca126e7572e" />
<img width="1366" height="720" alt="Screenshot 2026-07-29 202449" src="https://github.com/user-attachments/assets/a92bc716-9a0b-4c1f-94bf-a06e7893697c" />
<img width="1366" height="720" alt="Screenshot 2026-07-29 202449" src="https://github.com/user-attachments/assets/b4d75b7d-29d1-4ed6-819c-7c32a8de646c" />

```

---

# 🔮 Future Enhancements

- Deep Learning Forecasting
- LSTM Models
- Live Database Integration
- Cloud Deployment
- User Authentication
- Automated Email Reports
- Real-time Inventory Monitoring

---

# 👩‍💻 Developed By

**L Pragna**

B.E. Information Science & Engineering

Project FORESIGHT

---

# 📜 License

This project is developed for educational and internship purposes.

---

# ⭐ Support

If you found this project helpful,

⭐ Star the repository on GitHub.
=======
## 📸 Dashboard Preview

### 🏠 Home
![Home](c:\Users\nikit\OneDrive\Pictures\Screenshots\Screenshot 2026-07-29 202358.png)

---

### 🤖 AI Forecast
![Forecast](c:\Users\nikit\OneDrive\Pictures\Screenshots\Screenshot 2026-07-29 202449.png)

---

### 📦 Inventory Management
![Inventory](c:\Users\nikit\OneDrive\Pictures\Screenshots\Screenshot 2026-07-29 202558.png)

---
>>>>>>> ed06da9 (Update README with dashboard screenshots)
