from fastapi import FastAPI, BackgroundTasks
from pymongo import MongoClient, UpdateOne
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import uvicorn

# ==== CONFIGURATION ====
LOCAL_URI = "mongodb://localhost:27017"
ATLAS_URI = "mongodb+srv://pragyajoney2005_db_user:C5C1xVNHlgKnwXb2@cluster0.imk4fut.mongodb.net/Minor_Project1"
DB_NAME = "Minor_Project1"
# ========================

app = FastAPI(title="MongoDB Incremental Sync Service")

scheduler = BackgroundScheduler()


def sync_databases():
    print(f"[{datetime.now()}] 🔄 Starting incremental sync...")

    local_client = MongoClient(LOCAL_URI)
    atlas_client = MongoClient(ATLAS_URI)

    local_db = local_client[DB_NAME]
    atlas_db = atlas_client[DB_NAME]

    for collection_name in local_db.list_collection_names():
        print(f" → Checking collection: {collection_name}")
        local_collection = local_db[collection_name]
        atlas_collection = atlas_db[collection_name]

        operations = []

        # Iterate through all local docs
        for doc in local_collection.find({}):
            # Prepare upsert operation (update if exists, insert if not)
            operations.append(
                UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            )

        # Run bulk upserts in batches to avoid memory overload
        BATCH_SIZE = 1000
        for i in range(0, len(operations), BATCH_SIZE):
            batch = operations[i:i + BATCH_SIZE]
            atlas_collection.bulk_write(batch, ordered=False)

        print(f"   ✅ {len(operations)} documents synced in '{collection_name}'")

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
