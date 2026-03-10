from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from datetime import datetime
from models.receipt import ReceiptModel

budgets_bp = Blueprint("budgets", __name__)


def get_db():
    client = MongoClient(current_app.config["MONGO_URI"])
    return client["algosphere"]


# ---------------------------------------------
# SET BUDGET
# ---------------------------------------------
@budgets_bp.route("/set", methods=["POST"])
@jwt_required()
def set_budget():

    user_id = get_jwt_identity()
    data = request.json

    category = data.get("category").lower()
    month = int(data.get("month"))
    amount = float(data.get("monthly_budget"))

    now = datetime.now()
    year = now.year

    db = get_db()

    db.budgets.update_one(
        {
            "user_id": user_id,
            "category": category,
            "month": month,
            "year": year
        },
        {
            "$set": {
                "monthly_budget": amount
            }
        },
        upsert=True
    )

    return jsonify({"message": "Budget saved"})
    

# ---------------------------------------------
# BUDGET STATUS
# ---------------------------------------------
@budgets_bp.route("/status", methods=["GET"])
@jwt_required()
def get_budget_status():

    user_id = get_jwt_identity()
    db = get_db()

    receipt_model = ReceiptModel(db)

    cursor = db.budgets.find({"user_id": user_id})

    budgets = []

    for b in cursor:

        spent = receipt_model.total_spent_by_category(
            user_id,
            b["category"],
            b["month"],
            b["year"]
        )

        budgets.append({
            "category": b["category"],
            "month": b["month"],
            "budget": b["monthly_budget"],
            "spent": spent
        })

    return jsonify(budgets)