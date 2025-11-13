import pymongo
import base64
import json
import datetime
import os
from collections import defaultdict

# --- MongoDB connections ---
client = pymongo.MongoClient(
    "mongodb+srv://9923103056_db_user:3oPkm1uJC0gzANUd@cluster0.imk4fut.mongodb.net/"
)
cloud_db = client["Minor_Project1"]
cloud_collection = cloud_db["Summarized_Data"]

fog_client = pymongo.MongoClient("mongodb://localhost:27017/")
fog_db = fog_client["fog_ai_detection"]
fog_collection = fog_db["events"]

# --- Helper: encode image as base64 ---
def encode_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except:
        return None

# --- Main summarization ---
def transfer_to_cloud():
    today = datetime.datetime.now()
    week_ago = today - datetime.timedelta(days=7)

    # Fetch last 7 days of events
    recent_events = list(
        fog_collection.find({
            "timestamp": {"$gte": week_ago.strftime("%Y-%m-%d %H:%M:%S")}
        })
    )

    if not recent_events:
        print("⚠️ No events found in last 7 days.")
        return

    # Group by device_id and label
    summary_data = defaultdict(lambda: defaultdict(list))

    for event in recent_events:
        device_id = event.get("device_id", "unknown")
        label = event.get("label", "unknown")
        snapshot_name = event.get("snapshot_name", None)
        summary_data[device_id][label].append(snapshot_name)

    # Prepare summarized records for each device
    for device_id, label_data in summary_data.items():
        summarized_entry = {
            "device_id": device_id,
            "summary_start": week_ago.strftime("%Y-%m-%d"),
            "summary_end": today.strftime("%Y-%m-%d"),
            "archived_at": today.strftime("%Y-%m-%d %H:%M:%S"),
            "object_summary": {},
            "total_objects": 0
        }

        for label, snapshots in label_data.items():
            summarized_entry["object_summary"][label] = {
                "count": len(snapshots),
                "sample_image": None
            }

            # Attach one sample image if available
            if snapshots and snapshots[0]:
                img_path = os.path.join("received_snapshots", snapshots[0])
                summarized_entry["object_summary"][label]["sample_image"] = encode_image(img_path)

            summarized_entry["total_objects"] += len(snapshots)

        # Insert one summarized document per device
        cloud_collection.insert_one(summarized_entry)
        print(f"✅ Summarized data for device '{device_id}' uploaded to MongoDB Atlas.")

    print("🎯 All summaries successfully transferred to cloud.")

if __name__ == "__main__":
    transfer_to_cloud()
