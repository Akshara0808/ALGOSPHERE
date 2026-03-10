from flask import Flask, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

# Extensions
CORS(app, supports_credentials=True)
jwt = JWTManager(app)

# MongoDB
client = MongoClient(app.config["MONGO_URI"])
try:
    db = client.get_default_database()
except Exception:
    db = client["expenseeye"]

# Ensure upload folder exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Register blueprints
from routes.auth import auth_bp
from routes.receipts import receipts_bp
from routes.dashboard import dashboard_bp
from routes.reports import reports_bp

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(receipts_bp, url_prefix="/api/receipts")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(reports_bp, url_prefix="/api/reports")


# Frontend routes – serve HTML pages
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/signup")
def signup_page():
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/upload")
def upload_page():
    return render_template("upload.html")

@app.route("/receipts")
def receipts_page():
    return render_template("receipts.html")


# JWT error handlers
@jwt.unauthorized_loader
def unauthorized_response(callback):
    return {"error": "Missing or invalid token"}, 401

@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_payload):
    return {"error": "Token has expired"}, 401

@jwt.invalid_token_loader
def invalid_token_response(callback):
    return {"error": "Invalid token"}, 401


if __name__ == "__main__":
    app.run(debug=app.config["FLASK_ENV"] == "development", host="0.0.0.0", port=5000)
