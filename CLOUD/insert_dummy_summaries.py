# insert_dummy_summaries.py
import pymongo, base64, os, datetime, json

# ---------- CONFIG ----------
MONGO_URI = "mongodb+srv://9923103056_db_user:3oPkm1uJC0gzANUd@cluster0.imk4fut.mongodb.net/"
DB_NAME = "Minor_Project1"
COLLECTION = "Summarized_Data"

# Optional: folder with sample images (png/jpg). If empty, sample_image will be None.
SAMPLE_IMG_DIR = "sample_images"  # create and drop 1-2 images here or leave empty
# ----------------------------

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]
col = db[COLLECTION]

def encode_image_if_exists(filename):
    if not filename:
        return None
    p = os.path.join(SAMPLE_IMG_DIR, filename)
    if not os.path.exists(p):
        return None
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# Create a few sample documents (per device + per object)
now = datetime.datetime.utcnow()
start = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
end = now.strftime("%Y-%m-%d")
archived_at = now.strftime("%Y-%m-%d %H:%M:%S")

# Example dummy summaries - edit labels or counts as you want
dummy_docs = [
    {
        "device_id": "LAPTOP-S8IESMCT",
        "summary_start": start,
        "summary_end": end,
        "archived_at": archived_at,
        "object_summary": {
            "cell phone": {"count": 3, "sample_image": encode_image_if_exists("phone1.jpg")},
            "backpack": {"count": 1, "sample_image": encode_image_if_exists("backpack1.jpg")}
        },
        "total_objects": 4
    },
    {
        "device_id": "edge_cam_02",
        "summary_start": start,
        "summary_end": end,
        "archived_at": archived_at,
        "object_summary": {
            "laptop": {"count": 2, "sample_image": encode_image_if_exists("laptop1.jpg")},
            "cell phone": {"count": 1, "sample_image": encode_image_if_exists("phone2.jpg")}
        },
        "total_objects": 3
    },
    {
        "device_id": "edge_cam_03",
        "summary_start": start,
        "summary_end": end,
        "archived_at": archived_at,
        "object_summary": {
            "backpack": {"count": 5, "sample_image": None},
            "bottle": {"count": 2, "sample_image": None}
        },
        "total_objects": 7
    }
]

# Insert docs
res = col.insert_many(dummy_docs)
print(f"Inserted {len(res.inserted_ids)} dummy summary docs into {DB_NAME}.{COLLECTION}")
print("Inserted IDs:", res.inserted_ids)
