import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ============================
# Page Setup
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
# Google Sheets Connection
# ============================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# Load credentials from Streamlit secrets (TOML)
creds_dict = st.secrets["gcp_service_account"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Change this to your exact Google Sheet name
SHEET_NAME = "Dog_Counts"
sheet = client.open(SHEET_NAME).sheet1

# ============================
# Fetch Data
# ============================
data = sheet.get_all_records()

if not data:
    st.warning("No dog detection data available yet.")
    st.stop()

df = pd.DataFrame(data)
df.columns = [c.strip() for c in df.columns]  # clean column names

# ============================
# Validate Columns
# ============================
required_cols = ["Timestamp", "Dog Count"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' not found in Google Sheet. Please check headers.")
        st.stop()

df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp")

# ============================
# Latest Statistics
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
    st.markdown(f"""<div style="
        padding: 20px;
        background-color: #ffe6e6;
        color: #cc0000;
        border-radius: 12px;
        font-size: 24px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;">
        ⚠️ ALERT! {latest_count} dogs detected<br>
        {latest_time.strftime("%Y-%m-%d %H:%M:%S")}
    </div>""", unsafe_allow_html=True)
else:
    st.markdown("""<div style="
        padding: 15px;
        background-color: #e6ffe6;
        color: #006600;
        border-radius: 12px;
        font-size: 20px;
        text-align: center;
        margin-bottom: 20px;">
        ✅ Dogs count normal
    </div>""", unsafe_allow_html=True)

# ============================
# Line Chart
# ============================
st.subheader("📈 Dog Counts Over Time")
chart_df = df[["Timestamp", "Dog Count"]].set_index("Timestamp")
st.line_chart(chart_df)

# ============================
# Full Log Table
# ============================
with st.expander("📄 Show Full Detection Log"):
    st.dataframe(df, use_container_width=True)

# ============================
# Footer
# ============================
st.markdown(
    "<hr>"
    "<p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets | Urban Monitoring Project</p>",
    unsafe_allow_html=True
)
