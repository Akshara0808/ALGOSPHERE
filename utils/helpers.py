"""
Shared utility helpers used across the application.
"""
import uuid
import os
from werkzeug.utils import secure_filename as _secure_filename


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check whether a filename has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in allowed_extensions


def secure_unique_filename(filename: str) -> str:
    """Return a safe, collision-free filename by prepending a UUID."""
    safe = _secure_filename(filename)
    ext = safe.rsplit(".", 1)[-1] if "." in safe else "bin"
    return f"{uuid.uuid4().hex}.{ext}"


def format_currency(amount: float) -> str:
    """Format a float as an INR currency string."""
    return f"₹{amount:,.2f}"
