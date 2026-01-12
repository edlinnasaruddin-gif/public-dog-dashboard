import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="Public Dog Dashboard", layout="wide")
st.title("🐕 Stray Dog Public Dashboard")

# ----------------------------
# Public Google Sheet CSV URL
# ----------------------------
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTbucEZqgl9vWZJHSQFb1tpk2VVWRyPrxfxbRQ224TMzPbONeGVPEhTgQl9bGVstZOVc07T5nqDHIEV/pub?output=csv"

# ----------------------------
# Fetch data
# ----------------------------
try:
    df = pd.read_csv(CSV_URL)
except Exception as e:
    st.error(f"Failed to load data from public CSV: {e}")
    st.stop()

if df.empty:
    st.warning("No dog detection data available yet.")
    st.stop()

# Clean column names
df.columns = [c.strip() for c in df.columns]

# Check required columns
required_cols = ['Timestamp', 'Dog Count']
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' not found in the CSV. Please check headers.")
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
# Optional: Table view (only Dog Count > 1)
# ----------------------------
with st.expander("📄 Show dogs detected (count >= 1)"):
    df_filtered = df[df['Dog Count'] >= 1]
    if df_filtered.empty:
        st.info("No records with Dog Count > 1.")
    else:
        st.dataframe(df_filtered)

# ----------------------------
# Footer
# ----------------------------
st.markdown("<hr><p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets CSV</p>", unsafe_allow_html=True)

