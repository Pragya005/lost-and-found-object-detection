from fastapi import FastAPI, BackgroundTasks
from pymongo import MongoClient, UpdateOne
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import uvicorn

# ==== CONFIGURATION ====
LOCAL_URI = "mongodb://localhost:27017"
LOCAL_DB_NAME = "fog_ai_detection"
LOCAL_COLLECTION = "events"

ATLAS_URI = "mongodb+srv://9923103056_db_user:3oPkm1uJC0gzANUd@cluster0.imk4fut.mongodb.net/"
ATLAS_DB_NAME = "Minor_Project1"
ATLAS_COLLECTION = "project1"
# ========================

app = FastAPI(title="MongoDB Incremental Sync Service")

scheduler = BackgroundScheduler()


def sync_databases():
    print(f"[{datetime.now()}] 🔄 Starting incremental sync...")

    # Connect to both MongoDB instances
    local_client = MongoClient(LOCAL_URI)
    atlas_client = MongoClient(ATLAS_URI)

    local_db = local_client[LOCAL_DB_NAME]
    atlas_db = atlas_client[ATLAS_DB_NAME]

    local_collection = local_db[LOCAL_COLLECTION]
    atlas_collection = atlas_db[ATLAS_COLLECTION]

    operations = []

    # Iterate through all local docs
    for doc in local_collection.find({}):
        # Upsert: insert if new, update if already exists (based on _id)
        operations.append(
            UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
        )

    # Run in batches to handle large data efficiently
    BATCH_SIZE = 1000
    for i in range(0, len(operations), BATCH_SIZE):
        batch = operations[i:i + BATCH_SIZE]
        atlas_collection.bulk_write(batch, ordered=False)

    print(f"   ✅ {len(operations)} documents synced from '{LOCAL_COLLECTION}' → '{ATLAS_COLLECTION}'")
    print(f"[{datetime.now()}] ✅ Incremental sync completed successfully!")


# === Schedule automatic midnight sync ===
scheduler.add_job(sync_databases, "cron", hour=0, minute=0)
scheduler.start()


@app.post("/sync")
def trigger_sync(background_tasks: BackgroundTasks):
    """Manual trigger endpoint"""
    background_tasks.add_task(sync_databases)
    return {"status": "started", "message": "Incremental sync started in background."}


@app.get("/")
def home():
    return {"status": "running", "message": "MongoDB Incremental Sync API is live."}


if __name__ == "__main__":
    print("🚀 MongoDB Incremental Sync API is running at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
