
import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(override=True)
MONGO_URI = os.getenv("MONGODB_URI")

client = None
collection = None

try:
    if not MONGO_URI:
        raise ValueError("MONGO_URI is missing from your .env file")

    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )

    client.admin.command("ping")

    db = client["gesturebridge"]
    collection = db["gesture_history"]

    print("MongoDB connected successfully!")

except Exception as error:
    print("MongoDB connection failed:", error)


def save_gesture(gesture):
    """Save a recognized gesture to MongoDB."""
    if collection is None:
        return False

    try:
        record = {
            "gesture": gesture,
            "timestamp": datetime.now(timezone.utc),
            "source": "webcam"
        }

        collection.insert_one(record)
        print("Saved gesture:", gesture)
        return True

    except Exception as error:
        print("Could not save gesture:", error)
        return False


def get_gesture_history(limit=50):
    """Return the latest recognized gestures."""
    if collection is None:
        return []

    try:
        records = collection.find(
            {},
            {"_id": 0, "gesture": 1, "timestamp": 1, "source": 1}
        ).sort("timestamp", -1).limit(limit)

        return list(records)

    except Exception as error:
        print("Could not load history:", error)
        return []
