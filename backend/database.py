"""
database.py – MongoDB connection and user collection helpers.
Falls back gracefully if MongoDB is unavailable (uses in-memory store).
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above backend/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MongoDB connection
# ---------------------------------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "edu2job")

# Log which host we're connecting to (mask credentials)
_display_uri = MONGO_URI.split("@")[-1] if "@" in MONGO_URI else MONGO_URI
logger.info(f"Connecting to MongoDB: ...@{_display_uri}")

try:
    from pymongo import MongoClient
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Force a connection check
    client.server_info()
    db = client[DB_NAME]
    users_collection = db["users"]
    # Ensure unique email index
    users_collection.create_index("email", unique=True)
    USING_MONGO = True
    logger.info(f"Connected to MongoDB successfully. Database: {DB_NAME}")
except Exception as e:
    logger.warning(f"MongoDB unavailable ({e}). Using in-memory fallback store.")
    USING_MONGO = False
    _memory_store: list[dict] = []


# ---------------------------------------------------------------------------
# CRUD helpers (abstract away Mongo vs in-memory)
# ---------------------------------------------------------------------------

def find_user_by_email(email: str) -> dict | None:
    email = email.strip().lower()          # normalise for consistent lookup
    if USING_MONGO:
        user = users_collection.find_one({"email": email})
        if user:
            user["id"] = str(user.pop("_id"))
            # Ensure password_hash is a string (bcrypt needs consistent types)
            if "password_hash" in user and isinstance(user["password_hash"], bytes):
                user["password_hash"] = user["password_hash"].decode("utf-8")
        return user
    else:
        for u in _memory_store:
            if u["email"] == email:
                return u
        return None


def insert_user(user_data: dict) -> str:
    if USING_MONGO:
        result = users_collection.insert_one(user_data)
        return str(result.inserted_id)
    else:
        import uuid
        user_data["id"] = str(uuid.uuid4())
        _memory_store.append(user_data)
        return user_data["id"]


def update_user(email: str, update_fields: dict) -> bool:
    if USING_MONGO:
        result = users_collection.update_one(
            {"email": email}, {"$set": update_fields}
        )
        return result.matched_count > 0
    else:
        for u in _memory_store:
            if u["email"] == email:
                u.update(update_fields)
                return True
        return False


def add_prediction(email: str, prediction: dict) -> bool:
    """Append a prediction to the user's predictions array in MongoDB."""
    email = email.strip().lower()
    if USING_MONGO:
        result = users_collection.update_one(
            {"email": email},
            {"$push": {"predictions": prediction}}
        )
        return result.matched_count > 0
    else:
        for u in _memory_store:
            if u["email"] == email:
                u.setdefault("predictions", []).append(prediction)
                return True
        return False


def get_predictions(email: str) -> list:
    """Fetch all stored predictions for a user."""
    email = email.strip().lower()
    if USING_MONGO:
        user = users_collection.find_one({"email": email}, {"predictions": 1})
        return user.get("predictions", []) if user else []
    else:
        for u in _memory_store:
            if u["email"] == email:
                return u.get("predictions", [])
        return []

