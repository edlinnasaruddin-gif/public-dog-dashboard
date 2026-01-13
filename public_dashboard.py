import streamlit as st
import cv2
from ultralytics import YOLO
from datetime import datetime
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import tempfile

# ============================
# PAGE SETUP
# ============================
st.set_page_config(page_title="Stray Dog Detection & Public Dashboard", layout="wide")
st.title("🐕 Stray Dog Detection & Public Dashboard")

# ============================
# GOOGLE SHEETS SETUP
# ============================
GOOGLE_SHEET_CREDS = r"C:\yolo_dashboard\creds.json"
SHEET_NAME = "Dog_Counts"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEET_CREDS, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

def save_to_sheets(timestamp, count, source):
    try:
        sheet.append_row([timestamp, count, source])
    except Exception as e:
        st.error(f"Google Sheets error: {e}")

# ============================
# LAYOUT: LEFT = LIVE DETECTION, RIGHT = PUBLIC DASHBOARD
# ============================
left_col, right_col = st.columns([2, 1])

# ============================
# LEFT COLUMN: LIVE DETECTION
# ============================
with left_col:
    st.header("🎥 Live Detection")

    # Load YOLO
    model = YOLO("best.pt")
    st.write("Model classes:", model.names)

    # Video source
    source = st.radio("Select video source:", ["Live Webcam", "Upload CCTV Video"])
    if source == "Upload CCTV Video":
        video_file = st.file_uploader("Upload CCTV video", type=["mp4", "avi", "mov"])
        if video_file is None:
            st.stop()
        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(video_file.read())
        cap = cv2.VideoCapture(tfile.name)
    else:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            st.error("Cannot access webcam")
            st.stop()

    # Placeholders
    frame_window = st.empty()
    col1, col2, col3 = st.columns(3)
    current_metric = col1.metric("Current Dog Count", 0)
    max_metric = col2.metric("Max Dogs Detected", 0)
    time_metric = col3.metric("Last Detection Time", "N/A")
    chart_placeholder = st.empty()
    stop_btn = st.button("Stop Detection")

    # Session state
    st.session_state.setdefault("max_dogs", 0)
    st.session_state.setdefault("last_saved", -1)
    dog_log = []

    # Detection loop
    frame_skip = 2
    frame_id = 0
    while cap.isOpened():
        if stop_btn:
            break
        ret, frame = cap.read()
        if not ret:
            break
        frame_id += 1
        if frame_id % frame_skip != 0:
            continue

        # YOLO inference
        result = model(frame, conf=0.4)[0]
        dog_boxes = [box for box in result.boxes if "dog" in model.names[int(box.cls[0])].lower()]
        current_dog_count = len(dog_boxes)

        # Update max
        if current_dog_count > st.session_state.max_dogs:
            st.session_state.max_dogs = current_dog_count

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dog_log.append((timestamp, current_dog_count))

        # Update Google Sheets
        if current_dog_count != st.session_state.last_saved:
            save_to_sheets(timestamp, current_dog_count, source)
            st.session_state.last_saved = current_dog_count

        # Display annotated frame
        annotated = result.plot()
        frame_window.image(annotated, channels="BGR")

        # Update metrics
        current_metric.metric("Current Dog Count", current_dog_count)
        max_metric.metric("Max Dogs Detected", st.session_state.max_dogs)
        time_metric.metric("Last Detection Time", timestamp)

        # Chart
        df_chart = pd.DataFrame(dog_log, columns=["Time", "Dog Count"]).set_index("Time")
        chart_placeholder.line_chart(df_chart)

    cap.release()
    st.success("Detection stopped")

# ============================
# RIGHT COLUMN: PUBLIC DASHBOARD
# ============================
with right_col:
    st.header("📊 Public Dashboard")

    # Public Google Sheet CSV URL (same sheet)
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{sheet.spreadsheet.id}/gviz/tq?tqx=out:csv&sheet={sheet.title}"

    try:
        df = pd.read_csv(CSV_URL)
    except Exception as e:
        st.error(f"Failed to load public data: {e}")
        st.stop()

    if df.empty:
        st.warning("No dog detection data available yet.")
        st.stop()

    df.columns = [c.strip() for c in df.columns]
    required_cols = ['Timestamp', 'Dog Count']
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Column '{col}' not found in the CSV.")
            st.stop()

    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df = df.sort_values('Timestamp')

    latest_row = df.iloc[-1]
    latest_count = latest_row['Dog Count']
    latest_time = latest_row['Timestamp']
    max_count = df['Dog Count'].max()
    total_dogs = df['Dog Count'].sum()

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 Total Dogs Counted", total_dogs)
    col2.metric("🔵 Current Dog Count", latest_count)
    col3.metric("🔴 Max Dogs Detected", max_count)

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

    # Alert card
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

    # Line chart
    st.subheader("📈 Dog Counts Over Time")
    chart_df = df[['Timestamp', 'Dog Count']].set_index('Timestamp')
    st.line_chart(chart_df)

    # Table
    with st.expander("📄 Show dogs detected (count >= 1)"):
        df_filtered = df[df['Dog Count'] >= 1]
        if df_filtered.empty:
            st.info("No records with Dog Count > 1.")
        else:
            st.dataframe(df_filtered)

    st.markdown("<hr><p style='text-align:center;color:gray;'>Powered by Streamlit & Google Sheets CSV</p>", unsafe_allow_html=True)

