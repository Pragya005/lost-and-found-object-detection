import streamlit as st
import requests
from PIL import Image
from gtts import gTTS
import os
import base64
import time

API_URL = "http://localhost:5000"


# --------------------------------------------------
# Hidden autoplay audio
# --------------------------------------------------
def play_audio_hidden(file_path):
    with open(file_path, "rb") as f:
        audio_bytes = f.read()

    b64 = base64.b64encode(audio_bytes).decode()

    audio_html = f"""
        <audio autoplay hidden>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)



def run():

    # Initialize session variables
    if "last_ids" not in st.session_state:
        st.session_state["last_ids"] = set()

    if "initialized" not in st.session_state:
        st.session_state["initialized"] = False

    st.markdown(
        "<h1 style='font-size:40px; font-weight:700;'>Live Lost & Found Detections</h1>",
        unsafe_allow_html=True
    )

    # Fetch data function
    def fetch_events():
        try:
            res = requests.get(f"{API_URL}/api/detections")
            return res.json()
        except:
            return []

    # Update collected
    def update_collected(id, new_value):
        try:
            requests.post(
                f"{API_URL}/api/update_collected/{id}",
                json={"collected": new_value}
            )
        except:
            pass

    # FIRST RUN - show the page normally
    events = fetch_events()

    if not events:
        st.warning("No events found.")
        return

    # On first load: set last_ids, do NOT alert
    if not st.session_state["initialized"]:
        st.session_state["last_ids"] = {item["_id"] for item in events}
        st.session_state["initialized"] = True

    # Display all events normally
    for item in events:
        st.markdown("<hr>", unsafe_allow_html=True)

        header_left, header_right = st.columns([4, 1])

        with header_left:
            st.markdown(
                f"<h2 style='margin-bottom:5px; font-weight:700;'>{item['label']}</h2>",
                unsafe_allow_html=True
            )

        with header_right:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            st.checkbox(
                "Collected",
                value=item.get("collected", False),
                key=item["_id"],
                on_change=update_collected,
                args=(item["_id"], not item.get("collected", False))
            )

        left, right = st.columns([1.5, 1])

        with left:
            st.write(f"**Device:** {item['device_id']}")
            st.write(f"**Object ID:** {item['object_id']}")
            st.write(f"**Detected At:** {item['timestamp']}")
            st.write(f"**Saved At:** {item['saved_at']}")

        with right:
            img_path = item["image_path"]
            if os.path.exists(img_path):
                img = Image.open(img_path)
                st.image(img, width=350)
            else:
                st.error("Image not found.")

    # --------------------------------------------------
    # POLLING LOOP (runs only when Live page is open)
    #---------------------------------------------------
    while True:

        time.sleep(1)  # poll every second
        new_events = fetch_events()

        if not new_events:
            continue

        current_ids = {item["_id"] for item in new_events}
        new_ids = current_ids - st.session_state["last_ids"]

        if new_ids:
            # Alert & rerun
            for item in new_events:
                if item["_id"] in new_ids:

                    label = item.get("label", "object")
                    location = item.get("device_id", "unknown")

                    text = f"Attention! A {label} is found unattended at {location}"

                    tts = gTTS(text=text, lang="en")
                    audio_file = "alert.mp3"
                    tts.save(audio_file)

                    play_audio_hidden(audio_file)

            time.sleep(3)
            
            st.session_state["last_ids"] = current_ids
            st.rerun()  # refresh ONLY when new object arrives
