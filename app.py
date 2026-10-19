
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

# --------------------------------------------------
# Configuration
# --------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent
DETECTOR_FILE = PROJECT_DIR / "hand_test.py"

load_dotenv(PROJECT_DIR / ".env", override=True)

st.set_page_config(
    page_title="GestureBridge AI",
    page_icon="✋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# Styling
# --------------------------------------------------
st.markdown("""
<style>
.stApp {
    background-color: #0b1220;
    color: #edf2f7;
}
[data-testid="stSidebar"] {
    background-color: #111c2e;
}
[data-testid="stSidebar"] * {
    color: #e2e8f0;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}
.hero {
    background: linear-gradient(120deg, #123c42, #172554);
    border: 1px solid #28565d;
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 22px;
}
.hero h1 {
    color: #e6fffb;
    margin-bottom: 6px;
}
.hero p {
    color: #cbdfe8;
    margin-bottom: 0;
}
div[data-testid="stMetric"] {
    background: #131f31;
    border: 1px solid #34465d;
    padding: 17px;
    border-radius: 14px;
}
div[data-testid="stMetricLabel"] {
    color: #cbd5e1 !important;
}
div[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
}
h1, h2, h3, h4, p, label {
    color: #edf2f7;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Session state and detector controls
# --------------------------------------------------
if "detector_process" not in st.session_state:
    st.session_state.detector_process = None


def detector_running():
    process = st.session_state.detector_process
    return process is not None and process.poll() is None


def stop_detector():
    process = st.session_state.detector_process

    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    st.session_state.detector_process = None


# --------------------------------------------------
# MongoDB
# --------------------------------------------------
@st.cache_resource
def get_collection():
    uri = os.getenv("MONGODB_URI")

    if not uri:
        raise ValueError(
            "MONGODB_URI was not found. Check your project .env file."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")

    return client["gesturebridge"]["gesture_history"]


def load_history():
    collection = get_collection()
    records = list(collection.find().sort("_id", -1).limit(200))
    records.reverse()

    for record in records:
        record["_id"] = str(record["_id"])

        for key, value in record.items():
            if isinstance(value, datetime):
                record[key] = value.strftime("%d %b %Y, %I:%M:%S %p")

    return records


# --------------------------------------------------
# Gesture helpers
# --------------------------------------------------
gesture_fields = [
    "gesture",
    "gesture_name",
    "predicted_gesture",
    "label",
    "prediction",
    "detected_gesture",
]

known_gestures = [
    "Thumbs Up",
    "Open Palm",
    "Fist",
    "Peace Sign",
    "OK Sign",
]


def get_gesture(record):
    for field in gesture_fields:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "Unknown"


# --------------------------------------------------
# Sidebar
# --------------------------------------------------
with st.sidebar:
    st.markdown("## ✋ GestureBridge AI")
    st.caption("AI-powered hand gesture recognition")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        ["Overview", "Gesture History", "About Project"],
    )

    st.divider()
    st.caption("SUPPORTED GESTURES")
    st.write("👍 Thumbs Up")
    st.write("✋ Open Palm")
    st.write("✊ Fist")
    st.write("✌️ Peace Sign")
    st.write("👌 OK Sign")

    st.divider()
    st.caption("Built with Python, MediaPipe, OpenCV and MongoDB")


# --------------------------------------------------
# Header
# --------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>GestureBridge AI</h1>
    <p>
        Real-time hand gesture recognition, voice announcements,
        and intelligent gesture history.
    </p>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------
# Load database history
# --------------------------------------------------
records = []
db_error = None

try:
    records = load_history()
except (PyMongoError, ValueError, Exception) as error:
    db_error = str(error)


# Count known gestures
gesture_counts = {name: 0 for name in known_gestures}

for record in records:
    name = get_gesture(record)
    if name in gesture_counts:
        gesture_counts[name] += 1

unique_count = sum(count > 0 for count in gesture_counts.values())
running = detector_running()


# --------------------------------------------------
# Overview
# --------------------------------------------------
if page == "Overview":
    st.subheader("System Overview")
    st.caption("Monitor your detector and saved gesture activity.")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Saved Records", len(records))
    col2.metric("Gesture Types", unique_count)
    col3.metric("Detector", "Running" if running else "Stopped")
    col4.metric("Voice System", "Windows Speech")

    st.divider()
    st.subheader("Live Detector Controls")

    left, right = st.columns([2, 1])

    with left:
        if running:
            st.success("Your existing hand_test.py process is running.")
        else:
            st.info("The webcam detector is currently stopped.")

        st.caption(
            "The webcam opens in its existing OpenCV window. "
            "Keep this dashboard open while using the detector."
        )

        start_col, stop_col = st.columns(2)

        with start_col:
            if st.button(
                "▶ Start Detection",
                type="primary",
                use_container_width=True,
                disabled=running,
            ):
                if not DETECTOR_FILE.exists():
                    st.error("Could not find hand_test.py in the project folder.")
                else:
                    try:
                        process = subprocess.Popen(
                            [sys.executable, str(DETECTOR_FILE)],
                            cwd=str(PROJECT_DIR),
                            creationflags=(
                                subprocess.CREATE_NEW_PROCESS_GROUP
                                if os.name == "nt" else 0
                            ),
                        )
                        st.session_state.detector_process = process
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not start detector: {error}")

        with stop_col:
            if st.button(
                "■ Stop Detection",
                use_container_width=True,
                disabled=not running,
            ):
                stop_detector()
                st.rerun()

    with right:
        st.markdown("### System Components")
        st.write("🟢 MediaPipe hand tracking")
        st.write("🟢 OpenCV webcam")
        st.write("🟢 Windows speech integration")

        if db_error:
            st.write("🔴 MongoDB connection issue")
        else:
            st.write("🟢 MongoDB connected")

    if db_error:
        st.warning(
            "MongoDB history could not be loaded. "
            "Check your .env configuration and connection. "
            f"Details: {db_error}"
        )

    st.divider()
    
    st.subheader("Gesture Distribution")

    chart_data = pd.DataFrame({
        "Gesture": list(gesture_counts.keys()),
        "Saved detections": list(gesture_counts.values()),
    })

    if chart_data["Saved detections"].sum() == 0:
        st.info("No gesture records available yet.")
    else:
        st.bar_chart(
            chart_data,
            x="Gesture",
            y="Saved detections",
            color="#2DD4BF",
        )

        st.markdown("### Gesture Counts")
        count_cols = st.columns(5)

        for col, (gesture, count) in zip(
            count_cols, gesture_counts.items()
        ):
            with col:
                st.metric(gesture, count)


    st.divider()
    st.subheader("Recent Activity")

    if records:
        recent = records[-10:][::-1]

        display_rows = [
            {
                "Gesture": get_gesture(record),
                "Saved record ID": record.get("_id", ""),
            }
            for record in recent
        ]

        st.dataframe(
            pd.DataFrame(display_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No saved gesture records found yet.")

    if st.button("↻ Refresh Dashboard"):
        st.rerun()


# --------------------------------------------------
# Gesture History
# --------------------------------------------------
elif page == "Gesture History":
    st.subheader("Gesture History")
    st.caption("Records retrieved from your existing MongoDB collection.")

    if db_error:
        st.error(f"Could not load MongoDB history: {db_error}")

    elif records:
        history_rows = []

        for record in records[::-1]:
            row = {"Gesture": get_gesture(record)}

            for key, value in record.items():
                if key != "_id":
                    row[key] = value

            history_rows.append(row)

        history_df = pd.DataFrame(history_rows)

        search = st.text_input(
            "Search history",
            placeholder="Search for Peace Sign, Thumbs Up, etc.",
        )

        if search:
            mask = history_df.astype(str).apply(
                lambda column: column.str.contains(
                    search,
                    case=False,
                    na=False,
                )
            ).any(axis=1)

            history_df = history_df[mask]

        st.dataframe(
            history_df,
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download History as CSV",
            data=history_df.to_csv(index=False).encode("utf-8"),
            file_name="gesturebridge_history.csv",
            mime="text/csv",
        )

    else:
        st.info("Your gesture history is empty.")

    if st.button("↻ Refresh History"):
        st.rerun()


# --------------------------------------------------
# About Project
# --------------------------------------------------
elif page == "About Project":
    st.subheader("About GestureBridge AI")

    st.write("""
    GestureBridge AI is a computer-vision prototype that detects
    hand gestures through a webcam and announces recognized gestures
    using Windows speech synthesis.

    The application also stores gesture history in MongoDB so users
    can review previous detections.
    """)

    st.markdown("### Technology Stack")
    st.write("- Python")
    st.write("- MediaPipe hand landmark detection")
    st.write("- OpenCV webcam processing")
    st.write("- Windows System.Speech voice synthesis")
    st.write("- MongoDB Atlas")
    st.write("- Streamlit dashboard")

    st.markdown("### Current Supported Gestures")
    st.write(", ".join(known_gestures))

    st.info(
        "The existing gesture recognition logic remains in hand_test.py. "
        "This dashboard starts that script rather than replacing it."
    )


# --------------------------------------------------
# Footer
# --------------------------------------------------
st.divider()
st.caption("GestureBridge AI · Project Dashboard")
