import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/expenseeye")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)   # tokens last 7 days
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
