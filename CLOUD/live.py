import streamlit as st
import requests
from PIL import Image
from gtts import gTTS
import os
import base64
import time
import streamlit.components.v1 as components

API_URL = "http://localhost:5000"

# --------------------------------------------------
# 1-second REAL MP3 silence (guaranteed valid)
# --------------------------------------------------
ONE_SECOND_SILENCE = (
    "SUQzAwAAAAAAQ1RTU0UAAAAPAAADTGF2ZjU2LjEwMAAAAAAAAAAAAAAA//uQxAADB8gACuAAAAgAAAABAAgAZGF0YQAAAAA="
)

# --------------------------------------------------
# Build final alert audio: silence + speech
# --------------------------------------------------
def create_final_audio(message, final_file):
    silent_bytes = base64.b64decode(ONE_SECOND_SILENCE)

    speech_file = "speech.mp3"
    gTTS(message, lang="en").save(speech_file)

    with open(speech_file, "rb") as f:
        speech_bytes = f.read()

    with open(final_file, "wb") as out:
        out.write(silent_bytes + speech_bytes)

    os.remove(speech_file)

# --------------------------------------------------
# Play audio (Chrome-safe)
# --------------------------------------------------
def play_audio_hidden(file_path):
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    encoded = base64.b64encode(audio_bytes).decode()

    audio_html = f"""
    <audio autoplay style="opacity:0; width:0px; height:0px;">
        <source src="data:audio/mp3;base64,{encoded}" type="audio/mp3">
    </audio>
    """
    components.html(audio_html, height=0)

# --------------------------------------------------
# MAIN PAGE
# --------------------------------------------------
def run():

    # Track new vs old objects
    if "last_ids" not in st.session_state:
        st.session_state["last_ids"] = set()

    if "initialized" not in st.session_state:
        st.session_state["initialized"] = False

    # PAGE TITLE
    st.markdown(
        "<h1 style='font-size:40px; font-weight:700;'>Live Lost & Found Detections</h1>",
        unsafe_allow_html=True,
    )

    # --------------------------------------------------
    # TOP MANUAL REFRESH BUTTON
    # --------------------------------------------------
    c1, c2 = st.columns([0.8, 0.2])
    with c2:
        if st.button("🔄 Refresh"):
            st.rerun()

    # --------------------------------------------------
    # Fetch API Data
    # --------------------------------------------------
    def fetch_events():
        try:
            r = requests.get(f"{API_URL}/api/detections")
            return r.json()
        except:
            return []

    events = fetch_events()

    if not events:
        st.warning("No events found.")
        return

    # First load: store IDs but do NOT alert
    if not st.session_state["initialized"]:
        st.session_state["last_ids"] = {e["_id"] for e in events}
        st.session_state["initialized"] = True

    # --------------------------------------------------
    # Show all events
    # --------------------------------------------------
    for item in events:
        st.markdown("<hr>", unsafe_allow_html=True)

        left, right = st.columns([4, 1])

        with left:
            st.markdown(
                f"<h2 style='margin-bottom:5px; font-weight:700;'>{item['label']}</h2>",
                unsafe_allow_html=True,
            )

        with right:
            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns([1.5, 1])

        with c1:
            st.write(f"**Device:** {item['device_id']}")
            st.write(f"**Object ID:** {item['object_id']}")
            st.write(f"**Detected At:** {item['timestamp']}")
            st.write(f"**Saved At:** {item['saved_at']}")

        with c2:
            img_path = item["image_path"]
            if os.path.exists(img_path):
                st.image(Image.open(img_path), width=350)
            else:
                st.error("Image not found.")

    # --------------------------------------------------
    # NEW EVENT DETECTION
    # --------------------------------------------------
    current_ids = {e["_id"] for e in events}
    new_ids = current_ids - st.session_state["last_ids"]

    if new_ids:
        for item in events:
            if item["_id"] in new_ids:

                label = item["label"]
                loc = item["device_id"]

                message = f"Attention, a {label} is found unattended at {loc}."

                # build audio
                final_mp3 = "alert.mp3"
                create_final_audio(message, final_mp3)

                # play audio
                play_audio_hidden(final_mp3)

        time.sleep(3)

        # update last seen IDs
        st.session_state["last_ids"] = current_ids

        # refresh UI only when new objects arrive
        st.rerun()

    # --------------------------------------------------
    # NO AUTO REFRESH → PAGE STAYS STILL
    # --------------------------------------------------
