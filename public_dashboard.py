import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="Public Dog Dashboard", layout="wide")
st.title("🐕 Stray Dog Public Dashboard")

# ----------------------------
# Google Sheets setup
# ----------------------------
SHEET_NAME = "Dog_Counts"
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

def load_google_creds():
    """
    Load Google credentials from Streamlit secrets or local JSON.
    Returns: ServiceAccountCredentials
    """
    # 1️⃣ Try Streamlit secrets first
    if "GOOGLE_CREDS" in st.secrets:
        try:
            raw_creds = st.secrets["GOOGLE_CREDS"].strip()
            creds_dict = json.loads(raw_creds)
            # Fix newlines in private_key
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except json.JSONDecodeError:
            st.error("Failed to decode JSON from Streamlit secrets. Check formatting of GOOGLE_CREDS.")
            st.stop()
        except Exception as e:
            st.error(f"Failed to load credentials from secrets: {e}")
            st.stop()
    
    # 2️⃣ Fallback: local JSON file
    local_path = r"C:\yolo_dashboard\creds.json"  # adjust if needed
    if os.path.exists(local_path):
        try:
            return ServiceAccountCredentials.from_json_keyfile_name(local_path, scope)
        except Exception as e:
            st.error(f"Failed to load credentials from local JSON file: {e}")
            st.stop()

    # 3️⃣ If neither exists, stop
    st.error("Google credentials not found. Add GOOGLE_CREDS to Streamlit secrets or place creds.json locally.")
    st.stop()

# Authorize Google Sheets
creds = load_google_creds()
client = gspread.authorize(creds)

try:
    sheet = client.open(SHEET_NAME).sheet1
except Exception as e:
    st.error(f"Failed to open Google Sheet '{SHEET_NAME}': {e}")
    st.stop()

# ----------------------------
# Fetch data
# ----------------------------
data = sheet.get_all_records()
if not data:
    st.warning("No dog detection data available yet.")
    st.stop()

df = pd.DataFrame(data)
df.columns = [c.strip() for c in df.columns]

# Check required columns
required_cols = ['Timestamp', 'Dog Count']
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' not found in Google Sheet. Please check headers.")
        st.stop()

# Convert Timestamp to datetime
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
df = df.sort_values('Timestamp')

# ----------------------------
# Stats calculations
# ----------------------------
latest_row = df.iloc[-1]
latest_count = latest_row['Dog Count']
latest_time = latest_row['Timestamp']
max_count = df['Dog Count'].max()
total_dogs = df['Dog Count'].sum()

# ----------------------------
# Metrics / Cards
# ----------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("🟢 Total Dogs Counted", total_dogs)
col2.metric("🔵 Current Dog Count", latest_count)
col3.metric("🔴 Max Dogs Detected", max_count)

# Environment status logic
if latest_count == 1:
    env_status = "Safe"
    color = "#ccffcc"
elif latest_count == 3:
    env_status = "Critical"
    color = "#ff6666"
elif latest_count > 3:
    env_status = "Danger"
    color = "#ff0000"
else:
    env_status = "Caution"
    color = "#ffff66"

col4.markdown(f"""
    <div style="padding:15px; background-color:{color}; border-radius:10px; text-align:center;">
        🌿 Environment Status<br>
        <b>{env_status}</b>
    </div>
""", unsafe_allow_html=True)

# ----------------------------
# Alert Detector Card
# ----------------------------
if latest_count >= 1:
    st.markdown(f"""
        <div style="
            padding: 20px;
            background-color: #ffcccc;
            color: #b30000;
            border-radius: 10px;
            font-size: 20px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;">
            ⚠️ Dog Detected – {latest_count} dog(s) at {latest_time.strftime('%Y-%m-%d %H:%M:%S')}
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
            ✅ No dogs detected
        </div>
    """, unsafe_allow_html=True)

# ----------------------------
# Line chart: Dog counts over time
# ----------------------------
st.subheader("📈 Dog Counts Over Time")
chart_df = df[['Timestamp', 'Dog Count']].set_index('Timestamp')
st.line_chart(chart_df)

# ----------------------------
# Optional: Table view
# ----------------------------
with st.expander("📄 Show full log"):
    st.dataframe(df)

# ----------------------------
# Footer
# ----------------------------
st.markdown("<hr><p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets</p>", unsafe_allow_html=True)

