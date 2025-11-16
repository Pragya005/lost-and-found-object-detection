from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId

app = Flask(__name__)
CORS(app)

mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["fog_ai_detection"]
collection = db["events"]

# ---------------------------
# GET detections (dashboard)
# ---------------------------
@app.get("/api/detections")
def get_detections():
    data = list(collection.find().sort("_id", -1).limit(20))
    
    for d in data:
        d["_id"] = str(d["_id"])
        if "saved_at" in d:
            d["saved_at"] = str(d["saved_at"])
        if "collected" not in d:
            d["collected"] = False  # ensure key exists

    return jsonify(data)

# ---------------------------
# UPDATE collected status
# ---------------------------
@app.route("/api/update_collected/<id>", methods=["POST"])
def update_collected(id):
    try:
        data = request.get_json()
        collected = data.get("collected", False)

        collection.update_one(
            {"_id": ObjectId(id)},
            {"$set": {"collected": collected}}
        )

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------
# START SERVER
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)