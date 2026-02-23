import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from models.receipt import ReceiptModel
from services.ocr_service import extract_text
from services.ai_service import parse_receipt_with_ai
from utils.helpers import allowed_file, secure_unique_filename

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
    if not file or file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
        return jsonify({"error": "File type not allowed. Use JPG, PNG or PDF"}), 400

    # Save the file
    filename = secure_unique_filename(file.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    # OCR
    try:
        raw_text = extract_text(filepath, current_app.config["TESSERACT_CMD"])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"OCR failed: {str(e)}", "hint": "Is Tesseract installed at the path in your .env?"}), 500

    if not raw_text.strip():
        return jsonify({"error": "Could not extract text from image. Please upload a clearer image."}), 422

    # AI parsing (always succeeds – falls back to local parser if OpenAI unavailable)
    try:
        parsed = parse_receipt_with_ai(raw_text, current_app.config["OPENAI_API_KEY"])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Parsing failed: {str(e)}"}), 500

    # Persist to MongoDB
    try:
        receipt_model = get_receipt_model()
        receipt = receipt_model.create_receipt(
            user_id=user_id,
            vendor=parsed.get("vendor", "Unknown"),
            receipt_date=parsed.get("date", ""),
            items=parsed.get("items", []),
            total=float(parsed.get("total", 0)),
            category=parsed.get("category", "General"),
            tax=float(parsed.get("tax", 0)),
            raw_text=raw_text,
            image_path=filename,
        )
        return jsonify({
            "message": "Receipt processed successfully",
            "receipt": ReceiptModel.serialize(receipt),
        }), 201
    except Exception as e:
        return jsonify({"error": "Database error", "details": str(e)}), 500


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
