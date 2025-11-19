# search.py
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import datetime
import base64
from io import BytesIO
from PIL import Image

def run():
    st.title("🔍 Search Lost/Unattended Objects")

    # ---- Database Connections ----
    FOG_URI = "mongodb://localhost:27017/"
    CLOUD_URI = "mongodb+srv://9923103056_db_user:3oPkm1uJC0gzANUd@cluster0.imk4fut.mongodb.net/"

    fog_client = MongoClient(FOG_URI)
    cloud_client = MongoClient(CLOUD_URI)

    fog_collection = fog_client["fog_ai_detection"]["events"]
    cloud_collection = cloud_client["Minor_Project1"]["Project1"]   # RAW DATA

    # ---- USER INPUTS ----
    st.subheader("Enter Search Details")

    lost_date = st.date_input("Lost Date (Required)")
    device = st.text_input("Enter Device ID (Optional)")
    object_type = st.text_input("Enter Object Type (Optional)")

    if st.button("Search"):
        if not lost_date:
            st.error("Please provide a date")
            return

        today = datetime.date.today()

        # ============================
        # 1️⃣ Check where to search
        # ============================
        if lost_date == today:
            collection = fog_collection
            st.info("🟢 Searched in *FOG Layer (Local MongoDB)*")
        else:
            collection = cloud_collection
            st.info("☁ Searched in *CLOUD Layer (MongoDB Atlas)*")

        # ============================
        # 2️⃣ Build Query
        # ============================
        query = {}

        # Timestamp filter
        start = datetime.datetime.combine(lost_date, datetime.time.min)
        end = datetime.datetime.combine(lost_date, datetime.time.max)

        query["timestamp"] = {"$gte": start.strftime("%Y-%m-%d %H:%M:%S"),
                              "$lte": end.strftime("%Y-%m-%d %H:%M:%S")}

        if device:
            query["device_id"] = device

        if object_type:
            query["label"] = object_type

        # ============================
        # 3️⃣ Fetch results
        # ============================
        results = list(collection.find(query))

        if not results:
            st.error("No matching data found.")
            return
        else:
            st.success(f"Found {len(results)} matching records")

        # ============================
        # 4️⃣ Display Results
        # ============================
        for item in results:
            st.markdown("---")
            col1, col2 = st.columns([1,1])

            with col1:
                st.write(f"*Device:* {item.get('device_id')}")
                st.write(f"*Object Type:* {item.get('label')}")
                st.write(f"*Object ID:* {item.get('object_id')}")
                st.write(f"*Status:* {item.get('status')}")
                st.write(f"*Detected At:* {item.get('timestamp')}")
                st.write(f"*Saved At:* {item.get('saved_at')}")

            # Display image
            with col2:
                img_b64 = item.get("image_base64")
                if img_b64:
                    try:
                        img_bytes = base64.b64decode(img_b64)
                        img = Image.open(BytesIO(img_bytes))
                        st.image(img, caption=item.get("label"), width=300)
                    except:
                        st.error("Image format error.")
                else:
                    st.warning("No image available.")