import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="Public Dog Dashboard", layout="wide")
st.title("🐕 Stray Dog Public Dashboard")

# ----------------------------
# Google Sheets setup
# ----------------------------
GOOGLE_SHEET_CREDS = r"C:\yolo_dashboard\creds.json"  # Update path
SHEET_NAME = "Dog_Counts"

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEET_CREDS, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# ----------------------------
# Fetch data
# ----------------------------
data = sheet.get_all_records()
if not data:
    st.warning("No dog detection data available yet.")
    st.stop()

df = pd.DataFrame(data)

# Clean column names (remove spaces)
df.columns = [c.strip() for c in df.columns]

# Check for required columns
required_cols = ['Timestamp', 'Dog Count']
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' not found in Google Sheet. Please check headers.")
        st.stop()

# Convert Timestamp to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df = df.sort_values('Timestamp')

# ----------------------------
# Latest stats
# ----------------------------
latest_row = df.iloc[-1]
latest_count = latest_row['Dog Count']
latest_time = latest_row['Timestamp']
max_count = df['Dog Count'].max()

# ----------------------------
# Metrics / Cards
# ----------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Current Dog Count", latest_count)
col2.metric("Max Dogs Detected", max_count)
col3.metric("Last Detection Time", latest_time.strftime("%Y-%m-%d %H:%M:%S"))

# ----------------------------
# Alert card
# ----------------------------
if latest_count > 2:
    st.markdown(f"""
        <div style="
            padding: 20px;
            background-color: #ffcccc;
            color: #b30000;
            border-radius: 10px;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;">
            ⚠️ ALERT! {latest_count} dogs detected at {latest_time.strftime("%Y-%m-%d %H:%M:%S")}
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div style="
            padding: 15px;
            background-color: #ccffcc;
            color: #006600;
            border-radius: 10px;
            font-size: 20px;
            text-align: center;
            margin-bottom: 20px;">
            ✅ Dogs count normal
        </div>
    """, unsafe_allow_html=True)

# ----------------------------
# Line chart
# ----------------------------
st.subheader("Dog Counts Over Time")
chart_df = df[['Timestamp', 'Dog Count']].set_index('Timestamp')
st.line_chart(chart_df)

# ----------------------------
# Optional: Table view
# ----------------------------
with st.expander("Show full log"):
    st.dataframe(df)

# ----------------------------
# Footer
# ----------------------------
st.markdown("<hr><p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets</p>", unsafe_allow_html=True)
