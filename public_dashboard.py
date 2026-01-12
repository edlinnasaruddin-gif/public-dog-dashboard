import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ============================
# Page setup
# ============================
st.set_page_config(
    page_title="Public Dog Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    "<h1 style='text-align:center;'>🐕 Stray Dog Public Dashboard</h1>"
    "<h4 style='text-align:center;color:gray;'>Real-time monitoring of urban dog counts</h4>",
    unsafe_allow_html=True
)

# ============================
# Auto-refresh every 30 seconds
# ============================
st_autorefresh = st.experimental_rerun  # Streamlit built-in simple rerun
# Optional: use streamlit_autorefresh package for more control

# ============================
# Google Sheets connection (Streamlit Cloud SAFE)
# ============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Load credentials from Streamlit Secrets
creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)

client = gspread.authorize(creds)

# 🔴 CHANGE THIS to your exact Google Sheet name
SHEET_NAME = "Dog_Counts"
sheet = client.open(SHEET_NAME).sheet1

# ============================
# Fetch data from Google Sheets
# ============================
data = sheet.get_all_records()

if not data:
    st.warning("No dog detection data available yet.")
    st.stop()

df = pd.DataFrame(data)
df.columns = [c.strip() for c in df.columns]

# ============================
# Validate required columns
# ============================
required_cols = ["Timestamp", "Dog Count"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' not found in Google Sheet. Please check headers.")
        st.stop()

# Convert timestamp and sort
df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp")

# ============================
# Latest statistics
# ============================
latest_row = df.iloc[-1]
latest_count = latest_row["Dog Count"]
latest_time = latest_row["Timestamp"]
max_count = df["Dog Count"].max()

# ============================
# Metrics / Cards
# ============================
st.markdown("### 📊 Current Dog Detection Stats")
col1, col2, col3 = st.columns(3)
col1.metric("Current Dog Count", latest_count)
col2.metric("Max Dogs Detected", max_count)
col3.metric("Last Detection Time", latest_time.strftime("%Y-%m-%d %H:%M:%S"))

# ============================
# Alert Card
# ============================
if latest_count > 2:
    st.markdown(
        f"""
        <di

