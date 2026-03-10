from datetime import datetime, timezone
from bson import ObjectId
import bcrypt


class UserModel:
    """Handles all user-related database operations."""

    def __init__(self, db):
        self.collection = db["users"]
        # Unique index on email
        self.collection.create_index("email", unique=True)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    def create_user(self, name: str, email: str, password: str) -> dict:
        """Hash password and insert a new user document. Returns the user dict."""
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        doc = {
            "name": name,
            "email": email.lower().strip(),
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def find_by_email(self, email: str) -> dict | None:
        return self.collection.find_one({"email": email.lower().strip()})

    def find_by_id(self, user_id: str) -> dict | None:
        try:
            return self.collection.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update_password(self, user_id: str, new_password: str) -> bool:
        """Update user's password. Returns True if successful."""
        try:
            password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            result = self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"password_hash": password_hash}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    @staticmethod
    def serialize(user: dict) -> dict:
        return {
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "created_at": user.get("created_at", datetime.now(timezone.utc)).isoformat(),
        }
