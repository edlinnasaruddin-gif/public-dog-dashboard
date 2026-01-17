import streamlit as st
import pandas as pd
from datetime import datetime
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="Public Dog Dashboard", layout="wide")
st.title("🐕 Stray Dog Public Dashboard")

# ----------------------------
# Auto-refresh every 15 seconds (built-in)
# ----------------------------
if "last_refresh" not in st.session_state:
    st.session_state["last_refresh"] = time.time()

if time.time() - st.session_state["last_refresh"] >= 15:
    st.session_state["last_refresh"] = time.time()
    st.rerun()

# ----------------------------
# Session state for alert-on-change
# ----------------------------
if "prev_dog_count" not in st.session_state:
    st.session_state["prev_dog_count"] = None

# ----------------------------
# Google Sheets setup
# ----------------------------
# Scope and credentials
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = st.secrets["gcp_service_account"]  # See step 4 below
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)

gc = gspread.authorize(credentials)

# Open the sheet by name or URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nDsxO0BV3hBCtn4FhtpXyRnKCGli6qW3oXSeewJZpbE/edit?gid=0#gid=0"
sh = gc.open_by_url(https://docs.google.com/spreadsheets/d/1nDsxO0BV3hBCtn4FhtpXyRnKCGli6qW3oXSeewJZpbE/edit?gid=0)
worksheet = sh.sheet1  # or by name: sh.worksheet("Sheet1")

# Fetch all data
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# ----------------------------
# Process data
# ----------------------------
if df.empty:
    st.warning("No dog detection data yet.")
    st.stop()

df.columns = [c.strip() for c in df.columns]
required_cols = ["Timestamp", "Dog Count"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' missing in sheet")
        st.stop()

df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp")

# ----------------------------
# Stats calculations
# ----------------------------
latest_row = df.iloc[-1]
latest_count = int(latest_row["Dog Count"])
latest_time = latest_row["Timestamp"]
total_dogs = int(df["Dog Count"].sum())
max_count = int(df["Dog Count"].max())

# ----------------------------
# Detect changes
# ----------------------------
dog_count_changed = False
if st.session_state["prev_dog_count"] is None:
    st.session_state["prev_dog_count"] = latest_count
elif latest_count != st.session_state["prev_dog_count"]:
    dog_count_changed = True
    st.session_state["prev_dog_count"] = latest_count

# ----------------------------
# Metrics / Cards
# ----------------------------
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1.2])
col1.metric("🟢 Total Dogs Counted", total_dogs)
col2.metric("🔵 Current Dog Count", latest_count)
col3.metric("🔴 Max Dogs Detected", max_count)

# Environment Status
if latest_count == 1:
    env_status, bg_color = "Caution", "#ffff66"
elif latest_count == 3:
    env_status, bg_color = "Critical", "#ff9999"
elif latest_count > 3:
    env_status, bg_color = "Danger", "#ff3333"
else:
    env_status, bg_color = "Safe", "#ccffcc"

col4.markdown(f"""
<div style="padding:15px;background-color:{bg_color};border-radius:10px;text-align:center;color:black;">
🌿 Environment Status<br><b>{env_status}</b>
</div>""", unsafe_allow_html=True)

col5.markdown(f"""
<div style="padding:12px;background-color:#f2f2f2;border-radius:10px;text-align:center;font-size:14px;color:#333;">
🕒 Last Updated<br><b>{latest_time.strftime('%Y-%m-%d %H:%M:%S')}</b>
</div>""", unsafe_allow_html=True)

# ----------------------------
# Alert
# ----------------------------
if dog_count_changed and latest_count >= 1:
    st.markdown(f"""
    <div style="padding:20px;background-color:#ff3333;color:white;border-radius:10px;font-size:20px;font-weight:bold;text-align:center;margin-bottom:20px;">
    🚨 DOG COUNT CHANGED! – {latest_count} dog(s)<br>⏱ {latest_time.strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)
elif latest_count >= 1:
    st.info(f"🐕 {latest_count} dog(s) detected (no change)")
else:
    st.success("✅ No dogs detected")

# ----------------------------
# Line chart
# ----------------------------
st.subheader("📈 Dog Counts Over Time")
st.line_chart(df.set_index("Timestamp")["Dog Count"])

# ----------------------------
# Table view
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
st.markdown("<hr><p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets</p>", unsafe_allow_html=True)


