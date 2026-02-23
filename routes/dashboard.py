from flask import Blueprint, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from models.receipt import ReceiptModel

dashboard_bp = Blueprint("dashboard", __name__)


def get_receipt_model():
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client["algosphere"]
    return ReceiptModel(db)


# ---------------------------------------------------------------
# GET /api/dashboard/stats
# ---------------------------------------------------------------
@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def stats():
    user_id = get_jwt_identity()
    receipt_model = get_receipt_model()

    total_spent = receipt_model.total_spending(user_id)
    all_receipts = receipt_model.find_by_user(user_id)
    category_breakdown = receipt_model.spending_by_category(user_id)
    monthly_data = receipt_model.monthly_totals(user_id)
    recent = receipt_model.recent_receipts(user_id, limit=5)

    # Top category
    top_category = category_breakdown[0]["_id"] if category_breakdown else "N/A"

    return jsonify({
        "total_spent": round(total_spent, 2),
        "total_receipts": len(all_receipts),
        "top_category": top_category,
        "category_breakdown": [
            {"category": c["_id"] or "General", "total": round(c["total"], 2), "count": c["count"]}
            for c in category_breakdown
        ],
        "monthly_totals": [
            {"month": m["_id"], "total": round(m["total"], 2), "count": m["count"]}
            for m in monthly_data
        ],
        "recent_receipts": [ReceiptModel.serialize(r) for r in recent],
    }), 200
