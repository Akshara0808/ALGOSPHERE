import os
from xmlrpc import client
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from models.receipt import ReceiptModel
from services.ocr_service import extract_text
from services.ai_service import parse_receipt_with_ai
from utils.helpers import allowed_file, secure_unique_filename
from models.budget import BudgetModel
from datetime import datetime
from utils.email_service import send_budget_alert
from bson import ObjectId
receipts_bp = Blueprint("receipts", __name__)


def get_receipt_model():
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client["algosphere"]
    return ReceiptModel(db)


# ---------------------------------------------------------------
# POST /api/receipts/upload
# ---------------------------------------------------------------
@receipts_bp.route("/upload", methods=["POST"])
@jwt_required()
def upload_receipt():

    user_id = get_jwt_identity()

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
        return jsonify({"error": "File type not allowed. Use JPG, PNG or PDF"}), 400

    # ---------------------------
    # Save File
    # ---------------------------

    filename = secure_unique_filename(file.filename)
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # ---------------------------
    # OCR
    # ---------------------------

    try:
        raw_text = extract_text(filepath, current_app.config["TESSERACT_CMD"])
    except Exception as e:
        return jsonify({"error": f"OCR failed: {str(e)}"}), 500

    if not raw_text.strip():
        return jsonify({"error": "Could not extract text from image"}), 422

    # ---------------------------
    # AI Parsing
    # ---------------------------

    try:
        parsed = parse_receipt_with_ai(raw_text, current_app.config["OPENAI_API_KEY"])
    except Exception as e:
        return jsonify({"error": f"Parsing failed: {str(e)}"}), 500

    # ---------------------------
    # Normalize Category
    # ---------------------------

    category = parsed.get("category", "other").lower()

    # ---------------------------
    # Determine Month / Year
    # ---------------------------

    try:
        receipt_date = datetime.strptime(parsed.get("date", ""), "%Y-%m-%d")
    except:
        receipt_date = datetime.now()

    month = receipt_date.month
    year = receipt_date.year

    # ---------------------------
    # Save Receipt
    # ---------------------------

    try:

        receipt_model = get_receipt_model()

        receipt = receipt_model.create_receipt(
            user_id=user_id,
            vendor=parsed.get("vendor", "Unknown"),
            receipt_date=receipt_date.strftime("%Y-%m-%d"),
            items=parsed.get("items", []),
            total=float(parsed.get("total", 0)),
            category=category,
            tax=float(parsed.get("tax", 0)),
            raw_text=raw_text,
            image_path=filename
        )

    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500

    # ---------------------------
    # Budget Alert Logic
    # ---------------------------

    client = MongoClient(current_app.config["MONGO_URI"])
    db = client["algosphere"]

    budgets_collection = db["budgets"]

    budget = budgets_collection.find_one({
        "user_id": user_id,
        "category": category,
        "month": month,
        "year": year
    })

    alert = None
    spent = 0

    if budget:

        spent = receipt_model.total_spent_by_category(
            user_id,
            category,
            month,
            year
        )

        budget_amount = float(budget["monthly_budget"])
        user = db.users.find_one({"_id": ObjectId(user_id)})
        user_email = None
        if user and "email" in user:
            user_email = user["email"]
        if spent > budget_amount:
            alert = f"⚠ Budget exceeded for {category} in {month}/{year}. Spent ₹{spent} of ₹{budget_amount}"
            if user_email:
                send_budget_alert(user_email, category, spent, budget_amount)
        elif spent >= budget_amount * 0.8:
            alert = f"⚠ {category} spending reached 80% of budget. ₹{spent} of ₹{budget_amount}"
            if user_email:
                send_budget_alert(user_email, category, spent, budget_amount)
    # ---------------------------
    # Response
    # ---------------------------

    return jsonify({
        "receipt": ReceiptModel.serialize(receipt),
        "alert": alert,
        "spent": spent
    }), 201
    


# ---------------------------------------------------------------
# GET /api/receipts/
# ---------------------------------------------------------------
@receipts_bp.route("/", methods=["GET"])
@jwt_required()
def list_receipts():
    user_id = get_jwt_identity()
    limit = int(request.args.get("limit", 50))
    skip = int(request.args.get("skip", 0))
    receipt_model = get_receipt_model()
    receipts = receipt_model.find_by_user(user_id, limit=limit, skip=skip)
    return jsonify({
        "receipts": [ReceiptModel.serialize(r) for r in receipts],
        "count": len(receipts),
    }), 200


# ---------------------------------------------------------------
# GET /api/receipts/<id>
# ---------------------------------------------------------------
@receipts_bp.route("/<receipt_id>", methods=["GET"])
@jwt_required()
def get_receipt(receipt_id):
    user_id = get_jwt_identity()
    receipt_model = get_receipt_model()
    receipt = receipt_model.find_by_id(receipt_id, user_id)
    if not receipt:
        return jsonify({"error": "Receipt not found"}), 404
    return jsonify({"receipt": ReceiptModel.serialize(receipt)}), 200


# ---------------------------------------------------------------
# DELETE /api/receipts/<id>
# ---------------------------------------------------------------
@receipts_bp.route("/<receipt_id>", methods=["DELETE"])
@jwt_required()
def delete_receipt(receipt_id):
    user_id = get_jwt_identity()
    receipt_model = get_receipt_model()
    deleted = receipt_model.delete_receipt(receipt_id, user_id)
    if not deleted:
        return jsonify({"error": "Receipt not found"}), 404
    return jsonify({"message": "Receipt deleted"}), 200


# ---------------------------------------------------------------
# GET /api/receipts/image/<filename>
# ---------------------------------------------------------------
@receipts_bp.route("/image/<filename>", methods=["GET"])
@jwt_required()
def get_image(filename):
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(os.path.abspath(upload_folder), filename)