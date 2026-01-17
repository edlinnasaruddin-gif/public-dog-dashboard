import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_autorefresh import st_autorefresh

# ----------------------------
# Auto-refresh every 15 seconds
# ----------------------------
st_autorefresh(interval=5_000, key="refresh")

# ----------------------------
# Page setup
# ----------------------------
st.set_page_config(page_title="🐕 Stray Dog Public Dashboard", layout="wide")
st.title("🐕 Stray Dog Public Dashboard")

# ----------------------------
# Track previous dog count in session state
# ----------------------------
if "prev_dog_count" not in st.session_state:
    st.session_state["prev_dog_count"] = 0

# ----------------------------
# Google Sheets setup
# ----------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = st.secrets["gcp_service_account"]  # JSON service account stored in Streamlit Secrets
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds, scope)
gc = gspread.authorize(credentials)

# Replace with your live Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nDsxO0BV3hBCtn4FhtpXyRnKCGli6qW3oXSeewJZpbE/edit"
sh = gc.open_by_url(SHEET_URL)
worksheet = sh.sheet1

# ----------------------------
# Fetch data
# ----------------------------
data = worksheet.get_all_records()
df = pd.DataFrame(data)

if df.empty:
    st.warning("No dog detection data yet.")
    st.stop()

# ----------------------------
# Clean and process data
# ----------------------------
df.columns = [c.strip() for c in df.columns]
required_cols = ["Timestamp", "Dog Count"]
for col in required_cols:
    if col not in df.columns:
        st.error(f"Column '{col}' missing in sheet")
        st.stop()

df["Timestamp"] = pd.to_datetime(df["Timestamp"])
df = df.sort_values("Timestamp")

latest_count = int(df.iloc[-1]["Dog Count"])
total_dogs = int(df["Dog Count"].sum())
max_count = int(df["Dog Count"].max())

# ----------------------------
# Detect changes for alert
# ----------------------------
dog_count_changed = latest_count != st.session_state["prev_dog_count"]
if dog_count_changed:
    st.session_state["prev_dog_count"] = latest_count

# ----------------------------
# Metrics / Cards
# ----------------------------
col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1.2])
col1.metric("🟢 Total Dogs Counted", total_dogs)
col2.metric("🔵 Current Dog Count", latest_count)
col3.metric("🔴 Max Dogs Detected", max_count)

# Environment status
if latest_count == 1:
    env_status, bg_color = "Caution", "#ffff66"
elif latest_count == 2:
    env_status, bg_color = "Critical", "#ff9999"
elif latest_count >= 3:
    env_status, bg_color = "Danger", "#ff3333"
else:
    env_status, bg_color = "Safe", "#ccffcc"

col4.markdown(f"""
<div style="padding:15px;background-color:{bg_color};border-radius:10px;text-align:center;color:black;">
🌿 Environment Status<br><b>{env_status}</b>
</div>""", unsafe_allow_html=True)

# ----------------------------
# Current time in Malaysia timezone (UTC+8)
# ----------------------------
malaysia_time = datetime.now(timezone.utc) + timedelta(hours=8)
current_time = malaysia_time.strftime("%Y-%m-%d %H:%M:%S")

# Last Updated card
col5.markdown(f"""
<div style="padding:12px;background-color:#f2f2f2;border-radius:10px;text-align:center;font-size:14px;color:#333;">
🕒 Last Updated<br><b>{current_time}</b>
</div>""", unsafe_allow_html=True)

# ----------------------------
# Alert
# ----------------------------
if dog_count_changed and latest_count >= 1:
    st.markdown(f"""
    <div style="padding:20px;background-color:#ff3333;color:white;border-radius:10px;font-size:20px;font-weight:bold;text-align:center;margin-bottom:20px;">
    🚨 {latest_count} dog(s) detected at {current_time}
    </div>
    """, unsafe_allow_html=True)
elif latest_count >= 1:
    st.info(f"🐕 {latest_count} dog(s) detected (no change)")
else:
    st.success("✅ No dogs detected")

# ----------------------------
# Line chart: Dog counts over time
# ----------------------------
st.subheader("📈 Dog Counts Over Time")
st.line_chart(df.set_index("Timestamp")["Dog Count"])

# ----------------------------
# ----------------------------
# Table view (Dog Count ≥ 1) with date filter
# ----------------------------
with st.expander("📄 Show dogs detected (count ≥ 1)"):
    # Date picker (default = latest date in sheet)
    min_date = df['Timestamp'].dt.date.min()
    max_date = df['Timestamp'].dt.date.max()
    default_date = max_date
    selected_date = st.date_input("Select date to view", value=default_date, min_value=min_date, max_value=max_date)

    # Filter dataframe for selected date and dog count ≥ 1
    df_filtered = df[(df['Timestamp'].dt.date == selected_date) & (df['Dog Count'] >= 1)]

    if df_filtered.empty:
        st.info(f"No dog detections on {selected_date}")
    else:
        st.dataframe(df_filtered[['Timestamp', 'Dog Count']], use_container_width=True)


# ----------------------------
# Footer
# ----------------------------
st.markdown("<hr><p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets</p>", unsafe_allow_html=True)




