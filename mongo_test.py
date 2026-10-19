import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()

uri = os.getenv("MONGODB_URI")

if not uri or uri == "PASTE_YOUR_ATLAS_CONNECTION_STRING_HERE":
    raise ValueError("Please add your Atlas connection string to .env")

client = None

try:
    client = MongoClient(
        uri,
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=10000,
    )

    client.admin.command("ping")
    print("Connected to MongoDB Atlas successfully!")

    db = client["gesturebridge_db"]
    collection = db["gesture_history"]

    result = collection.insert_one({
        "gesture": "Thumbs Up",
        "meaning": "Good job!",
        "confidence": 0.96,
    })

    print("Test record saved:", result.inserted_id)

except Exception as error:
    print("Connection failed:", error)

finally:
    if client:
        client.close()
