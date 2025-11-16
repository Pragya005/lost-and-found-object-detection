# cloud_dashboard.py
import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import datetime
import requests
import time

def run():
    st.title("📊 AI Lost & Found - Cloud Dashboard")

    # MongoDB Atlas Connection
    MONGO_URI = "mongodb+srv://9923103056_db_user:3oPkm1uJC0gzANUd@cluster0.imk4fut.mongodb.net/"
    client = MongoClient(MONGO_URI)
    db = client["Minor_Project1"]
    collection = db["Summarized_Data"]

    # Load Data
    data = list(collection.find())
    if not data:
        st.warning("No data found in MongoDB Atlas yet.")
        return

    # Convert data into DataFrame
    records = []
    for doc in data:
        if "object_summary" not in doc or not isinstance(doc["object_summary"], dict):
            continue

        for label, obj_info in doc["object_summary"].items():
            records.append({
                "device_id": doc.get("device_id", "unknown"),
                "label": label,
                "count": obj_info.get("count", 0),
                "archived_at": doc.get("archived_at", ""),
                "summary_start": doc.get("summary_start", ""),
                "summary_end": doc.get("summary_end", "")
            })

    df = pd.DataFrame(records)

    # Summary Overview
    st.subheader("📅 Summary Overview")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Devices", len(df["device_id"].unique()))
    col2.metric("Total Object Types", len(df["label"].unique()))
    col3.metric("Total Objects", int(df["count"].sum()))

    st.divider()

    # Device Summary
    st.subheader("🧩 Device-wise Summary")
    device_summary = df.groupby("device_id")["count"].sum().reset_index()
    fig1 = px.bar(device_summary, x="device_id", y="count",
                  title="Objects Detected per Device", color="device_id", text_auto=True)
    st.plotly_chart(fig1, use_container_width=True)

    # Object Summary
    st.subheader("🧳 Object Type Summary")
    obj_summary = df.groupby("label")["count"].sum().reset_index()
    fig2 = px.pie(obj_summary, names="label", values="count", title="Distribution of Object Types")
    st.plotly_chart(fig2, use_container_width=True)

    # Trend Analysis
    st.subheader("📈 Detection Trend Over Time")
    df["archived_at"] = pd.to_datetime(df["archived_at"])
    trend_df = df.groupby(df["archived_at"].dt.date)["count"].sum().reset_index()
    fig3 = px.line(trend_df, x="archived_at", y="count", markers=True,
                   title="Total Detections Over Time")
    st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------
    # Sync Button (Fog → Cloud)
    # -----------------------------
    st.subheader("🔄 Sync Raw Data")

    if st.button("Sync Now"):
        try:
            with st.spinner("Syncing raw data from Fog Node to Cloud..."):
                response = requests.post("http://localhost:8000/sync")

            if response.status_code == 200:
                st.success("✅ Raw data synced successfully!")
            else:
                st.error("❌ Sync failed! Check FastAPI sync service.")
        except Exception as e:
            st.error(f"❌ Could not reach sync service. Error: {e}")

    # Export option
    st.subheader("💾 Export Data")
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download Summary as CSV", csv, "summary_export.csv", "text/csv")
