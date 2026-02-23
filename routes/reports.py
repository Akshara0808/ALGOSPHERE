from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from pymongo import MongoClient
from models.receipt import ReceiptModel
from models.user import UserModel
from services.pdf_service import generate_monthly_report
import io
from datetime import datetime

reports_bp = Blueprint("reports", __name__)


def get_models():
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client["algosphere"]
    return ReceiptModel(db), UserModel(db)


# ---------------------------------------------------------------
# GET /api/reports/monthly?year=2024&month=3
# ---------------------------------------------------------------
@reports_bp.route("/monthly", methods=["GET"])
@jwt_required()
def monthly_report():
    user_id = get_jwt_identity()
    now = datetime.utcnow()

    try:
        year = int(request.args.get("year", now.year))
        month = int(request.args.get("month", now.month))
    except ValueError:
        return jsonify({"error": "Invalid year or month"}), 400

    if not (1 <= month <= 12):
        return jsonify({"error": "Month must be between 1 and 12"}), 400

    receipt_model, user_model = get_models()
    user = user_model.find_by_id(user_id)
    receipts = receipt_model.find_by_month(user_id, year, month)

    if not receipts:
        return jsonify({"error": f"No receipts found for {year}-{month:02d}"}), 404

    try:
        pdf_buffer = generate_monthly_report(
            user=user,
            receipts=receipts,
            year=year,
            month=month,
        )
        month_name = datetime(year, month, 1).strftime("%B_%Y")
        return send_file(
            io.BytesIO(pdf_buffer),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"AlgoSphere_Report_{month_name}.pdf",
        )
    except Exception as e:
        return jsonify({"error": "PDF generation failed", "details": str(e)}), 500


# ---------------------------------------------------------------
# GET /api/reports/available  –  list months that have receipts
# ---------------------------------------------------------------
@reports_bp.route("/available", methods=["GET"])
@jwt_required()
def available_months():
    user_id = get_jwt_identity()
    receipt_model, _ = get_models()
    monthly_data = receipt_model.monthly_totals(user_id)
    return jsonify({
        "months": [{"month": m["_id"], "total": round(m["total"], 2), "count": m["count"]}
                   for m in monthly_data]
    }), 200
