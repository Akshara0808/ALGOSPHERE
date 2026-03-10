from calendar import month
from datetime import datetime, timezone
from unittest import result
from bson import ObjectId
from typing import List

class ReceiptModel:
    """Handles all receipt-related database operations."""

    def __init__(self, db):
        self.collection = db["receipts"]
        self.collection.create_index("user_id")
        self.collection.create_index([("user_id", 1), ("receipt_date", -1)])

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------
    def create_receipt(
        self,
        user_id: str,
        vendor: str,
        receipt_date: str,
        items: List[dict],
        total: float,
        category: str,
        tax: float,
        raw_text: str,
        image_path: str,
    ) -> dict:
        doc = {
            "user_id": user_id,
            "vendor": vendor,
            "receipt_date": receipt_date,
            "items": items,           # [{"name": str, "qty": float, "price": float}]
            "total": total,
            "category": category,
            "tax": tax,
            "raw_text": raw_text,
            "image_path": image_path,
            "created_at": datetime.now(timezone.utc),
        }
        result = self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------
    def find_by_user(self, user_id: str, limit: int = 100, skip: int = 0) -> List[dict]:
        return list(
            self.collection.find({"user_id": user_id})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )

    def find_by_id(self, receipt_id: str, user_id: str) -> dict | None:
        try:
            return self.collection.find_one({"_id": ObjectId(receipt_id), "user_id": user_id})
        except Exception:
            return None

    def find_by_month(self, user_id: str, year: int, month: int) -> List[dict]:
        start = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end = f"{year + 1:04d}-01-01"
        else:
            end = f"{year:04d}-{month + 1:02d}-01"
        return list(
            self.collection.find(
                {"user_id": user_id, "receipt_date": {"$gte": start, "$lt": end}}
            ).sort("receipt_date", 1)
        )

    # ------------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------------
    def delete_receipt(self, receipt_id: str, user_id: str) -> bool:
        result = self.collection.delete_one({"_id": ObjectId(receipt_id), "user_id": user_id})
        return result.deleted_count > 0

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------
    def spending_by_category(self, user_id: str) -> List[dict]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": "$category", "total": {"$sum": "$total"}, "count": {"$sum": 1}}},
            {"$sort": {"total": -1}},
        ]
        return list(self.collection.aggregate(pipeline))

    def monthly_totals(self, user_id: str) -> List[dict]:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": {"$substr": ["$receipt_date", 0, 7]},  # "YYYY-MM"
                    "total": {"$sum": "$total"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        return list(self.collection.aggregate(pipeline))

    def recent_receipts(self, user_id: str, limit: int = 5) -> List[dict]:
        return list(
            self.collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        )
    

    def total_spent_by_category(self, user_id: str, category: str, month: int, year: int) -> float:
        start = f"{year:04d}-{month:02d}-01"

        if month == 12:
            end = f"{year + 1:04d}-01-01"
        else:
            end = f"{year:04d}-{month + 1:02d}-01"

        pipeline = [
            {
                "$match": {
                "user_id": user_id,
                "category": category,
                "receipt_date": {"$gte": start, "$lt": end}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$total"}
            }
        }
    ]

        result = list(self.collection.aggregate(pipeline))

        return result[0]["total"] if result else 0.0
    

    def total_spending(self, user_id: str) -> float:
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {"_id": None, "total": {"$sum": "$total"}}},
        ]
        result = list(self.collection.aggregate(pipeline))
        return result[0]["total"] if result else 0.0

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------
    @staticmethod
    def serialize(receipt: dict) -> dict:
        return {
            "id": str(receipt["_id"]),
            "user_id": receipt.get("user_id", ""),
            "vendor": receipt.get("vendor", "Unknown"),
            "receipt_date": receipt.get("receipt_date", ""),
            "items": receipt.get("items", []),
            "total": receipt.get("total", 0.0),
            "category": receipt.get("category", "General"),
            "tax": receipt.get("tax", 0.0),
            "raw_text": receipt.get("raw_text", ""),
            "image_path": receipt.get("image_path", ""),
            "created_at": receipt.get("created_at", datetime.now(timezone.utc)).isoformat(),
        }
