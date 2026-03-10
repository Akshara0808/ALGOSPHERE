from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from pymongo import MongoClient
from models.user import UserModel
from config import Config

auth_bp = Blueprint("auth", __name__)


def get_user_model():
    client = MongoClient(current_app.config["MONGO_URI"])
    db = client["expenseeye"]
    return UserModel(db)


# ---------------------------------------------------------------
# POST /api/auth/signup
# ---------------------------------------------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    user_model = get_user_model()
    if user_model.find_by_email(email):
        return jsonify({"error": "An account with this email already exists"}), 409

    try:
        user = user_model.create_user(name, email, password)
        access_token = create_access_token(identity=str(user["_id"]))
        return jsonify({
            "message": "Account created successfully",
            "token": access_token,
            "user": UserModel.serialize(user),
        }), 201
    except Exception as e:
        return jsonify({"error": "Registration failed", "details": str(e)}), 500


# ---------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user_model = get_user_model()
    user = user_model.find_by_email(email)
    if not user or not user_model.verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user["_id"]))
    return jsonify({
        "message": "Login successful",
        "token": access_token,
        "user": UserModel.serialize(user),
    }), 200


# ---------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------
@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user_model = get_user_model()
    user = user_model.find_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": UserModel.serialize(user)}), 200


# ---------------------------------------------------------------
# POST /api/auth/change-password
# ---------------------------------------------------------------
@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")

    if not old_password or not new_password:
        return jsonify({"error": "Old and new passwords are required"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    user_model = get_user_model()
    user = user_model.find_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Verify old password
    if not user_model.verify_password(old_password, user["password_hash"]):
        return jsonify({"error": "Current password is incorrect"}), 401

    # Update password
    if user_model.update_password(user_id, new_password):
        return jsonify({"message": "Password changed successfully"}), 200
    else:
        return jsonify({"error": "Failed to update password"}), 500
