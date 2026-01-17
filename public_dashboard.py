import streamlit as st
import pandas as pd
from datetime import datetime

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="Public Dog Dashboard", layout="wide")
st.title("🐕 Stray Dog Public Dashboard")

# ----------------------------
# Location info
# ----------------------------
st.subheader("📍 Location: Taman Bunga Raya, Kajang")

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
required_cols = ["Timestamp", "Dog Count"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' not found in the CSV.")
        st.stop()

# Convert Timestamp to datetime
df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp")

# ----------------------------
# Stats calculations
# ----------------------------
latest_row = df.iloc[-1]
latest_count = int(latest_row["Dog Count"])
latest_time = latest_row["Timestamp"]

max_count = int(df["Dog Count"].max())
total_dogs = int(df["Dog Count"].sum())

# ----------------------------
# Metrics / Cards
# ----------------------------
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1.2])

col1.metric("🟢 Total Dogs Counted", total_dogs)
col2.metric("🔵 Current Dog Count", latest_count)
col3.metric("🔴 Max Dogs Detected", max_count)

# Environment status
if latest_count == 1:
    env_status = "Caution"
    bg_color = "#ffff66"
elif latest_count == 3:
    env_status = "Critical"
    bg_color = "#ff9999"
elif latest_count > 3:
    env_status = "Danger"
    bg_color = "#ff3333"
else:
    env_status = "Safe"
    bg_color = "#ccffcc"

col4.markdown(f"""
<div style="
    padding:15px;
    background-color:{bg_color};
    border-radius:10px;
    text-align:center;
    color:black;">
    🌿 Environment Status<br>
    <b>{env_status}</b>
</div>
""", unsafe_allow_html=True)

# ----------------------------
# Last Updated small card
# ----------------------------
col5.markdown(f"""
<div style="
    padding:12px;
    background-color:#f2f2f2;
    border-radius:10px;
    text-align:center;
    font-size:14px;
    color:#333;">
    🕒 Last Updated<br>
    <b>{latest_time.strftime('%Y-%m-%d %H:%M:%S')}</b>
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
        ⚠️ Dog Detected – {latest_count} dog(s)<br>
        ⏱ {latest_time.strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
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
# Line chart
# ----------------------------
st.subheader("📈 Dog Counts Over Time")
chart_df = df[["Timestamp", "Dog Count"]].set_index("Timestamp")
st.line_chart(chart_df)

# ----------------------------
# Table (Dog Count >= 1)
# ----------------------------
with st.expander("📄 Show dogs detected (count ≥ 1)"):
    df_filtered = df[df["Dog Count"] >= 1]
    if df_filtered.empty:
        st.info("No records with Dog Count ≥ 1.")
    else:
        st.dataframe(df_filtered, use_container_width=True)

# ----------------------------
# Footer
# ----------------------------
st.markdown(
    "<hr><p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets CSV</p>",
    unsafe_allow_html=True
)
