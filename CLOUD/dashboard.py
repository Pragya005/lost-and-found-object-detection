# cloud_dashboard.py
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import base64
from io import BytesIO
from PIL import Image
import datetime

# -----------------------------
# MongoDB Atlas Connection
# -----------------------------
MONGO_URI = "mongodb+srv://9923103056_db_user:3oPkm1uJC0gzANUd@cluster0.imk4fut.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["Minor_Project1"]
collection = db["Summarized_Data"]

# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(page_title="AI Lost & Found Dashboard", layout="wide")
st.title("📊 AI Lost & Found Object Detection - Cloud Dashboard")

# -----------------------------
# Load Data
# -----------------------------
data = list(collection.find())
if not data:
    st.warning("No data found in MongoDB Atlas yet.")
    st.stop()

# Convert data into DataFrame
records = []
for doc in data:
    # Skip documents missing object_summary
    if "object_summary" not in doc or not isinstance(doc["object_summary"], dict):
        continue

    for label, obj_info in doc["object_summary"].items():
        count = obj_info.get("count", 0)
        sample_image = obj_info.get("sample_image", None)

        records.append({
            "device_id": doc.get("device_id", "unknown"),
            "label": label,
            "count": count,
            "archived_at": doc.get("archived_at", ""),
            "summary_start": doc.get("summary_start", ""),
            "summary_end": doc.get("summary_end", ""),
            "sample_image": sample_image
        })

df = pd.DataFrame(records)

# -----------------------------
# Summary Section
# -----------------------------
st.subheader("📅 Summary Overview")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Devices", len(df["device_id"].unique()))
with col2:
    st.metric("Total Object Types", len(df["label"].unique()))
with col3:
    st.metric("Total Objects", int(df["count"].sum()))

st.divider()

# -----------------------------
# Device Summary
# -----------------------------
st.subheader("🧩 Device-wise Summary")
device_summary = df.groupby("device_id")["count"].sum().reset_index()
fig1 = px.bar(device_summary, x="device_id", y="count",
              title="Objects Detected per Device", color="device_id", text_auto=True)
st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# Object Summary
# -----------------------------
st.subheader("🧳 Object Type Summary")
obj_summary = df.groupby("label")["count"].sum().reset_index()
fig2 = px.pie(obj_summary, names="label", values="count", title="Distribution of Object Types")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Trend Analysis (Over Time)
# -----------------------------
st.subheader("📈 Detection Trend Over Time")
df["archived_at"] = pd.to_datetime(df["archived_at"])
trend_df = df.groupby(df["archived_at"].dt.date)["count"].sum().reset_index()
fig3 = px.line(trend_df, x="archived_at", y="count", markers=True,
               title="Total Detections Over Time")
st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# Image Gallery
# -----------------------------
# st.subheader("🖼️ Sample Images from Summaries")
# for _, row in df.iterrows():
#     if row["sample_image"]:
#         try:
#             img_data = base64.b64decode(row["sample_image"])
#             img = Image.open(BytesIO(img_data))
#             st.image(img, caption=f"{row['label']} (Device: {row['device_id']})", width=250)
#         except Exception:
#             st.info(f"No valid image for {row['label']} from {row['device_id']}.")
#     else:
#         st.info(f"No image available for {row['label']} from {row['device_id']}.")

# -----------------------------
# Export Option
# -----------------------------
st.subheader("💾 Export Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download Summary as CSV", csv, "summary_export.csv", "text/csv")

st.caption("Dashboard auto-refreshes with new summarized data from MongoDB Atlas.")
