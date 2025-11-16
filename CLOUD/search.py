# search.py
import streamlit as st
from pymongo import MongoClient
import pandas as pd

def run():
    st.title("🔍 Search Historical Data")

    MONGO_URI = "mongodb+srv://9923103056_db_user:3oPkm1uJC0gzANUd@cluster0.imk4fut.mongodb.net/"
    client = MongoClient(MONGO_URI)
    db = client["Minor_Project1"]
    collection = db["Summarized_Data"]

    device = st.text_input("Enter Device ID")
    object_type = st.text_input("Enter Object Type")

    if st.button("Search"):
        query = {}
        if device:
            query["device_id"] = device
        if object_type:
            query[f"object_summary.{object_type}"] = {"$exists": True}

        results = list(collection.find(query))

        if results:
            st.success(f"Found {len(results)} records")
            st.json(results)
        else:
            st.error("No matching data found.")
