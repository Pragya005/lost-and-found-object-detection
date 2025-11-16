# live.py
import streamlit as st
import requests
from PIL import Image
import os
import time


def run():
    st.title("📡 Live Monitoring")
    # st.info("This page will show live events from Fog → Cloud (Future Enhancement).")
    API_URL = "http://localhost:5000"

    st.set_page_config(page_title="Lost & Found Dashboard", layout="wide")

    # PAGE TITLE
    st.markdown(
        "<h1 style='font-size:40px; font-weight:700;'>Live Lost & Found Detections</h1>",
        unsafe_allow_html=True
    )

    # Fetch data from API
    def fetch_events():
        try:
            res = requests.get(f"{API_URL}/api/detections")
            return res.json()
        except:
            return []

    # Update collected in backend
    def update_collected(id, new_value):
        try:
            requests.post(
                f"{API_URL}/api/update_collected/{id}",
                json={"collected": new_value}
            )
        except:
            pass

    # MAIN LOOP
    events = fetch_events()

    for item in events:
        st.markdown("<hr>", unsafe_allow_html=True)

        # HEADER: Title (left), Checkbox (right)
        header_left, header_right = st.columns([4, 1])

        # TITLE
        with header_left:
            st.markdown(
                f"<h2 style='margin-bottom:5px; font-weight:700;'>{item['label']}</h2>",
                unsafe_allow_html=True
            )

        # CHECKBOX ON RIGHT
        with header_right:
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)  # small spacing
            st.checkbox(
                "Collected",
                value=item.get("collected", False),
                key=item["_id"],
                on_change=update_collected,
                args=(item["_id"], not item.get("collected", False))
            )

        # CONTENT: Details on left, Image on right
        left, right = st.columns([1.5, 1])

        with left:
            st.markdown(
                f"<p style='font-size:18px;'><b>Device:</b> {item['device_id']}</p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='font-size:18px;'><b>Object ID:</b> {item['object_id']}</p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='font-size:18px;'><b>Detected At:</b> {item['timestamp']}</p>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<p style='font-size:18px;'><b>Saved At:</b> {item['saved_at']}</p>",
                unsafe_allow_html=True,
            )

        with right:
            img_path = item["image_path"]
            if os.path.exists(img_path):
                img = Image.open(img_path)
                st.image(img, width=350)
            else:
                st.error("Image not found.")

    # AUTO REFRESH EVERY 2 SECONDS
    time.sleep(2)
    st.rerun()



